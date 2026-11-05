"""Builds evidence/ and the tables of this note from the raw collection kept outside git.

    python3 -I scripts/build.py <raw_dir>

Copies on-chain and Relay responses verbatim, reduces Polymarket API responses (drops third-party
profile fields, keeps the public username), writes SHA256SUMS.txt, transactions.csv, accounts.csv,
graph.json, graph.mmd and rarity.json. The figures of REPORT.md are recomputed independently by verify.py.
"""
import csv, hashlib, json, shutil, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import netlib as L  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
EV = HERE / "evidence"
DROP = {"bio", "pseudonym", "profile_image", "profile_image_optimized", "profileImage", "profileImageOptimized",
        "users", "icon", "xUsername", "verifiedBadge"}


def reduce(o):
    if isinstance(o, dict):
        return {k: reduce(v) for k, v in o.items() if k not in DROP}
    if isinstance(o, list):
        return [reduce(v) for v in o]
    return o


def copy_tree(raw):
    if EV.exists():
        shutil.rmtree(EV)
    plan = [("http", "relay_user_*", "relay"), ("bsc", "*", "bsc"), ("polygon", "*", "polygon"),
            ("etherscan", "*", "etherscan"), ("http", "bs_meta_*", "http")]
    for sub, pat, dst in plan:
        for f in sorted((raw / sub).glob(pat)):
            if f.is_file():
                (EV / dst).mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, EV / dst / f.name)
    for d in sorted((raw / "sol").iterdir()):
        if d.is_dir():
            shutil.copytree(d, EV / "sol" / d.name)
    red, orig = EV / "polymarket_reduced", []
    red.mkdir(parents=True)
    for f in sorted((raw / "http").glob("pm_*.json")):
        if f.name.endswith(".meta.json"):
            continue
        body = f.read_bytes()
        (red / f.name).write_text(json.dumps(reduce(json.loads(body)), indent=1))
        meta = f.with_suffix(".meta.json")
        orig.append({"file": f.name, "sha256": hashlib.sha256(body).hexdigest(),
                     "meta": json.loads(meta.read_text()) if meta.exists() else None})
    (red / "ORIGINALS.json").write_text(json.dumps({"note": "Original Polymarket API responses kept outside git. Fields "
                                                    "dropped: " + ", ".join(sorted(DROP)), "files": orig}, indent=1))


def sums():
    lines = []
    for p in sorted(EV.rglob("*")):
        if p.is_file():
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(HERE)}")
    (HERE / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    return len(lines)


def tables():
    links = L.links(EV)
    with open(HERE / "transactions.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(links[0].keys()))
        w.writeheader()
        w.writerows(links)
    acc = L.accounts(EV)
    with open(HERE / "accounts.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(acc[0].keys()))
        w.writeheader()
        w.writerows(acc)
    nodes, edges = {}, defaultdict(lambda: {"n": 0, "usd": 0.0, "kinds": set()})
    for x in links:
        for side in ("from", "to"):
            nodes[x[f"{side}_address"]] = x[f"{side}_label"]
        e = edges[(x["from_address"], x["to_address"])]
        e["n"] += 1
        e["usd"] += float(x["amount"] or 0)
        e["kinds"].add(x["kind"])
    g = {"nodes": [{"id": k, "label": v} for k, v in sorted(nodes.items())],
         "edges": [{"from": a, "to": b, "transfers": e["n"], "amount": round(e["usd"], 6), "kinds": sorted(e["kinds"])}
                   for (a, b), e in sorted(edges.items())]}
    (HERE / "graph.json").write_text(json.dumps(g, indent=1))
    ids = {k: f"n{i}" for i, k in enumerate(sorted(nodes))}
    mm = ["flowchart LR"] + [f'  {ids[k]}["{v}"]' for k, v in sorted(nodes.items())]
    mm += [f'  {ids[a]} -->|"{e["n"]} tx, {e["usd"]:,.0f}"| {ids[b]}' for (a, b), e in sorted(edges.items())]
    (HERE / "graph.mmd").write_text("\n".join(mm) + "\n")
    pop = (HERE / "population.txt").read_text().split()
    r = L.rarity(EV, pop)
    if r["collected"] == len(pop):  # PLAN_RARITY.md: no partial statistic is published as a result
        (HERE / "rarity.json").write_text(json.dumps(r, indent=1))


if __name__ == "__main__":
    copy_tree(Path(sys.argv[1]))
    tables()
    print("evidence files", sums())
