"""Download public taker trades. Period filters on a condition query are not trusted.

A market is complete only when the cursor is exhausted. A capped walk is
incomplete and must not be read as a negative detector result.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PAGE = 1000
PAGE_CAP = 3


def _get(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "research-client/1.0", "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 3:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise
    raise RuntimeError(url)


def pull_market(condition: str) -> dict:
    """Return compact taker rows. `taker_only` is left at the API default, true."""
    cursor = None
    rows = []
    seen = set()
    complete = False
    pages = 0
    for _ in range(PAGE_CAP):
        url = f"https://data-api.polymarket.com/v2/trades?condition={condition}&limit={PAGE}"
        if cursor:
            url += "&cursor=" + urllib.parse.quote(str(cursor))
        payload = _get(url)
        pages += 1
        data = payload.get("data") or []
        for row in data:
            wallet = str(row.get("proxy_wallet") or "").lower()
            key = (
                str(row.get("transaction_hash") or ""), wallet, row.get("side"),
                row.get("outcome"), row.get("size"), row.get("price"), row.get("timestamp"),
            )
            if key in seen or not wallet.startswith("0x"):
                continue
            seen.add(key)
            rows.append({
                "t": int(row["timestamp"]),
                "w": wallet,
                "side": row.get("side"),
                "outcome": row.get("outcome"),
                "size": float(row.get("size") or 0),
                "price": float(row.get("price") or 0),
                "tx": str(row.get("transaction_hash") or ""),
            })
        pagination = payload.get("pagination") or {}
        if not pagination.get("has_more"):
            complete = True
            break
        cursor = pagination.get("next_cursor")
        if not cursor:
            complete = True
            break
        time.sleep(0.1)
    return {"rows": rows, "complete": complete, "pages": pages}


def main(jobs_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    done = {path.stem for path in out_dir.glob("*.json")}
    jobs = json.loads(jobs_path.read_text())
    for index, job in enumerate(jobs):
        condition = job["condition_id"]
        if condition in done:
            continue
        try:
            pulled = pull_market(condition)
            error = None
        except Exception as exc:
            pulled = {"rows": [], "complete": False, "pages": 0}
            error = type(exc).__name__
        body = {**job, "n": len(pulled["rows"]), "complete": pulled["complete"], "pages": pulled["pages"], "error": error, "rows": pulled["rows"]}
        (out_dir / f"{condition}.json").write_text(json.dumps(body))
        if index % 10 == 0:
            print(index, condition[:12], body["n"], body["complete"], flush=True)
        time.sleep(0.08)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    main(Path("/tmp/trade_jobs.json"), root / ".local" / "trades")
