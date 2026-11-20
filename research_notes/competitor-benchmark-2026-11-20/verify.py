"""Offline checks of the competitor benchmark, and the renderer of REPORT.md from benchmark.json.

    python3 -B verify.py            named checks, "N/M checks pass", exit 1 on any failure; no network
    python3 -B verify.py --write    re-render REPORT.md from benchmark.json, then check
    python3 -B verify.py --online   also re-read the head commit of each compared repository (public GitHub API)

Competitor evidence tokens: a path in the archived tree listing, "(tree)" for a fact read from the whole listing
(an absence, a count), or "(api:<field>)" for a field of the archived API metadata (license, runs, compare).
"""
import csv
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

NOTE = Path(__file__).resolve().parent
ROOT = NOTE.parent.parent
POSITIONS = ("ahead", "level", "mixed", "behind", "not compared")


def load(note=NOTE):
    return (json.loads((note / "benchmark.json").read_text()),
            json.loads((note / "raw" / "github_api_metadata.json").read_text()))


def short(sha):
    return sha[:7]


def ours_md(paths):
    return ", ".join(f"[`{p}`](../../{p})" for p in paths) or "none"


def theirs_md(tokens):
    return ", ".join(f"`{t}`" for t in tokens) or "none read"


def counts(data):
    return {p: [c["name"] for c in data["capabilities"] if c["position"] == p] for p in POSITIONS}


def result_sentence(data):
    n = counts(data)
    parts = [f"{p} on {len(n[p])} ({', '.join(n[p])})" for p in POSITIONS if n[p]]
    return (f"Across {len(data['capabilities'])} capabilities compared with {len(data['repos'])} public repositories, "
            f"this repository is " + "; ".join(parts) + ".")


def render(data, meta):
    heads = {r: m["head"] for r, m in meta["repos"].items()}
    o = data["our_repository"]
    out = [f"# {data['title']}", "",
           f"**Type:** comparison note built from code read at pinned commits; the data is [`benchmark.json`](benchmark.json) "
           f"and this page is its rendering by [`verify.py`](verify.py), which also checks it offline. "
           f"This repository was read at `{short(o['commit_read'])}`. {o['note']}", "",
           f"Status words: {data['status_words']}", "",
           "## Result", "", result_sentence(data), "",
           "| Capability | Position | Basis |", "|---|---|---|"]
    out += [f"| {c['name']} | **{c['position']}** | {c['basis']} |" for c in data["capabilities"]]
    out += [""] + [p for t in data["result_text"] for p in (t, "")]
    out += [f"{len(data['blockers'])} weaknesses prevent a first-place claim; they are listed below with their evidence.", "",
            "## Method", ""] + [f"- {m}" for m in data["method"]]
    out += ["", "## Compared repositories", "",
            "| Repository | Licence | Commit read | Last commit (UTC) | What it does |", "|---|---|---|---|---|"]
    for r in data["repos"]:
        h = heads[r["name"]]
        out.append(f"| [{r['name']}]({r['url']}) | {r['licence']['value']} ({theirs_md(r['licence']['evidence'])}) | "
                   f"`{h['sha']}` | {h['committer_date']} | {r['what_it_does']} |")
    out += ["", "## Capability matrix", "", "Competitor paths are at the commit listed above; ours are links into this clone.", ""]
    for c in data["capabilities"]:
        out += [f"### {c['name']}: {c['position']}", "",
                f"- **This repository:** {c['ours']['value']}. Evidence: {ours_md(c['ours']['evidence'])}"]
        out += [f"- **{r}:** {v['value']}. Evidence: {theirs_md(v['evidence'])}" for r, v in c["cells"].items()]
        out.append("")
    out += ["## Repository by repository", ""]
    for r in data["repos"]:
        out += [f"### {r['name']}", ""]
        for key, label in (("strengths", "Strengths"), ("defects", "Defects"),
                           ("better_than_us", "What it does better than this repository"),
                           ("we_do_better", "What this repository does better")):
            out += [f"**{label}**", ""]
            out += [f"- {s['text']} ({s['status']}). Theirs: {theirs_md(s['theirs'])}. Ours: {ours_md(s['ours'])}" for s in r[key]]
            out.append("")
        if r["earlier_card_errors"]:
            out += ["**Errors of the earlier provisional card**", ""] + [f"- {e}" for e in r["earlier_card_errors"]] + [""]
    out += ["## Corrections to earlier statements about this repository", ""]
    out += [f"- {s['text']} Evidence: {ours_md(s['ours'])}" for s in data["our_side_corrections"]]
    out += ["", "## Capabilities worth integrating", "",
            "Ranked by the readers' priority (the compared set first, then the scout's projects); not a measured ranking.", "",
            "| Rank | Capability | Source | What the licence allows | Today | Measurable gain | Effort | Ours |",
            "|---|---|---|---|---|---|---|---|"]
    out += [f"| {i['rank']} | {i['capability']} | {i['source']} | {i['licence_allows']} | {i['today']} | {i['gain']} | "
            f"{i['effort']} | {ours_md(i['ours'])} |" for i in data["integrate"]]
    out += ["", "## Newer projects and papers found by the scout", "",
            "| Project | Licence | Last commit (UTC) | What it offers | Caveats |", "|---|---|---|---|---|"]
    out += [f"| [{p['name']}]({p['url']}) | {p['licence']} | {p['last_commit_utc']} | {p['offers']} | {p['caveats']} |"
            for p in data["scout"]["projects"]]
    out += ["", "| Paper | Method we could use |", "|---|---|"]
    out += [f"| [{p['title']}]({p['url']}) | {p['use']} |" for p in data["scout"]["papers"]]
    out += ["", "## Weaknesses that prevent a first-place claim", ""]
    out += [f"{n}. {b['text']}. Evidence: {ours_md(b['ours'])}" for n, b in enumerate(data["blockers"], 1)]
    out += ["", "## What is not shown", ""] + [f"- {t}" for t in data["not_shown"]]
    out += ["", "## Reproduce", "", "```bash"] + data["reproduce"] + ["```", "", "## Limits", ""]
    out += [f"- {t}" for t in data["limits"]]
    return "\n".join(out) + "\n"


def their_tokens(data):
    """(repo, token) for every competitor evidence token in the data."""
    for r in data["repos"]:
        for t in r["licence"]["evidence"]:
            yield r["name"], t
        for key in ("strengths", "defects", "better_than_us", "we_do_better"):
            for s in r[key]:
                for t in s["theirs"]:
                    yield r["name"], t
    for c in data["capabilities"]:
        for repo, v in c["cells"].items():
            for t in v["evidence"]:
                yield repo, t


def our_paths(data):
    for r in data["repos"]:
        for key in ("strengths", "defects", "better_than_us", "we_do_better"):
            for s in r[key]:
                yield from s["ours"]
    for c in data["capabilities"]:
        yield from c["ours"]["evidence"]
    for group in ("our_side_corrections", "integrate", "blockers"):
        for s in data[group]:
            yield from s["ours"]
    for c in data["our_counts"]:
        yield c["path"]


def check_their_paths(data, meta):
    bad = []
    for repo, t in their_tokens(data):
        m = meta["repos"].get(repo)
        if m is None:
            bad.append(f"{repo}: no archived metadata")
        elif t == "(tree)":
            continue
        elif t.startswith("(api:"):
            if t[5:-1] not in m:
                bad.append(f"{repo}: {t} not in metadata")
        elif t not in {b[0] for b in m["tree"]["blobs"]}:
            bad.append(f"{repo}: {t} not in tree listing")
    return bad


def check_our_paths(data, root=ROOT):
    return sorted({p for p in our_paths(data) if not (root / p).exists()})


def check_commits(data, meta):
    bad = []
    for r in data["repos"]:
        m = meta["repos"].get(r["name"])
        sha = m["head"]["sha"] if m else ""
        if not re.fullmatch(r"[0-9a-f]{40}", sha) or m["tree"]["sha"] != sha or m["tree"]["truncated"]:
            bad.append(r["name"])
    if not re.fullmatch(r"[0-9a-f]{40}", data["our_repository"]["commit_read"]):
        bad.append("our commit_read")
    return bad


def check_both_sides(data):
    bad = []
    for r in data["repos"]:
        for key in ("strengths", "defects", "better_than_us", "we_do_better"):
            bad += [f"{r['name']} {key}: {s['text'][:40]}" for s in r[key]
                    if not s["theirs"] or not s["ours"] or s["status"] not in ("VERIFIED", "REPORTED")]
    return bad


def check_matrix(data):
    names = [r["name"] for r in data["repos"]]
    bad = []
    for c in data["capabilities"]:
        if c["position"] not in POSITIONS or not c["ours"]["evidence"] or sorted(c["cells"]) != sorted(names):
            bad.append(c["id"])
        bad += [f"{c['id']}/{r}" for r, v in c["cells"].items() if not v["evidence"] and v["value"] != "Not assessed"]
    return bad


def check_result_counts(data, report):
    """Every count quoted in the Result section equals the count in the data."""
    sec = report.split("## Result", 1)[-1].split("\n## ", 1)[0]
    n = counts(data)
    want = {"capabilities": len(data["capabilities"]), "public repositories": len(data["repos"]),
            "weaknesses": len(data["blockers"]), **{p: len(n[p]) for p in POSITIONS}}
    got = {k: int(v) for v, k in re.findall(r"(\d+) (capabilities|public repositories|weaknesses)", sec)}
    got.update({k: int(v) for k, v in re.findall(r"(ahead|level|mixed|behind|not compared) on (\d+)", sec)})
    return [f"{k}: Result says {got.get(k)}, data has {v}" for k, v in want.items() if v and got.get(k) != v]


FRENCH = re.compile(r"\b(les|des|une|est|dans|pour|avec|sont|nous|cette|qui|pas|sur|aux|du)\b", re.I)
ENGLISH = re.compile(r"\b(the|and|is|are|with|for|this|that|not|of|to|in)\b", re.I)


def recount(path, how):
    if how == "lines":
        with path.open() as f:
            return sum(1 for _ in f)
    if how == "french_md":
        # tracked .md files outside sources/ folders with at least 20 French function words and more French than English ones
        tracked = subprocess.run(["git", "-C", str(path), "ls-files", "*.md"], capture_output=True, text=True, check=True).stdout.split("\n")
        texts = ((path / f).read_text(errors="replace") for f in tracked if f and "sources" not in f.split("/")[:-1])
        return sum(1 for t in texts if len(FRENCH.findall(t)) >= 20 and len(FRENCH.findall(t)) > len(ENGLISH.findall(t)))
    if how == "ci_verify_scripts_all":
        return len(set(re.findall(r"research_notes/\S+?/verify\.py", path.read_text())))
    if how == "csv_rows":
        with path.open(newline="") as f:
            return sum(1 for _ in csv.DictReader(f))
    if how == "dated":
        cases = json.loads(path.read_text())
        cases = cases["cases"] if isinstance(cases, dict) else cases  # the two registries use both shapes
        return [sum(1 for c in cases if c.get("first_public_information_utc")), len(cases)]
    if how == "ci_verify_scripts":
        return len(set(re.findall(r"research_notes/[^ /]+/verify\.py", path.read_text())))
    value = json.loads(path.read_text())
    for key in how.split(":", 1)[1].split("."):
        value = value[key]
    return value


def check_our_counts(data, root=ROOT):
    bad = []
    for c in data["our_counts"]:
        try:
            got = recount(root / c["path"], c["how"])
        except (OSError, KeyError, ValueError) as e:
            got = f"error {e}"
        if got != c["expected"]:
            bad.append(f"{c['what']}: expected {c['expected']}, got {got}")
    return bad


def check_style(note=NOTE):
    homes = ("/" + "Users" + "/", "/" + "home" + "/", "~" + "/")  # split so this file does not flag itself
    email = re.compile(r"[\w.+-]+" + "@" + r"[\w-]+\.[a-z]{2,}")
    bad = []
    for p in sorted(note.rglob("*")):
        if p.is_file() and p.suffix in (".md", ".json", ".py"):
            text = p.read_text()
            if chr(0x2014) in text or any(h in text for h in homes) or email.search(text):
                bad.append(p.name)
    return bad


def online(meta):
    for repo, m in sorted(meta["repos"].items()):
        req = urllib.request.Request(f"https://api.github.com/repos/{repo}/commits?per_page=1",
                                     headers={"User-Agent": "benchmark-verify", "Accept": "application/vnd.github+json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                now = json.load(r)[0]["sha"]
            print(f"{'MOVED' if now != m['head']['sha'] else 'same '} {repo}: pinned {short(m['head']['sha'])}, now {short(now)}")
        except Exception as e:  # report and continue: the offline checks decide the exit code
            print(f"ERROR {repo}: {e}")


def main(argv):
    data, meta = load()
    if "--write" in argv:
        (NOTE / "REPORT.md").write_text(render(data, meta))
    report = (NOTE / "REPORT.md").read_text()
    checks = [("report_is_rendering", [] if report == render(data, meta) else ["REPORT.md differs from render(benchmark.json)"]),
              ("our_paths_exist", check_our_paths(data)),
              ("competitor_commits", check_commits(data, meta)),
              ("competitor_paths_in_tree", check_their_paths(data, meta)),
              ("statements_have_both_sides", check_both_sides(data)),
              ("matrix_complete", check_matrix(data)),
              ("result_counts_match_data", check_result_counts(data, report)),
              ("our_counts_recomputed", check_our_counts(data)),
              ("style_no_em_dash_no_home_path", check_style())]
    for name, bad in checks:
        print(f"{'PASS' if not bad else 'FAIL'} {name}" + "".join(f"\n     {b}" for b in bad[:20]))
    ok = sum(1 for _, bad in checks if not bad)
    print(f"{ok}/{len(checks)} checks pass")
    if "--online" in argv:
        online(meta)
    return 0 if ok == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
