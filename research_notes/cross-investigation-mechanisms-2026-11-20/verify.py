#!/usr/bin/env python3
"""Offline checks of the mechanisms synthesis, and the renderer of its tables.

    python3 -I verify.py           named checks, "N/M checks pass", exit 1 on any failure; no network
    python3 -I verify.py --write   re-render the tables of REPORT.md from data/instances.csv, then check

Every row of data/instances.csv cites one report of this repository and the exact sentences that support it. The
check reads those reports in the working tree: a figure, an address or a level that is not written in its source fails.
The address index is recounted from the Git objects of the commit the note was written on (a full clone is needed).
"""
import csv
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

NOTE = Path(__file__).resolve().parent
ROOT = NOTE.parents[1]
COMMIT = "0b0882c1ec1295357b4063e19c4ec8f46b52c0f4"
MECHANISMS = "ABCDEFG"
ADDRESS = re.compile(r"(?<![0-9a-fA-Fx])0x[0-9a-fA-F]{40}(?![0-9a-fA-F])")  # not the first 40 digits of a transaction hash
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f"  [{detail}]" if detail else ""))


def instances():
    with open(NOTE / "data" / "instances.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def table(rows, mechanism):
    out = ["| # | Case | Population | What the source records | Level in the source | Source |", "|---|---|---|---|---|---|"]
    for r in rows:
        if r["mechanism"] == mechanism:
            parts = r["source"].split("/")
            name = "/".join(parts[-2:]) if len(parts) > 1 else parts[0]
            case = r["case"] + (", contrast not counted" if r["contrast"] == "1" else "")
            out.append(f"| {r['id']} | {case} | {r['population']} | {r['what_the_source_records']} | {r['level_in_source']} | "
                       f"[{name}](../../{r['source']}) |")
    return "\n".join(out)


BLOCK = r"(<!-- table:{} -->\n)((?:\|.*\n)*)(<!-- /table -->)"  # a block holds table lines only, so it never runs past its end


def blocks(report):
    found = {m: re.search(BLOCK.format(m), report) for m in MECHANISMS}
    return {m: x.group(2).strip() for m, x in found.items() if x}


def fill(report, rows):
    for m in MECHANISMS:
        report = re.sub(BLOCK.format(m), lambda x: x.group(1) + table(rows, m) + "\n" + x.group(3), report)
    return report


def write(rows):
    (NOTE / "REPORT.md").write_text(fill((NOTE / "REPORT.md").read_text(encoding="utf-8"), rows), encoding="utf-8")


def unsupported(rows, root=ROOT):
    """(id, quote) pairs whose quote is not written in the cited report."""
    bad = []
    for r in rows:
        path = root / r["source"]
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        bad += [(r["id"], q) for q in r["quotes"].split(" || ") if not q or q not in text]
    return bad


def case_name(row):
    return row["case"].split(" (")[0]


def section(report, title):
    return report.split(title, 1)[-1].split("\n## ", 1)[0]


def shared_rows(report):
    """The table of addresses named by several folders: [(address, [folders])]."""
    sec = section(report, "## Addresses named by the reports of two or more folders")
    return [(m.group(1).lower(), re.findall(r"`((?:investigations|research_notes)/[^`]+)`", m.group(2)))
            for m in re.finditer(r"^\| `(0x[0-9a-fA-F]{40})` \| (.*)$", sec, re.M)]


def folders_naming(address, root=ROOT):
    """Folders of investigations/ and research_notes/ whose Markdown, outside sources/ copies, writes the address."""
    out = set()
    for top in ("investigations", "research_notes"):
        for p in (root / top).glob("*/**/*.md"):
            rel = p.relative_to(root)
            if "sources" in rel.parts or rel.parts[1] == NOTE.name:
                continue
            if address in {a.lower() for a in ADDRESS.findall(p.read_text(encoding="utf-8", errors="replace"))}:
                out.add("/".join(rel.parts[:2]))
    return out


def address_index(commit=COMMIT, root=ROOT):
    """(Markdown files, {address: folders}) over investigations/ and research_notes/ at the commit, outside sources/."""
    names = subprocess.run(["git", "-C", str(root), "ls-tree", "-r", "--name-only", commit, "--", "investigations", "research_notes"],
                           capture_output=True, text=True, check=True).stdout.splitlines()
    files = [f for f in names if f.endswith(".md") and len(f.split("/")) > 2 and "sources" not in f.split("/")[:-1]]
    folders = defaultdict(set)
    for f in files:
        text = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{f}"], capture_output=True, text=True, check=True).stdout
        for a in ADDRESS.findall(text):
            folders[a.lower()].add("/".join(f.split("/")[:2]))
    return files, folders


def main(argv):
    rows = instances()
    if "--write" in argv:
        write(rows)
    report = (NOTE / "REPORT.md").read_text(encoding="utf-8")
    result = section(report, "## Result")
    ids = [r["id"] for r in rows]
    check("A1 27 rows, unique ids, each in one of the seven mechanisms, with at least one quote; only C4 is a contrast",
          len(rows) == 27 and len(set(ids)) == 27 and all(r["mechanism"] in MECHANISMS and r["id"].startswith(r["mechanism"]) and r["quotes"] for r in rows)
          and [r["id"] for r in rows if r["contrast"] == "1"] == ["C4"] and {r["contrast"] for r in rows} == {"0", "1"}, f"{len(rows)} rows")
    bad = unsupported(rows)
    check("A2 every quote of every row is written word for word in its cited report", not bad, "; ".join(f"{i}: {q[:40]}" for i, q in bad[:3]))
    got = blocks(report)
    check("A3 the seven tables of REPORT.md are the rendering of data/instances.csv", sorted(got) == list(MECHANISMS) and all(got[m] == table(rows, m) for m in MECHANISMS))
    counted = [r for r in rows if r["contrast"] == "0"]
    counts = {m: sum(r["mechanism"] == m for r in counted) for m in MECHANISMS}
    stated = dict(re.findall(r"^\d\. \*\*([A-G])\. .*?\*\* \((\d+) cases?", result, re.M))
    check("A4 the number of cases given for each mechanism in the Result is its number of rows, the contrast left out", {m: int(n) for m, n in stated.items()} == counts, str(counts))
    cases = {case_name(r) for r in counted}
    check("A5 the Result counts 13 distinct cases", len(cases) == 13 and "13 cases" in result, str(len(cases)))
    mechanisms_of = defaultdict(set)
    for r in counted:
        mechanisms_of[case_name(r)].add(r["mechanism"])
    combined = {name: set(letters.split(", ")) for name, letters in re.findall(r"([A-Z][\w'./ -]*?) \(([A-G](?:, [A-G])+)\)", result)}
    check("A6 every case the Result names with its mechanisms has exactly those mechanisms in the rows, and every case with two or more is named",
          combined == {k: v for k, v in mechanisms_of.items() if len(v) >= 2}, str(sorted((k, "".join(sorted(v))) for k, v in combined.items())))
    files, index = address_index()
    multi = {a for a, fs in index.items() if len(fs) >= 2}
    sec = section(report, "## Addresses named by the reports of two or more folders")
    check("B1 the address index recounts 188 reports, 200 distinct full addresses and 54 named by two or more folders, as the text says",
          (len(files), len(index), len(multi)) == (188, 200, 54) and "Of the 200 distinct full addresses" in sec and "54 appear in two folders or more" in sec
          and "54 addresses" in result, str((len(files), len(index), len(multi))))
    shared = shared_rows(report)
    missing = [(a, f) for a, fs in shared for f in fs if f not in folders_naming(a)]
    check("B2 each of the 8 addresses of the table is among the 54 and is written by every folder listed for it, outside sources/ copies",
          len(shared) == 8 and all(len(fs) >= 2 and a in multi and set(fs) <= index[a] for a, fs in shared) and not missing, f"missing {missing[:2]}")
    both = [a for a, fs in shared if {"research_notes/inca-crosscheck-2026-11-06", "research_notes/iran-cluster-e-network-2026-11-05"} <= set(fs)]
    check("B3 five rows of the table are named by both the Inca cross-check and the cluster E note, as the Result says", len(both) == 5 and "five of them are named by both" in result, str(len(both)))
    text = "".join(p.read_text(encoding="utf-8") for p in NOTE.rglob("*") if p.is_file() and p.suffix in (".md", ".py", ".csv"))
    homes = ("/" + "Users" + "/", "/" + "home" + "/", "~" + "/")
    check("C1 no em dash, home path or e-mail address in the note", chr(0x2014) not in text and not any(h in text for h in homes)
          and not re.search(r"[\w.+-]+" + "@" + r"[\w-]+\.[a-z]{2,}", text))
    forged = [dict(r) for r in rows]
    forged[0]["quotes"] = forged[0]["quotes"] + " || 999,999.99 USDC"
    check("E1 a quote that is not in its source makes the check fail", unsupported(forged) == [(forged[0]["id"], "999,999.99 USDC")])
    check("E2 a folder that does not write an address, or only a transaction hash that starts like it, is not counted",
          "research_notes/relay-followup-2026-11-04" not in folders_naming("0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a")
          and ADDRESS.findall("tx 0x" + "ab" * 32 + " and 0x" + "cd" * 20 + ".") == ["0x" + "cd" * 20])
    sample = "<!-- table:A -->\n<!-- /table -->\n\nkept text\n\n<!-- table:B -->\n<!-- /table -->\n"
    filled = fill(sample, rows)
    check("E3 rendering fills two empty tables and keeps the text between them", "\n\nkept text\n\n" in filled
          and blocks(filled) == {"A": table(rows, "A"), "B": table(rows, "B")} and fill(filled, rows) == filled)
    print(f"{sum(RESULTS)}/{len(RESULTS)} checks pass")
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
