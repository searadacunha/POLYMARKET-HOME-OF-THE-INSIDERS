"""Renders and checks the repository table of REPORT.md from scout.json, and checks the positions table.

    python3 -I research_notes/competitor-benchmark-extension-2026-11-20/verify.py           # check (CI)
    python3 -I research_notes/competitor-benchmark-extension-2026-11-20/verify.py --write   # re-render the table

Offline. The scout's file records what was read on 20 November 2026 through the public GitHub API; no competitor code
was executed. When the Nobel replay note is in the tree, the figures this note copies from it are checked against it."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
START, END = "<!-- table:repos -->", "<!-- /table:repos -->"
PERMISSIVE = ("MIT", "Apache-2.0")
ok, bad = [], []


def check(name, cond):
    (ok if cond else bad).append(name)


def cell(s, n=220):
    s = re.sub(r"\s+", " ", str(s or "")).replace("|", "/").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def licence_word(text):
    t = text or ""
    if t.lower().startswith(("none", "unclear")):
        return "none (all rights reserved)" if t.lower().startswith("none") else "unclear, treated as all rights reserved"
    for k in ("Apache-2.0", "MIT"):
        if k in t:
            return k + (" (code)" if "CC BY" in t else "")
    return cell(t, 40)


def table(scout):
    rows = ["| Repository | Licence | Last push | Category | What its code or README shows | Point-in-time risk | Tests |", "|---|---|---|---|---|---|---|"]
    for r in sorted(scout["repos"], key=lambda r: r["name"].lower()):
        rows.append(f"| [{cell(r['name'], 80)}]({r['url']}) | {licence_word(r['license'])} | {cell(r.get('last_push'), 12)} | {cell(r['category'], 60)} | "
                    f"{cell(r['method'])} | {cell(r.get('point_in_time_risks'), 160)} | {cell(r.get('tests'), 90)} |")
    return "\n".join(rows)


def main(write=False):
    with open(os.path.join(HERE, "scout.json")) as f:
        scout = json.load(f)
    path = os.path.join(HERE, "REPORT.md")
    with open(path) as f:
        rep = f.read()
    a, b = rep.index(START) + len(START), rep.index(END)
    want = "\n" + table(scout) + "\n"
    if write:
        with open(path, "w") as f:
            f.write(rep[:a] + want + rep[b:])
        print("table written"); return 0
    check("repository table is the rendering of scout.json", rep[a:b] == want)
    names = [r["name"] for r in scout["repos"]]
    check("24 repositories, no duplicate", len(names) == 24 == len(set(names)))
    check("none of them is in the published eight", not set(n.split(" ")[0] for n in names) & {
        "veeradittya/polymarket-insider-detection", "vsbtc/polymarket-insider-detection", "pselamy/polymarket-insider-tracker",
        "orcalayer/polymarket-insider-score-backtest", "Benja-Pauls/polymarket-insider-detection", "matthewmurden/polymarket-insider-detection",
        "yasithdsl/polymarket-surveillance", "BRKME/Polymarket_insider"})
    check("every repository has a licence statement and an https URL", all(r["license"] and r["url"].startswith("https://github.com/") for r in scout["repos"]))
    for name in ("andy1245-rgb/PolyCrawler", "NickNaskida/polymarket-insider-bot"):    # the two rules re-implemented in the Nobel note
        r = next(x for x in scout["repos"] if x["name"] == name)
        check(f"{name} is under a permissive licence", any(k in r["license"] for k in PERMISSIVE))
    check("no first-place claim", "COMPETITIVE_NOT_FIRST_PROVEN" in rep and "first place" in rep)
    nobel = os.path.join(REPO, "research_notes", "nobel-strict-replay-2026-11-20", "data")
    if os.path.isdir(nobel):                                                       # only once that note is in the tree
        with open(os.path.join(nobel, "queue.json")) as f:
            q = json.load(f)["classes"]
        with open(os.path.join(nobel, "ext_nn.json")) as f:
            nn = json.load(f)
        check("EXT_PC figures match the Nobel note", f"1st of {q['INFO:ext_pc']['alerts']}" in rep)
        check("EXT_NN figures match the Nobel note", f"1st of {nn['flagged']} flagged" in rep)
        check("C1 figures match the Nobel note", f"{q['INFO:c1']['first_on_eight_rank_by_time']}th of {q['INFO:c1']['alerts']}" in rep)
    print(f"{len(ok)} checks passed, {len(bad)} failed")
    for x in bad:
        print("FAILED:", x)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
