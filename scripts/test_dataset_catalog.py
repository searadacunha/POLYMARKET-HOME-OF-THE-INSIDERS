#!/usr/bin/env python3
"""The dataset catalogue on a git repository made by the test: what is listed, how it is read, when it is stale."""
import contextlib
import gzip
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_dataset_catalog as catalog  # noqa: E402

CSV = 'a,b\n1,"two\nlines"\n3,4\n'
FILES = {
    "top.csv": CSV,
    "investigations/case-1/README.md": "# Case one\n\ntext\n",
    "investigations/case-1/results/t.tsv": "x\ty\n1\t2\n",
    "research_notes/note-2/REPORT.md": "Intro\n## Report two\n",
    "research_notes/note-2/data/rows.jsonl": '{"k": 1, "v": "a"}\n\n{"k": 2}\n',
    "research_notes/note-2/data/arrays.jsonl": "[1, 2]\n[3, 4]\n",
    "research_notes/note-2/data/empty.csv": "",
    "edge_research/data/p.parquet": "PAR1",
    "edge_research/notes.md": "not a table\n",
}


def run(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def quiet(argv, root):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        code = catalog.main(argv, root=root)
    return code, out.getvalue()


class Catalogue(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for path, text in FILES.items():
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text(text, encoding="utf-8")
        with gzip.open(self.root / "investigations/case-1/results/g.csv.gz", "wt", encoding="utf-8") as handle:
            handle.write("﻿h1,h2\n5,6\n")
        (self.root / "untracked.csv").write_text("u\n1\n", encoding="utf-8")
        run(self.root, "init", "-q")
        run(self.root, "add", *FILES, "investigations/case-1/results/g.csv.gz")

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_tracked_table_and_only_those(self):
        self.assertEqual([e["path"] for e in catalog.build(self.root)], [
            "edge_research/data/p.parquet", "investigations/case-1/results/g.csv.gz", "investigations/case-1/results/t.tsv",
            "research_notes/note-2/data/arrays.jsonl", "research_notes/note-2/data/empty.csv", "research_notes/note-2/data/rows.jsonl", "top.csv"])

    def test_entries_are_exact(self):
        by_path = {e["path"]: e for e in catalog.build(self.root)}
        self.assertEqual(by_path["top.csv"], {"path": "top.csv", "format": "csv", "bytes": len(CSV.encode()),
                                              "sha256": hashlib.sha256(CSV.encode()).hexdigest(), "columns": ["a", "b"], "rows": 2,
                                              "owner": ".", "owner_title": None, "note": None})
        shapes = {p: (e["format"], e["columns"], e["rows"], e["owner"], e["owner_title"], e["note"]) for p, e in by_path.items()}
        self.assertEqual(shapes, {
            "edge_research/data/p.parquet": ("parquet", None, None, "edge_research", None, catalog.PARQUET_NOTE),
            "investigations/case-1/results/g.csv.gz": ("csv.gz", ["h1", "h2"], 1, "investigations/case-1", "Case one", None),
            "investigations/case-1/results/t.tsv": ("tsv", ["x", "y"], 1, "investigations/case-1", "Case one", None),
            "research_notes/note-2/data/arrays.jsonl": ("jsonl", None, 2, "research_notes/note-2", "Report two", catalog.ARRAY_NOTE),
            "research_notes/note-2/data/empty.csv": ("csv", [], 0, "research_notes/note-2", "Report two", None),
            "research_notes/note-2/data/rows.jsonl": ("jsonl", ["k", "v"], 2, "research_notes/note-2", "Report two", None),
            "top.csv": ("csv", ["a", "b"], 2, ".", None, None)})

    def test_the_file_is_deterministic_json_with_a_trailing_newline(self):
        self.assertEqual(quiet([], self.root), (0, "7 tables catalogued\n"))
        first = (self.root / catalog.CATALOG).read_bytes()
        quiet([], self.root)
        self.assertEqual((self.root / catalog.CATALOG).read_bytes(), first)
        self.assertTrue(first.endswith(b"]}\n"))
        self.assertEqual(json.loads(first)["entries"], catalog.build(self.root))

    def test_check_passes_on_a_fresh_catalogue_and_fails_when_a_table_changes_or_appears(self):
        self.assertEqual(quiet(["--check"], self.root), (1, f"stale: {catalog.CATALOG} is missing\n"))
        quiet([], self.root)
        self.assertEqual(quiet(["--check"], self.root), (0, "catalogue up to date\n"))
        (self.root / "top.csv").write_text(CSV.replace("3,4", "3,5"), encoding="utf-8")
        self.assertEqual(quiet(["--check"], self.root), (1, "stale: top.csv\n"))
        (self.root / "new.jsonl").write_text("{}\n", encoding="utf-8")
        run(self.root, "add", "new.jsonl")
        self.assertEqual(quiet(["--check"], self.root), (1, "stale: new.jsonl, top.csv\n"))

    def test_check_counts_what_it_does_not_print(self):
        quiet([], self.root)
        for i in range(25):
            (self.root / f"n{i:02d}.csv").write_text("a\n", encoding="utf-8")
        run(self.root, "add", *(f"n{i:02d}.csv" for i in range(25)))
        code, out = quiet(["--check"], self.root)
        self.assertEqual((code, out.count(", ") + 1, out.rstrip().endswith("and 5 more")), (1, 20, True))

    def test_owner_of_a_path(self):
        paths = ("a.csv", "investigations/x/a.csv", "investigations/a.csv", "research_notes/n/d/a.csv", "edge_research/d/a.csv")
        self.assertEqual([catalog.owner(p) for p in paths], [".", "investigations/x", "investigations", "research_notes/n", "edge_research"])


@unittest.skipUnless((catalog.ROOT / catalog.CATALOG).exists(), "datasets/catalog.json not generated")
class RealCatalogue(unittest.TestCase):
    def test_the_catalogue_of_this_checkout_is_up_to_date(self):
        self.assertEqual(quiet(["--check"], catalog.ROOT), (0, "catalogue up to date\n"))


if __name__ == "__main__":
    unittest.main()
