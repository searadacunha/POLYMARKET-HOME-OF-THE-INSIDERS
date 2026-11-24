"""Collect, for the f2020 cohort's trading accounts, every finalized Polygon log that moves value for them.

Cohort: the 153 distinct lowercased `account` values of investigations/changenow-polymarket/sources/state/pm_traders.csv
(158 bettor records). Window: from the first block holding V1 CTF Exchange code (33,605,403, 2022-09-26) to the
finalized block read when the plan is made, so each account's whole trading life is in scope.

Seven filters, each run for every cohort chunk (topics are OR-lists of left-padded addresses):
  fills        OrderFilled of the five exchanges, maker (= order owner) in the cohort
  ctf_events   splits, merges, redemptions and conversions on Conditional Tokens and the Neg Risk Adapter,
               stakeholder or redeemer in the cohort
  erc1155_from / erc1155_to   TransferSingle and TransferBatch from / to the cohort (any emitter)
  erc20_from / erc20_to       Transfer from / to the cohort (any emitter; only collateral is valued later)
  adapter_events  any event of the two 2026 collateral adapters whose topic 1 is a cohort account

A range is accepted only when the provider answers it in full and it holds fewer than SPLIT_AT logs (the provider
refuses more than 20,000); otherwise it is halved. A refusal is never read as an empty range. Each accepted range is
stored with its SHA-256 and appended to checkpoint.jsonl, so a run resumes where it stopped.
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from monitoring.phi_monitor import net  # noqa: E402

TENDERLY = "https://gateway.tenderly.co/public/polygon"
COHORT_CSV = "investigations/changenow-polymarket/sources/state/pm_traders.csv"
START_BLOCK = 33_605_403
SPLIT_AT = 10_000
MAX_SPAN = 8_000_000
CHUNK = 80

V1_FILL = "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6"
V2_FILL = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"
EXCHANGES = [
    "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",  # CTF Exchange (2022)
    "0xc5d563a36ae78145c45a50134d48a1215220f80a",  # Neg Risk CTF Exchange (2023)
    "0xe111180000d2663c0091e4f400237545b87b996b",  # CTF Exchange (2026)
    "0xe2222d279d744050d28e00520010520000310f59",  # Neg Risk CTF Exchange (2026)
    "0xe3333700ca9d93003f00f0f71f8515005f6c00aa",  # ExchangeV3 (Polymarket Protocol V2)
]
CTF = "0x4d97dcd97ec945f40cf65f87097ace5ea0476045"
NEG_RISK_ADAPTER = "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TRANSFER_SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
TRANSFER_BATCH = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"
CTF_EVENTS = [
    "0x2e6bb91f8cbcda0c93623c54d0403a43514fabc40084ec96b6d5379a74786298",  # PositionSplit (CTF)
    "0x6f13ca62553fcc2bcd2372180a43949c1e4cebba603901ede2f4e14f36b282ca",  # PositionsMerge (CTF)
    "0x2682012a4a4f1973119f1c9b90745d1bd91fa2bab387344f044cb3586864d18d",  # PayoutRedemption (CTF)
    "0xbbed930dbfb7907ae2d60ddf78345610214f26419a0128df39b6cc3d9e5df9b0",  # PositionSplit (adapter)
    "0xba33ac50d8894676597e6e35dc09cff59854708b642cd069d21eb9c7ca072a04",  # PositionsMerge (adapter)
    "0xb03d19dddbc72a87e735ff0ea3b57bef133ebe44e1894284916a84044deb367e",  # PositionsConverted (adapter)
    "0x9140a6a270ef945260c03894b3c6b3b2695e9d5101feef0ff24fec960cfd3224",  # PayoutRedemption (adapter)
]
# Since 2026, user splits, merges, redemptions and conversions go through these collateral adapters; the CTF and
# Neg Risk Adapter events then name the adapter, and only the adapter's own events name the user (in topic 1).
COLLATERAL_ADAPTERS = [
    "0xada100db00ca00073811820692005400218fce1f",  # binary CTF markets with pUSD
    "0xada2005600dec949baf300f4c6120000bdb6eaab",  # neg-risk markets with pUSD
]


class TooMany(Exception):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pad(a):
    return "0x" + "0" * 24 + a.lower()[2:]


def cohort(repo, rev="HEAD"):
    raw = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{COHORT_CSV}"], check=True,
                         capture_output=True).stdout
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    accounts = sorted({r["account"].lower() for r in rows})
    assert all(len(a) == 42 and a.startswith("0x") for a in accounts)
    return accounts, len(rows), hashlib.sha256(raw).hexdigest()


def filters(chunk):
    t = [pad(a) for a in chunk]
    return {
        "fills": {"address": EXCHANGES, "topics": [[V1_FILL, V2_FILL], None, t]},
        "ctf_events": {"address": [CTF, NEG_RISK_ADAPTER], "topics": [CTF_EVENTS, t]},
        "erc1155_from": {"topics": [[TRANSFER_SINGLE, TRANSFER_BATCH], None, t]},
        "erc1155_to": {"topics": [[TRANSFER_SINGLE, TRANSFER_BATCH], None, None, t]},
        "erc20_from": {"topics": [[TRANSFER], t]},
        "erc20_to": {"topics": [[TRANSFER], None, t]},
        "adapter_events": {"address": COLLATERAL_ADAPTERS, "topics": [None, t]},
    }


def matches(log, flt):
    """The provider must return only what was asked: emitter and every constrained topic position."""
    if "address" in flt and log["address"].lower() not in flt["address"]:
        return False
    topics = [x.lower() for x in log["topics"]]
    for i, want in enumerate(flt["topics"]):
        if want is None:
            continue
        if i >= len(topics) or topics[i] not in want:
            return False
    return True


def get_logs(url, flt, lo, hi):
    body = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
            "params": [{**flt, "fromBlock": hex(lo), "toBlock": hex(hi)}]}
    status, raw = net.fetch(url, data=body, timeout=120, tries=5)
    if status != 200:
        raise net.SourceError(f"HTTP {status} {raw[:200]!r}", status)
    j = json.loads(raw)
    if "error" in j:
        msg = json.dumps(j["error"])  # tenderly puts "Query returned more than 20000 results" in error.data
        if "more than" in msg and "results" in msg:
            raise TooMany(msg)
        raise net.SourceError(f"JSON-RPC error {j['error']}")
    return j["result"], hashlib.sha256(raw).hexdigest()


def done_ranges(ck_path):
    out = {}
    if ck_path.exists():
        for line in ck_path.read_text().splitlines():
            c = json.loads(line)
            out.setdefault((c["filter"], c["chunk"]), []).append((c["from"], c["to"]))
    return out


def run_stream(out, plan, name, chunk_id, flt, lock, log, fetch=get_logs, sleep=time.sleep):
    end, url = plan["end_block"], plan["provider"]
    ck_path = out / "checkpoint.jsonl"
    with lock:
        prior = sorted(done_ranges(ck_path).get((name, chunk_id), []))
    pos = plan["start_block"]
    for a, b in prior:  # accepted ranges are contiguous from the start
        if a != pos:
            raise RuntimeError(f"checkpoint gap for {name}/{chunk_id} at {pos}")
        pos = b + 1
    span, calls = 1_000_000, 0
    while pos <= end:
        hi = min(pos + span - 1, end)
        try:
            logs, body_sha = fetch(url, flt, pos, hi)
            calls += 1
        except TooMany:
            calls += 1
            if hi == pos:
                raise RuntimeError(f"{name}/{chunk_id}: one block {pos} exceeds the provider cap")
            span = max(1, (hi - pos + 1) // 2)
            continue
        if len(logs) >= SPLIT_AT and hi > pos:
            span = max(1, (hi - pos + 1) // 2)
            continue
        bad = [x for x in logs if x.get("removed") or not (pos <= int(x["blockNumber"], 16) <= hi)
               or not matches(x, flt) or not x.get("blockTimestamp")]
        if bad:
            raise RuntimeError(f"{name}/{chunk_id} [{pos},{hi}]: {len(bad)} logs outside the request")
        rel = f"raw/{name}/{chunk_id}/{pos:09d}-{hi:09d}.json.gz"
        rec = {"filter": name, "chunk": chunk_id, "from": pos, "to": hi, "provider": url,
               "received_utc": utc_now(), "response_sha256": body_sha, "n": len(logs), "logs": logs}
        blob = gzip.compress(json.dumps(rec, sort_keys=True).encode(), mtime=0)
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
        with lock:
            with ck_path.open("a") as f:
                f.write(json.dumps({"filter": name, "chunk": chunk_id, "from": pos, "to": hi, "n": len(logs),
                                    "file": rel, "sha256": hashlib.sha256(blob).hexdigest(),
                                    "received_utc": rec["received_utc"]}) + "\n")
            log(f"{name}/{chunk_id} [{pos},{hi}] n={len(logs)}")
        pos = hi + 1
        if len(logs) < SPLIT_AT // 4:
            span = min(MAX_SPAN, span * 2)
        sleep(0.3)
    return calls


def make_plan(repo, out, provider, explicit=None):
    if explicit:  # a named regression cohort instead of pm_traders.csv
        accounts = sorted({a.strip().lower() for a in explicit.split(",") if a.strip()})
        assert all(len(a) == 42 and a.startswith("0x") for a in accounts)
        records, sha = len(accounts), hashlib.sha256(",".join(accounts).encode()).hexdigest()
    else:
        accounts, records, sha = cohort(repo)
    fin = net.rpc("eth_getBlockByNumber", ["finalized", False], urls=[provider], timeout=30)
    plan = {"made_utc": utc_now(), "provider": provider, "start_block": START_BLOCK,
            "end_block": int(fin["number"], 16), "end_block_hash": fin["hash"],
            "end_block_time_utc": datetime.fromtimestamp(int(fin["timestamp"], 16), timezone.utc).isoformat(),
            "cohort_source": "explicit --accounts" if explicit else COHORT_CSV, "cohort_records": records,
            "cohort_csv_sha256": sha,
            "accounts": accounts, "chunk_size": CHUNK, "split_at": SPLIT_AT}
    (out / "plan.json").write_text(json.dumps(plan, indent=1))
    return plan


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--accounts", help="comma-separated accounts (regression cohort) instead of pm_traders.csv")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    pp = a.out / "plan.json"
    plan = json.loads(pp.read_text()) if pp.exists() else make_plan(REPO, a.out, TENDERLY, a.accounts)
    if a.accounts and sorted({x.strip().lower() for x in a.accounts.split(",") if x.strip()}) != plan["accounts"]:
        raise SystemExit("--accounts differs from the existing plan.json in --out: use another folder")
    accts = plan["accounts"]
    chunks = [accts[i:i + plan["chunk_size"]] for i in range(0, len(accts), plan["chunk_size"])]
    lock = threading.Lock()
    logf = (a.out / "run.log").open("a")

    def log(msg):
        logf.write(f"{utc_now()} {msg}\n")
        logf.flush()

    log(f"start end_block={plan['end_block']} accounts={len(accts)} chunks={len(chunks)}")
    jobs = [(name, f"c{i}", flt) for i, ch in enumerate(chunks) for name, flt in filters(ch).items()]
    with ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(run_stream, a.out, plan, n, c, f, lock, log): (n, c) for n, c, f in jobs}
        failed = []
        for fu, (n, c) in futs.items():
            try:
                log(f"done {n}/{c} calls={fu.result()}")
            except Exception as e:  # recorded, never read as an empty stream
                failed.append(f"{n}/{c}")
                log(f"FAILED {n}/{c}: {e!r}")
    log(f"end failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
