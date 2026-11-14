"""Write SIGNALS_REGISTER.md from data/signals_register.json. Run with --check to verify that the page matches the data."""
import json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def render(reg):
    cell = lambda s: str(s or "").replace("|", "/").replace("\n", " ")
    rows, status = reg["register"], reg["statuses"]
    md = ["# Register of the signals already examined", "",
          "Every detection signal, pattern or hypothesis examined in this repository up to 14 November 2026, before the study of this note.",
          "It exists so that nothing validated is redone and nothing refuted is relaunched with other parameters.", "",
          "Compiled from the files cited in each row. Rows marked *recomputed* were recomputed from the published tables by two",
          "independent readers; the others were copied from the cited lines and were not recomputed. Machine-readable copy:",
          "[data/signals_register.json](data/signals_register.json).", "", "| Status | Rows |", "|---|---:|"]
    count = {}
    for r in rows:
        count[r["status"]] = count.get(r["status"], 0) + 1
    md += [f"| {status[s]} | {count.get(s, 0)} |" for s in status]
    md += ["", "**No signal is demonstrated as a sign of private information.** The two demonstrated rows concern prices only: a rise tends to continue",
           "for a short time, and some wallets lead small moves by a minute or two, which cannot be copied at a profit.", ""]
    fam = {}
    for r in rows:
        fam.setdefault(r["family"], []).append(r)
    for f in sorted(fam):
        md += [f"## {f[2:].strip().capitalize() if f[1] == ' ' else f}", "", "| Id | Signal | Tested on | Result | Status | Check | Source |", "|---|---|---|---|---|---|---|"]
        for r in fam[f]:
            src = "; ".join(r["sources"][:3]) or "local file, not published"
            md.append(f"| {r['id']} | {cell(r['signal'])} | {cell(r['data'])} | {cell(r['result'])}{(' Caveat: ' + cell(r['caveat'])) if r.get('caveat') else ''} | "
                      f"{r['status']} | {r['check']} | {cell(src)} |")
        md.append("")
    md += ["## Results that later work corrected or contradicted", "", "| Id | Topic | First version | Later version | Note |", "|---|---|---|---|---|"]
    md += [f"| {c['id']} | {cell(c.get('topic'))} | {cell(c.get('version_1'))} | {cell(c.get('version_2'))} | {cell(c.get('note'))} |" for c in reg["corrected_or_contradicted"]]
    md += ["", "## Experiments that must not be rerun with other parameters", "", "| Id | Experiment | Why |", "|---|---|---|"]
    md += [f"| {d['id']} | {cell(d.get('experiment'))} | {cell(d.get('why'))} |" for d in reg["do_not_rerun"]]
    md += ["", "## Questions that no test answered before this note", "", "| Id | Question |", "|---|---|"]
    md += [f"| {q['id']} | {cell(q.get('question'))} |" for q in reg["open_questions"]]
    return "\n".join(md) + "\n"


def main():
    with open(os.path.join(HERE, "data", "signals_register.json")) as f:
        text = render(json.load(f))
    path = os.path.join(HERE, "SIGNALS_REGISTER.md")
    if "--check" in sys.argv:
        with open(path) as f:
            same = f.read() == text
        print("SIGNALS_REGISTER.md matches the data" if same else "SIGNALS_REGISTER.md differs from data/signals_register.json")
        return 0 if same else 1
    with open(path, "w") as f:
        f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
