"""100-point grid. Unread items score nothing and leave the normalised denominator."""

import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text())


def score_repo(card, repo_id):
    weights = card["weights"]
    items = card["repos"][repo_id]["items"]
    unknown = [item for item in weights if item not in items]
    if unknown:
        raise ValueError(f"{repo_id} missing {unknown}")
    raw = 0
    assessed = 0
    by_dim = {}
    for dim, names in card["dimensions"].items():
        got = seen = 0
        for name in names:
            w = weights[name]
            mark = items[name]["v"]
            if mark not in ("yes", "no", "na"):
                raise ValueError(mark)
            if mark == "na":
                continue
            seen += w
            if mark == "yes":
                got += w
        by_dim[dim] = {"awarded": got, "assessed": seen, "weight": sum(weights[n] for n in names)}
        raw += got
        assessed += seen
    return {
        "id": repo_id,
        "raw": raw,
        "assessed_weight": assessed,
        "normalised": None if assessed == 0 else round(100.0 * raw / assessed, 2),
        "coverage": round(assessed / sum(weights.values()), 4),
        "by_dimension": by_dim,
    }


def rank(card, minimum_coverage=0.75):
    rows = [score_repo(card, repo_id) for repo_id in card["repos"]]
    eligible = [r for r in rows if r["coverage"] + 1e-9 >= minimum_coverage]
    eligible.sort(key=lambda r: (-r["normalised"], -r["raw"], r["id"]))
    return {"minimum_coverage": minimum_coverage, "ranked": eligible, "unranked": [r for r in rows if r not in eligible]}
