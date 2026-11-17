"""col_40: history of each ignition's initiator AS OF its first buy (activity strictly before t_first, at most 500 rows).
The `end` filter is asserted on every answer: a row at or after t_first raises. Errors are stored as errors. Resumable."""
import datetime as dt, json, os, sqlite3, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ETUDE, "data", "baselines.sqlite")
LIMIT = 500
WORKERS = 3


def act(user, **p):
    q = "&".join(f"{k}={v}" for k, v in p.items())
    j, _ = net.get_json(f"https://data-api.polymarket.com/v2/activity?user={user}&{q}", tag="baseline", archive=False, pause=0.1, timeout=60)
    if not isinstance(j.get("data"), list): raise RuntimeError(f"unexpected activity schema for {user}")
    return j["data"], (j.get("pagination") or {})


def one(key):
    wallet, t_first = key
    try:
        s, b, _ = net.fetch(f"https://gamma-api.polymarket.com/public-profile?address={wallet}", tag="profile", archive=False, pause=0.1)
        if s == 200:
            c = json.loads(b).get("createdAt")
            created = dt.datetime.fromisoformat(c.replace("Z", "+00:00")).timestamp() if c else None
        elif s == 404: created = None
        else: raise RuntimeError(f"profile HTTP {s}")
        first, _ = act(wallet, limit=1, sort_by="TIMESTAMP", sort_direction="ASC", exclude_deposits_withdrawals="false")
        prior, pg = act(wallet, limit=LIMIT, sort_by="TIMESTAMP", sort_direction="DESC", exclude_deposits_withdrawals="false", end=t_first - 1)
        if any(int(r["timestamp"]) >= t_first for r in prior): raise RuntimeError("end filter not honoured")
        tr = [r for r in prior if r.get("type") == "TRADE"]
        cash = [float(r.get("usdc_size") or 0) for r in tr]
        dep = [float(r.get("usdc_size") or 0) for r in prior if r.get("type") == "DEPOSIT" and int(r["timestamp"]) >= t_first - 72 * 3600]
        out = {"profile_created": created, "first_activity": int(first[0]["timestamp"]) if first else None,
               "prior_rows": len(prior), "prior_rows_capped": bool(pg.get("has_more")), "prior_trades": len(tr),
               "prior_markets": len({r.get("condition_id") for r in tr}), "prior_trade_cash": round(sum(cash), 2),
               "prior_trade_median": round(statistics.median(cash), 4) if cash else None,
               "deposit_72h_usdc": round(sum(dep), 2), "deposit_72h_n": len(dep)}
        return wallet, t_first, "ok", json.dumps(out)
    except Exception as e:  # stored as an error row: the ignition is then excluded and counted, never scored as "thin"
        return wallet, t_first, "error", json.dumps({"error": repr(e)[:300]})


def main():
    con = sqlite3.connect(DB)
    con.execute("create table if not exists baseline(wallet text, t_first integer, status text, body text, primary key(wallet, t_first))")
    done = {(r[0], r[1]) for r in con.execute("select wallet, t_first from baseline where status='ok'")}
    keys = sorted({(g["initiator"], g["t_first"]) for g in map(json.loads, open(os.path.join(ETUDE, "derived", "ignitions_features.jsonl")))})
    todo = [k for k in keys if k not in done]
    print("initiator baselines:", len(keys), "todo:", len(todo), flush=True)
    n = 0; t0 = time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        for row in ex.map(one, todo):
            con.execute("insert or replace into baseline values(?,?,?,?)", row); n += 1
            if n % 100 == 0:
                con.commit(); print(time.strftime("%H:%M:%S"), n, "/", len(todo), f"{n / (time.time() - t0):.2f}/s", net.COUNTS, flush=True)
    con.commit()
    c = dict(con.execute("select status, count(*) from baseline group by status").fetchall())
    print("DONE", c, net.COUNTS, flush=True)
    json.dump({"by_status": c, "http_this_run": net.COUNTS}, open(os.path.join(ETUDE, "data", "col_40_counts.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
