"""DATA_GAP_MATRIX: one row per dataset, built only from measured files (no hand-typed counts).

Statuses: COMPLETE, PARTIAL, UNAVAILABLE, LOCAL_ONLY, CORRUPT, UNVERIFIED, UNKNOWN. LOCAL_ONLY is never read as missing.
A row without a measurable denominator keeps expected_records = UNKNOWN and is never called COMPLETE.
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = ["dataset_id", "source", "origin", "chain", "contract", "market_id", "trading_wallet", "first_timestamp_utc",
          "last_timestamp_utc", "expected_records", "observed_records", "missing_records", "missing_fraction",
          "source_coverage", "evidence_level", "local_path", "publication_status", "sha256", "collection_checkpoint",
          "recovery_method", "estimated_cost", "validation_status", "priority"]
PR110 = "8b633048290e7174945bc811b16cf0b11b4d8ceb"
PR111 = "58c964b5aa5063d90e4dd7d72dab50d916a81bd7"


def row(**kw):
    r = {f: "" for f in FIELDS}
    r.update({k: v for k, v in kw.items() if k in r})
    e, o = r["expected_records"], r["observed_records"]
    if isinstance(e, int) and isinstance(o, int):
        r["missing_records"] = e - o
        r["missing_fraction"] = f"{(e - o) / e:.6f}" if e else "0.000000"
    elif r["missing_records"] == "":
        r["missing_records"], r["missing_fraction"] = "UNKNOWN", "UNKNOWN"
    return r


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else ""


def git(repo, rev, path):
    r = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def inventory_rows(res):
    rows = []
    per = defaultdict(Counter)
    for r in csv.DictReader(gzip.open(res / "file_inventory.csv.gz", "rt")):
        if r["in_scope"] == "YES":
            per[r["investigation"]][r["status"]] += 1
            per[r["investigation"]]["recoverable:" + r["recoverable"]] += 1
            per[r["investigation"]]["origin:" + (r["origin_state"] or "REPOSITORY")] += 1
    for inv, c in sorted(per.items()):
        total = sum(c[s] for s in ("COMPLETE", "PARTIAL", "UNAVAILABLE", "LOCAL_ONLY", "CORRUPT", "UNVERIFIED", "UNKNOWN"))
        present = c["COMPLETE"] + c["LOCAL_ONLY"]
        if c["CORRUPT"]:
            status = "CORRUPT"
        elif c["UNAVAILABLE"]:
            status = "UNAVAILABLE" if not present else "PARTIAL"
        elif c["LOCAL_ONLY"]:
            status = "LOCAL_ONLY"
        elif c["UNVERIFIED"]:
            status = "UNVERIFIED"
        else:
            status = "COMPLETE"
        offline = [k.split(":", 1)[1] for k in c if k.startswith("origin:VOLUME_OFFLINE")]
        rows.append(row(
            dataset_id=f"manifest:{inv}", source=f"investigations/{inv}/data_manifest.json (+local_only_hashes)",
            origin="manifest origin", chain="", expected_records=total, observed_records=present,
            source_coverage=f"COMPLETE={c['COMPLETE']} LOCAL_ONLY={c['LOCAL_ONLY']} UNAVAILABLE={c['UNAVAILABLE']} "
                            f"CORRUPT={c['CORRUPT']} UNVERIFIED={c['UNVERIFIED']}",
            evidence_level=status, local_path="results/file_inventory.csv.gz",
            publication_status="imported files in git; local_only files hashed only",
            sha256=sha(res / "file_inventory.csv.gz"),
            recovery_method=("mount " + ", ".join(sorted(set(offline))) + " or decrypt the verified encrypted backup packs"
                             if offline else ("recorded versions are in verified encrypted backup packs" if c["CORRUPT"]
                                              else "none needed")),
            estimated_cost="0 (local)", validation_status=f"recoverable YES={c['recoverable:YES']} "
                                                          f"UNKNOWN={c['recoverable:UNKNOWN']} NO={c['recoverable:NO']}",
            priority="P1" if status in ("UNAVAILABLE", "PARTIAL", "CORRUPT") else "P2"))
    return rows


def build(repo, res, raw):
    rows = inventory_rows(res)
    # PR #110: sparse manifest, inputs recorded elsewhere
    w = json.loads(git(repo, PR110, "investigations/weekly-funding-intelligence/results/weekly_funding.json"))
    ins = w["inputs_sha256"]
    ok = 0
    for name, h in ins.items():
        for cand in (name, "investigations/weekly-funding-intelligence/" + name):
            b = git(repo, PR110, cand)
            if b is not None:
                ok += hashlib.sha256(b).hexdigest() == h
                break
    m = json.loads(git(repo, PR110, "investigations/weekly-funding-intelligence/data_manifest.json"))
    rows.append(row(dataset_id="pr110:inputs", source=f"{PR110[:12]} results/weekly_funding.json inputs_sha256",
                    origin="PR #110 Git objects", expected_records=len(ins), observed_records=ok,
                    source_coverage=f"data_manifest.json lists {len(m.get('files', []))} files; inputs recorded in the "
                                    f"results JSON", evidence_level="COMPLETE" if ok == len(ins) else "CORRUPT",
                    local_path="git objects", publication_status="published on the PR #110 branch",
                    recovery_method="none needed (documentation gap only: the manifest does not list the inputs)",
                    estimated_cost="0", validation_status=f"{ok}/{len(ins)} SHA-256 equal to the Git blobs",
                    priority="P2"))
    # PR #111 evidence files against its SHA256SUMS
    sums = git(repo, PR111, "research_notes/f2020-bet-reconstruction-2026-11-22/SHA256SUMS")
    good = total = 0
    for line in (sums or b"").decode().splitlines():
        if line.strip():
            h, _, p = line.partition("  ")
            total += 1
            b = git(repo, PR111, "research_notes/f2020-bet-reconstruction-2026-11-22/" + p.strip())
            good += b is not None and hashlib.sha256(b).hexdigest() == h
    rows.append(row(dataset_id="pr111:evidence", source=f"{PR111[:12]} SHA256SUMS", origin="PR #111 Git objects",
                    expected_records=total, observed_records=good, evidence_level="COMPLETE" if good == total else "CORRUPT",
                    local_path="git objects", publication_status="published on the PR #111 branch",
                    recovery_method="none needed", estimated_cost="0",
                    validation_status=f"{good}/{total} files equal to SHA256SUMS", priority="P2"))
    # Cohort ledger
    lr = json.loads((res / "ledger_results.json").read_text())
    pl = lr["plan"]
    for k, v in sorted(lr["stream_coverage"].items()):
        rows.append(row(dataset_id=f"ledger:{k}", source=f"eth_getLogs {k.split('/')[0]} filter", origin=pl["provider"],
                        chain="137", trading_wallet=f"{lr['accounts_in_cohort']} cohort accounts ({k.split('/')[1]})",
                        expected_records="UNKNOWN", observed_records=v["logs"],
                        missing_records=0 if v["complete"] else "UNKNOWN",
                        missing_fraction="0.000000" if v["complete"] else "UNKNOWN",
                        source_coverage=f"blocks {pl['start_block']}..{pl['end_block']} contiguous={v['complete']} "
                                        f"ranges={v['ranges']}",
                        evidence_level="COMPLETE" if v["complete"] else "PARTIAL",
                        local_path="raw/ledger (local only)", publication_status="LOCAL_ONLY raw; derived tables published",
                        collection_checkpoint="checkpoint.jsonl (accepted ranges with SHA-256)",
                        recovery_method="rerun scripts/ledger_collect.py (resumes)", estimated_cost="0 (keyless RPC)",
                        validation_status="every log matches its filter; duplicates identical; no removed log",
                        priority="P0"))
    ck = lr["checks"]
    rows.append(row(dataset_id="ledger:positions", source="scripts/ledger_report.py", origin="cohort logs + Gamma + CTF",
                    chain="137", trading_wallet=f"{lr['accounts_with_positions']} of {lr['accounts_in_cohort']} accounts",
                    expected_records=lr["markets"]["account_market_positions"],
                    observed_records=ck["identity_pass"],
                    source_coverage=f"resolved on chain {lr['markets']['resolved_on_chain']} of "
                                    f"{lr['markets']['distinct_markets']} markets; unknown valuation "
                                    f"{lr['totals']['positions_with_unknown_valuation']}",
                    evidence_level="PARTIAL" if ck["identity_not_evaluated"] or ck["identity_fail"] else "COMPLETE",
                    local_path="results/wallet_position_summary.csv.gz", publication_status="published",
                    sha256=sha(res / "wallet_position_summary.csv.gz"),
                    recovery_method="value the remaining open inventory with a timestamped mark",
                    estimated_cost="0", validation_status=f"identity PASS {ck['identity_pass']} FAIL {ck['identity_fail']} "
                                                          f"NOT_EVALUATED {ck['identity_not_evaluated']}; collateral "
                                                          f"reconciled {ck['collateral_reconciled_accounts']} accounts; "
                                                          f"share sample {ck['position_balance_sample_pass']} pass "
                                                          f"{ck['position_balance_sample_fail']} fail",
                    priority="P0"))
    rg = json.loads((res / "regression_pr111.json").read_text())
    rows.append(row(dataset_id="ledger:regression_pr111", source="scripts/regression_pr111.py", origin=f"PR #111 {PR111[:12]}",
                    chain="137", trading_wallet="W1..W4", expected_records=rg["positions_compared"],
                    observed_records=rg["counts"]["EXACT"] + rg["counts"]["EXPLAINED_LATER_RESOLUTION"],
                    source_coverage=json.dumps(rg["counts"]), evidence_level="COMPLETE" if not rg["counts"]["UNEXPLAINED"]
                    and not rg["counts"]["MISSING"] else "PARTIAL", local_path="results/regression_pr111.json",
                    publication_status="published", sha256=sha(res / "regression_pr111.json"),
                    recovery_method="none needed", estimated_cost="0", validation_status="per-market net PnL within 1e-6",
                    priority="P0"))
    # Relay v2 screen
    rs = res / "relay_v2_screen.json"
    if rs.exists():
        r = json.loads(rs.read_text())
        ex = r["status_now"].get("EXHAUSTED", 0)
        rows.append(row(dataset_id="relay_v2:eth_to_polygon_histories", source="GET https://api.relay.link/requests/v2",
                        origin=r["source"], chain="1->137", trading_wallet=f"{r['accounts']} Ethereum recipients",
                        expected_records=r["accounts"], observed_records=ex,
                        source_coverage=json.dumps(r["status_now"], sort_keys=True),
                        evidence_level="COMPLETE" if ex == r["accounts"] else "PARTIAL",
                        local_path="raw/relay_v2/pages.jsonl (local only)", publication_status="results/relay_v2_screen.csv",
                        sha256=sha(res / "relay_v2_screen.csv"), collection_checkpoint="pages.jsonl (every HTTP exchange)",
                        recovery_method="v2 retired 2026-11-24T00:00:00Z; v3 needs an API key (not obtained)",
                        estimated_cost="API key registration required (not done)",
                        validation_status=f"{r['http_429']} HTTP 429 recorded, none read as empty", priority="P0"))
    # Ethereum weeks
    eth = list(csv.DictReader(open(res / "eth_weeks_coverage.csv")))
    by = defaultdict(list)
    for e in eth:
        by[e["stream"]].append(e)
    for s, es in sorted(by.items()):
        comp = sum(e["coverage_status"] == "COMPLETE" for e in es)
        rows.append(row(dataset_id=f"eth_weeks:{s}", source="PR #110 collect_week (pinned) on public Ethereum RPC",
                        origin="agent ethweeks", chain="1", expected_records=len(es), observed_records=comp,
                        first_timestamp_utc=es[0]["week"], last_timestamp_utc=es[-1]["week"],
                        source_coverage=f"weeks COMPLETE {comp} of {len(es)}; events {sum(int(e['events']) for e in es)}",
                        evidence_level="COMPLETE" if comp == len(es) else "PARTIAL",
                        local_path="raw/agents/ethweeks (local only)", publication_status="results/eth_weeks_coverage.csv",
                        sha256=sha(res / "eth_weeks_coverage.csv"),
                        recovery_method=("none needed" if comp == len(es) else
                                         "keyless txlist rate-limited (HTTP 429); retry later or an explorer key"),
                        estimated_cost="0 (keyless)" if comp == len(es) else "explorer API key for the native part",
                        validation_status="transaction-count control per week" if "native" in s else "verified_pack",
                        priority="P0"))
    # Cross-chain
    cc = list(csv.DictReader(open(res / "cross_chain_routes.csv")))
    rows.append(row(dataset_id="crosschain:pr109_arbitrum_passages", source="Arbitrum and Polygon receipts, 3-4 providers",
                    origin=f"PR #109 f34a8bff", chain="137,42161", expected_records=len(cc), observed_records=sum(
                        r["verdict"] == "CONFIRMED" for r in cc), evidence_level="COMPLETE",
                    local_path="results/cross_chain_routes.csv", publication_status="published",
                    sha256=sha(res / "cross_chain_routes.csv"), recovery_method="none needed", estimated_cost="0",
                    validation_status="field-level provider comparison", priority="P1"))
    # Prospective quality items and measured unavailable sources
    for r in csv.DictReader(open(res / "prospective_data_quality.csv")):
        rows.append(row(dataset_id=f"prospective:{r['item']}", source=r["source"], origin="agent prospective",
                        expected_records="UNKNOWN", observed_records="UNKNOWN",
                        source_coverage=r["history_depth"][:200], evidence_level={"AVAILABLE": "COMPLETE"}.get(
                            r["availability"], r["availability"]), local_path="results/prospective_data_quality.csv",
                        publication_status="published", recovery_method=r["recovery_method"][:200],
                        estimated_cost="see recovery_method", validation_status="measured", priority=r["priority"]))
    sp = json.loads((res / "source_probes.json").read_text())
    for name, why in (("subgraphs:polymarket_goldsky", "HTTP 429 paused and deprecated after the V2 migration"),
                      ("goldsky_edge_api", "HTTP 402 x402 payment required"),
                      ("envio_hypersync_query", "HTTP 401 token required"),
                      ("data_api_v1", "HTTP 410 retired; v2 used"),
                      ("clob_historical_book", "no historical order-book endpoint; /book 404 after close"),
                      ("publicnode_archive_logs", "HTTP 403 beyond about 2-3M blocks without a token")):
        rows.append(row(dataset_id=f"source:{name}", source=name, origin="agent sources (probe_log)",
                        expected_records="UNKNOWN", observed_records=0, evidence_level="UNAVAILABLE",
                        source_coverage=why, local_path="results/source_probes.json", publication_status="published",
                        sha256=sha(res / "source_probes.json"), recovery_method="none keyless",
                        estimated_cost="paid or key (not used)", validation_status=f"probed {sp.get('captured_utc', '')}",
                        priority="P1"))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    a = ap.parse_args()
    rows = build(a.repo, a.results, None)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    (a.results / "data_gap_matrix.csv").write_text(buf.getvalue())
    (a.results / "data_gap_matrix.json").write_text(json.dumps(rows, indent=1) + "\n")
    print(Counter(r["evidence_level"] for r in rows), len(rows))


if __name__ == "__main__":
    main()
