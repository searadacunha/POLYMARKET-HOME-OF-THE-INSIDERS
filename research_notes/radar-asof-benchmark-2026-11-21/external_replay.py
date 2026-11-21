"""Independent arithmetic on pinned public third-party tables. No external code runs and no raw inputs are copied."""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import statistics
import subprocess

HERE = Path(__file__).resolve().parent
PINS = {r["repository"]: r for r in json.loads((HERE / "sources.json").read_text())["repositories"]}
FFIC = "ForesightFlow/datasets"
WHALES = "0xinsider/research"
SKILL = "tlafargue/polymarket-research"
SPORTS = "GitHubMagnus/polymarket-calibration"
SCORES = "vsbtc/polymarket-insider-detection"


def blob(cache, repo, filename, fetch):
    pin = PINS[repo]
    directory = cache / repo.replace("/", "__")
    if not directory.exists() and fetch:
        directory.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "--quiet", str(directory)], check=True)
        subprocess.run(["git", "-C", str(directory), "remote", "add", "origin", "https://github.com/" + repo + ".git"], check=True)
        subprocess.run(["git", "-C", str(directory), "config", "remote.origin.promisor", "true"], check=True)
        subprocess.run(["git", "-C", str(directory), "config", "remote.origin.partialclonefilter", "blob:none"], check=True)
    if fetch and subprocess.run(["git", "-C", str(directory), "cat-file", "-e", pin["head"] + "^{commit}"], capture_output=True).returncode:
        subprocess.run(["git", "-C", str(directory), "fetch", "--quiet", "--depth=1", "--filter=blob:none", "origin", pin["head"]], check=True)
    content = subprocess.check_output(["git", "-C", str(directory), "show", pin["head"] + ":" + filename])
    if hashlib.sha256(content).hexdigest() != pin["local_blobs"][filename]:
        raise ValueError(f"hash mismatch for {repo}/{filename}")
    return content


def ranks(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    rank = [0.0] * len(order)
    i = 0
    while i < len(order):
        end = i + 1
        while end < len(order) and values[order[end]] == values[order[i]]:
            end += 1
        for j in range(i, end):
            rank[order[j]] = (i + end + 1) / 2
        i = end
    return rank


def run(cache, fetch):
    def read(repo, path):
        return blob(cache, repo, path, fetch)
    def rows(repo, path):
        return list(csv.DictReader(io.StringIO(read(repo, path).decode("utf-8-sig"))))
    f = rows(FFIC, "ffic-inventory/ffic-v1.csv")
    prefix = "cost-of-late-whale-alerts/2026-10-11-cost-of-late-whale-alerts-cohort.csv"
    large = rows(WHALES, prefix)
    deltas = [100 * (float(r["price_24h"]) - float(r["price_5m"])) for r in large if r["price_5m"] and r["price_24h"]]
    import pyarrow.parquet as pq  # optional, only the external replay requires a Parquet reader
    wallet = pq.read_table(io.BytesIO(read(SKILL, "data/wallet_skill_splithalf.parquet")), columns=["edge_a", "edge_b"]).to_pydict()
    a, b = ranks(wallet["edge_a"]), ranks(wallet["edge_b"])
    long = rows(SPORTS, "data/calibration_long.csv")
    meta = {r["market_id"]: r for r in rows(SPORTS, "data/markets.csv")}
    week = [r for r in long if int(r["horizon_days"]) == 7 and r["category"] == "Sports"]
    bucket = [r for r in week if 0.55 <= float(r["implied_prob"]) < 0.60]
    available = [r for r in bucket if float(r["price_ts"]) <= float(r["target_ts"])]
    games = [r for r in available if re.fullmatch(r"(mlb|nba|nfl|nhl)-[a-z0-9]+-[a-z0-9]+-\d{4}-\d\d-\d\d(?:-(?:game-)?[12])?", meta[r["market_id"]]["slug"])]
    rank_table = rows(SCORES, "data/processed/wallet_rankings.csv")
    return {"ffic": {"cases": len({r["case_id"] for r in f}), "rows": len(f), "unique_market_prefixes": len({r["market_id_prefix"] for r in f}),
                     "trade_history": dict(Counter(r["trade_history_available"] for r in f))},
            "large_buys": {"rows": len(large), "paired_5m_24h": len(deltas), "mean_cents": round(statistics.mean(deltas), 5),
                           "median_cents": round(statistics.median(deltas), 5)},
            "wallet_skill": {"wallets": len(a), "spearman": round(statistics.correlation(a, b), 7)},
            "sports_transfer": {"all_t7_sports": len(week), "bucket_rows": len(bucket), "at_or_before_target": len(available),
                                "eligible_events": len({r["event_id"] for r in available}), "eligible_wins": sum(int(r["outcome"]) for r in available),
                                "strict_four_league_moneylines": len(games),
                                "strict_wins": sum(int(r["outcome"]) for r in games) if games else None},
            "vsbtc": {"ranking_rows": len(rank_table), "distinct_wallets": len({r["proxyWallet"].lower() for r in rank_table})}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path, help="directory containing owner__repository clones")
    parser.add_argument("--fetch", action="store_true", help="fetch missing pinned revisions into the cache")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.dumps(run(args.cache, args.fetch), indent=2, sort_keys=True) + "\n"
    if args.check:
        if data != (HERE / "external_results.json").read_text():
            raise SystemExit("external reproduction differs")
        print("external tables reproduced")
    else:
        print(data, end="")
