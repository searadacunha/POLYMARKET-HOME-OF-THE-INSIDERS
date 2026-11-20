#!/usr/bin/env python3
"""Offline checks of the mechanisms synthesis, and the renderer of its tables.

    python3 -I verify.py           named checks, "N/M checks pass", exit 1 on any failure; no network
    python3 -I verify.py --write   re-render the tables of REPORT.md from data/instances.csv, then check

Every row of data/instances.csv cites one report of this repository and the exact sentences that support it. The
check reads those reports in the working tree: a figure, an address or a level that is not written in its source fails.
"""
import csv
import re
import sys
from pathlib import Path

NOTE = Path(__file__).resolve().parent
ROOT = NOTE.parents[1]
MECHANISMS = "ABCDEFG"
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
            out.append(f"| {r['id']} | {r['case']} | {r['population']} | {r['what_the_source_records']} | {r['level_in_source']} | "
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


def shared_rows(report):
    """The table of addresses named by several folders: [(address, [folders])]."""
    sec = report.split("## Addresses named by the reports of two or more folders", 1)[-1].split("\n## ", 1)[0]
    return [(m.group(1).lower(), re.findall(r"`((?:investigations|research_notes)/[^`]+)`", m.group(2)))
            for m in re.finditer(r"^\| `(0x[0-9a-fA-F]{40})` \| (.*)$", sec, re.M)]


def folders_naming(address, root=ROOT):
    """Folders of investigations/ and research_notes/ whose Markdown, outside sources/ copies, names the address."""
    out = set()
    for top in ("investigations", "research_notes"):
        for p in (root / top).glob("*/**/*.md"):
            rel = p.relative_to(root)
            if "sources" in rel.parts or rel.parts[1] == NOTE.name:
                continue
            if address in p.read_text(encoding="utf-8", errors="replace").lower():
                out.add("/".join(rel.parts[:2]))
    return out


def main(argv):
    rows = instances()
    if "--write" in argv:
        write(rows)
    report = (NOTE / "REPORT.md").read_text(encoding="utf-8")
    ids = [r["id"] for r in rows]
    check("A1 26 instances, unique ids, each in one of the seven mechanisms, with at least one quote",
          len(rows) == 26 and len(set(ids)) == 26 and all(r["mechanism"] in MECHANISMS and r["id"].startswith(r["mechanism"]) and r["quotes"] for r in rows),
          f"{len(rows)} rows")
    bad = unsupported(rows)
    check("A2 every quote of every instance is written word for word in its cited report", not bad, "; ".join(f"{i}: {q[:40]}" for i, q in bad[:3]))
    got = blocks(report)
    check("A3 the seven tables of REPORT.md are the rendering of data/instances.csv", sorted(got) == list(MECHANISMS) and all(got[m] == table(rows, m) for m in MECHANISMS))
    counts = {m: sum(r["mechanism"] == m for r in rows) for m in MECHANISMS}
    stated = dict(re.findall(r"^\d\. \*\*([A-G])\. .*?\*\* \((\d+) cases?", report, re.M))
    check("A4 the number of cases given for each mechanism in the Result is the number of its rows", {m: int(n) for m, n in stated.items()} == counts, str(counts))
    cases = {r["case"].split(" (")[0] for r in rows}
    check("A5 the Result counts 13 distinct cases", len(cases) == 13 and "13 cases" in report.split("## Result", 1)[1].split("\n## ", 1)[0], str(len(cases)))
    shared = shared_rows(report)
    missing = [(a, f) for a, fs in shared for f in fs if f not in folders_naming(a)]
    check("B1 each address of the shared-address table is named in the reports of every folder listed for it, outside sources/ copies",
          len(shared) == 7 and all(len(fs) >= 2 for _, fs in shared) and not missing, f"{len(shared)} addresses; missing {missing[:2]}")
    text = "".join(p.read_text(encoding="utf-8") for p in NOTE.rglob("*") if p.is_file() and p.suffix in (".md", ".py", ".csv"))
    homes = ("/" + "Users" + "/", "/" + "home" + "/", "~" + "/")
    check("C1 no em dash, home path or e-mail address in the note", chr(0x2014) not in text and not any(h in text for h in homes)
          and not re.search(r"[\w.+-]+" + "@" + r"[\w-]+\.[a-z]{2,}", text))
    forged = [dict(r) for r in rows]
    forged[0]["quotes"] = forged[0]["quotes"] + " || 999,999.99 USDC"
    check("E1 a quote that is not in its source makes the check fail", unsupported(forged) == [(forged[0]["id"], "999,999.99 USDC")])
    check("E2 a folder that does not name an address is detected", "research_notes/relay-followup-2026-11-04" not in folders_naming("0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a"))
    sample = "<!-- table:A -->\n<!-- /table -->\n\nkept text\n\n<!-- table:B -->\n<!-- /table -->\n"
    filled = fill(sample, rows)
    check("E3 rendering fills two empty tables and keeps the text between them", "\n\nkept text\n\n" in filled
          and blocks(filled) == {"A": table(rows, "A"), "B": table(rows, "B")} and fill(filled, rows) == filled)
    print(f"{sum(RESULTS)}/{len(RESULTS)} checks pass")
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
