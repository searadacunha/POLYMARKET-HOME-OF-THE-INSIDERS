"""Detection. `evaluate` is a pure function of the local store and of a time `as_of`: it reads only price points and tape
rows dated at or before `as_of`, and a wallet history dated before the first buy. Replaying the same store gives the same
alerts, which is how a live alert is checked afterwards.

An alert says that a trade pattern was seen. It never says who the trader is, nor that the trader knew anything."""
import hashlib, json, time
from . import collect, ignition, store, tapefeat

LEVELS = {(True, True): "LONELY_THIN", (True, False): "LONELY", (False, True): "THIN"}
COMPETING = ["a public report, post or broadcast that this monitor does not read", "a large trader moving to a new account",
             "a punt on a cheap outcome that happens to move a thin book", "an attempt to move the price itself",
             "a hedge of a position held elsewhere"]


def evaluate(con, condition_id, side, as_of, lookback=14 * 86400):
    """Return ("alert", body) | ("pending", reason) | ("none", reason) for one side of one market, as of a time."""
    m = con.execute("select * from markets where condition_id=?", (condition_id,)).fetchone()
    if m is None:
        return "none", "unknown_market"
    series = [(r[0], r[1]) for r in con.execute("select ts, price from prices where token_id=? and ts between ? and ? order by ts",
                                                (m["yes_token"], as_of - lookback, as_of))]
    ig = ignition.first_ignition(series, side)
    if ig is None:
        return "none", "no_ignition"
    rows = [r for r in store.tape(con, condition_id, ig["t0"] - tapefeat.PRE - 60, as_of)]
    if not rows:
        return "pending", "no_tape"
    probe, why = tapefeat.alert_features(rows, side, ig["base"], ig["t0"], ig["t1"])
    if probe is None:                                     # the first 15 minutes may still be filling: not a final answer yet
        return ("pending" if as_of < ig["t1"] + tapefeat.W_LONELY else "none"), why
    if as_of < probe["t_alert"]:
        return "pending", "before_alert_time"
    b = con.execute("select body from baselines where wallet=? and as_of=?", (probe["initiator"], probe["t_first"])).fetchone()
    if b is None:
        return "pending", "no_baseline:" + probe["initiator"] + ":" + str(probe["t_first"])
    base = json.loads(b[0])
    cls = tapefeat.classify(probe, base["prior_markets"])
    level = LEVELS.get((cls["lonely"], cls["thin"]))
    if level is None:
        return "none", "broad_ignition_by_established_account"
    tok = m["yes_token"] if side == "YES" else m["no_token"]
    ev = [r[0] for r in con.execute("select tx from fills where wallet=? and token_id=? and side='BUY' and ts between ? and ? order by ts limit 5",
                                    (probe["initiator"], tok, probe["t_first"], probe["t_alert"]))]
    fund = [dict(r) for r in con.execute("select tx, ts, payer, payer_kind, payer_nonce, amount from funding where proxy=? and ts between ? and ? order by ts",
                                         (probe["initiator"], probe["t_first"] - 72 * 3600, probe["t_first"]))]
    age = None if base["first_activity"] is None else round((probe["t_first"] - base["first_activity"]) / 3600, 2)
    reasons = [f"price of {side} went from a 6-hour median of {ig['base']:.3f} to {ig['x_t1']:.3f} at the 10-minute point of {_utc(ig['t1'])}",
               f"one account supplied {probe['share15']:.0%} of the {probe['total15']:,.0f} USD bought in the first 15 minutes "
               f"({probe['n_buyers15']} buyers of 20 USD or more)",
               f"that account had traded {base['prior_markets']} market(s) before" + (f"; its first activity was {age} h earlier" if age is not None else ""),
               f"it kept buying from {probe['initiator_first_price']:.3f} up to {probe['initiator_max_price']:.3f} "
               f"({probe['initiator_cash']:,.0f} USD by the alert time)"]
    if fund:
        reasons.append("deposits in the 72 h before: " + "; ".join(f"{x['amount']:,.0f} from {x['payer']} ({x['payer_kind']}, {x['payer_nonce']} txs)" for x in fund[:4]))
    body = {"id": hashlib.sha256(f"{condition_id}|{side}|{probe['t_first']}|{probe['initiator']}".encode()).hexdigest()[:16],
            "level": level, "condition_id": condition_id, "event_slug": m["event_slug"], "title": m["title"], "side": side,
            "t_first": probe["t_first"], "t_alert": probe["t_alert"], "t_first_utc": _utc(probe["t_first"]), "t_alert_utc": _utc(probe["t_alert"]),
            "p_alert": probe["p_alert"], "ignition": ig, "features": probe, "initiator_history": base, "classes": cls,
            "funding": fund, "cluster": _cluster(con, m["event_slug"], probe["initiator"], fund, as_of),
            "reasons": reasons, "evidence_tx": ev, "competing_explanations": COMPETING,
            "reading": "pattern seen in public data; says nothing about identity or about private information"}
    return "alert", body


def _roots(con, wallet, as_of):
    """Plain keys that paid `wallet` by `as_of`, directly or through a brand-new key. Contracts, mints and high-volume
    keys are services used by many people and are never roots."""
    rows = con.execute("select payer, payer_kind, payer_nonce, ts from funding where proxy=? and ts<=?", (wallet, as_of)).fetchall()
    roots = {p for p, kind, _n, _t in rows if kind == "key"}
    for p, kind, nonce, ts in rows:
        if kind == "key" and nonce <= collect.PASS_THROUGH_NONCE:
            roots |= {q for q, k in con.execute("select payer, payer_kind from funding where proxy=? and ts<=?", (p, ts)) if k == "key"}
    return roots


def clusters(con, event_slug, as_of):
    """Groups of two or more wallets of one event that share a plain-key payer, as known at `as_of`."""
    wallets = [r[0] for r in con.execute(
        "select distinct fu.proxy from funding fu where fu.ts<=? and exists (select 1 from fills f join tokens t on t.token_id=f.token_id "
        "join markets m on m.condition_id=t.condition_id where f.wallet=fu.proxy and m.event_slug=? and f.ts<=?)", (as_of, event_slug, as_of))]
    by = {}
    for w in wallets:
        for root in _roots(con, w, as_of):
            by.setdefault(root, set()).add(w)
    return [{"shared_payer": root, "wallets": sorted(ws)} for root, ws in sorted(by.items()) if len(ws) >= 2]


def _cluster(con, event_slug, initiator, fund, as_of):
    """Other wallets of the same event that share a plain-key payer with the initiator before `as_of`."""
    return [{"wallet": w, "shared_payer": g["shared_payer"]} for g in clusters(con, event_slug, as_of) if initiator in g["wallets"]
            for w in g["wallets"] if w != initiator]


def _utc(t):
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t))


def record(con, body):
    """Store an alert once and journal it. Returns True when it is new."""
    with con:
        cur = con.execute("insert or ignore into alerts values(?,?,?,?,?,?,?)", (body["id"], body["t_alert"], time.time(), body["condition_id"],
                                                                                body["side"], body["level"], json.dumps(body, sort_keys=True)))
        if cur.rowcount:
            store.journal(con, "alert", {"id": body["id"], "level": body["level"], "condition_id": body["condition_id"], "side": body["side"],
                                         "t_alert": body["t_alert"], "initiator": body["features"]["initiator"], "evidence_tx": body["evidence_tx"]})
    return bool(cur.rowcount)


def scan(con, now=None, budget=20):
    """Work on open candidates: resolve the market, read its price series and tape, then evaluate as of `now`.
    Network reads happen here; `evaluate` itself never touches the network. Returns the list of new alerts."""
    now = int(now or time.time()); new = []
    cands = con.execute("select condition_id, side, first_seen from candidates where state in ('new','pending') order by first_seen limit ?", (budget,)).fetchall()
    for (body,) in con.execute("select body from alerts where t_alert > ? order by t_alert desc limit 3", (now - 86400,)).fetchall():
        try:                                                # alerts of the last 24 h: refresh the tape, look for a cluster
            a = json.loads(body)
            collect.fetch_tape(con, a["condition_id"], a["ignition"]["t0"] - tapefeat.PRE - 60, fresh=True)
            record_cluster(con, a, followup(con, a, now, max_wallets=3), now)
        except collect.net.SourceError:
            pass                                            # retried at the next pass
    for key, side, first_seen in cands:
        try:
            if key.startswith("token:"):
                m = collect.resolve(con, key[6:])
                if m is None or set(json.loads(m["tags"])) & collect.EXCLUDED_TAGS:
                    _state(con, key, side, "excluded", "not a Yes/No market, unknown to Gamma, or excluded tag"); continue
                with con:                                   # from now on the candidate is the bought side of that market
                    con.execute("delete from candidates where condition_id=? and side=?", (key, side))
                    con.execute("insert or ignore into candidates values(?,?,?,?,?)",
                                (m["condition_id"], "YES" if key[6:] == m["yes_token"] else "NO", first_seen, "pending", ""))
                continue
            m = con.execute("select * from markets where condition_id=?", (key,)).fetchone()
            last = con.execute("select max(ts) from prices where token_id=?", (m["yes_token"],)).fetchone()[0] or 0
            # 14 days once, as the study read them, then only what is new: a shorter history truncates the six-hour base of its oldest points
            collect.fetch_prices(con, m["yes_token"], max(last - 3600, now - 14 * 86400), now)
            status, info = evaluate(con, key, side, now)
            if status == "pending" and info == "no_tape" or status == "none" and info == "no_ignition":
                ig = ignition.first_ignition([(r[0], r[1]) for r in con.execute("select ts, price from prices where token_id=? and ts<=? order by ts", (m["yes_token"], now))], side)
                if ig is not None:
                    if not collect.fetch_tape(con, key, ig["t0"] - tapefeat.PRE - 60, fresh=True)["complete"]:
                        _state(con, key, side, "too_deep", "tape needs more than 300 pages"); continue
                    status, info = evaluate(con, key, side, now)
            if status == "pending" and info.startswith("no_baseline:"):
                _, wallet, t_first = info.split(":")
                _history(con, wallet, int(t_first))
                status, info = evaluate(con, key, side, now)
            if status == "alert":
                if record(con, info):
                    new.append(info)
                _state(con, key, side, "alerted", info["id"])
            elif status == "none" and info != "no_ignition":
                _state(con, key, side, "closed", info)
            elif now - first_seen > 2 * 3600:
                _state(con, key, side, "expired", str(info))
            else:
                _state(con, key, side, "pending", str(info))
        except collect.net.SourceError as e:              # a failed source leaves the candidate open and visible
            _state(con, key, side, "pending", "source error: " + str(e)[:150])
    return new


def _history(con, wallet, t_first):
    """As-of history and funding of one wallet (network). Funding is read from the wallet's first activity, 72 h back at most."""
    base = collect.baseline(con, wallet, t_first)
    start = max(t_first - 72 * 3600, (base["first_activity"] or t_first) - 2 * 3600)
    collect.funding(con, wallet, start, t_first)
    return base


FOLLOW_MIN_CASH = 1000.0     # other buyers are examined from this amount bought on the alerted side


def followup(con, alert, as_of, max_wallets=8):
    """After an alert: look at the other wallets that bought the same side for FOLLOW_MIN_CASH or more by `as_of`.
    A wallet with almost no history gets its funding read; the cluster is every such wallet paid by the same plain key as
    the initiator. Uses rows dated at or before `as_of` only; each wallet is read once, as of its own first buy (network)."""
    m = con.execute("select * from markets where condition_id=?", (alert["condition_id"],)).fetchone()
    tok = m["yes_token"] if alert["side"] == "YES" else m["no_token"]
    who = alert["features"]["initiator"]
    buyers = con.execute("select wallet, min(ts), sum(cash) from fills where token_id=? and side='BUY' and ts between ? and ? and wallet != ? "
                         "group by wallet having sum(cash) >= ? order by min(ts)", (tok, alert["t_first"], as_of, who, FOLLOW_MIN_CASH)).fetchall()
    read = 0
    for wallet, first_ts, _cash in buyers:
        known = con.execute("select 1 from baselines where wallet=? and as_of=?", (wallet, first_ts)).fetchone()
        if not known and read >= max_wallets:
            continue                                      # new wallets beyond the budget wait for the next pass
        base = collect.baseline(con, wallet, first_ts); read += not known
        if base["prior_markets"] <= tapefeat.THIN_MARKETS:  # funding is checkpointed: asking again costs nothing
            collect.funding(con, wallet, max(first_ts - 72 * 3600, (base["first_activity"] or first_ts) - 2 * 3600), first_ts)
    return _cluster(con, m["event_slug"], who, alert["funding"], as_of)


def record_cluster(con, alert, members, as_of):
    """Journal a cluster once per new set of members and attach it to the stored alert."""
    known = con.execute("select body from alerts where id=?", (alert["id"],)).fetchone()
    old = json.loads(known[0])["cluster"] if known else []
    if not members or {x["wallet"] for x in members} <= {x["wallet"] for x in old}:
        return False
    with con:
        if known:
            con.execute("update alerts set body=? where id=?", (json.dumps(dict(json.loads(known[0]), cluster=members), sort_keys=True), alert["id"]))
        store.journal(con, "cluster", {"alert": alert["id"], "as_of": as_of, "members": members})
    return True


def backtest(con, condition_id, start, end, step=600):
    """Chronological replay of one stored market: `as_of` advances by `step`; a wallet history is fetched only when the
    replay reaches the point where the live monitor would have asked for it, and only as of that wallet's first buy."""
    out = {}
    for side in ("YES", "NO"):
        t = start - start % step + step; out[side] = {"level": None, "reason": "no_ignition", "as_of": end}
        while t <= end:
            status, info = evaluate(con, condition_id, side, t)
            if status == "pending" and info.startswith("no_baseline:"):
                _, wallet, t_first = info.split(":")
                _history(con, wallet, int(t_first))
                status, info = evaluate(con, condition_id, side, t)
            if status == "alert":
                out[side] = dict(info, as_of=t, cluster_timeline=[], other_groups=[])
                seen, others = set(), {}
                while t <= end:                             # keep replaying: when would a cluster have been seen?
                    members = followup(con, info, t)
                    fresh = [x for x in members if x["wallet"] not in seen]
                    if fresh:
                        seen.update(x["wallet"] for x in fresh)
                        out[side]["cluster_timeline"].append({"as_of": t, "members": len(seen), "new": fresh})
                    for g in clusters(con, info["event_slug"], t):   # groups that do not include the initiator
                        if info["features"]["initiator"] not in g["wallets"] and len(g["wallets"]) > len(others.get(g["shared_payer"], [])):
                            others[g["shared_payer"]] = g["wallets"]
                            out[side]["other_groups"].append(dict(g, as_of=t))
                    t += step
                break
            if status == "none" and info != "no_ignition":
                out[side] = {"level": None, "reason": info, "as_of": t}; break
            t += step
    return out


def _state(con, key, side, state, note):
    with con:
        con.execute("update candidates set state=?, note=? where condition_id=? and side=?", (state, note, key, side))


def replay(con, start=None, end=None, step=600):
    """Deterministic re-evaluation from stored rows only. For each market side with a stored tape, step `as_of` through
    time and return the first alert. Used for backtests and to re-check journaled alerts."""
    out = []
    for m in con.execute("select condition_id from markets order by condition_id").fetchall():
        span = con.execute("select min(f.ts), max(f.ts) from fills f join tokens t on t.token_id=f.token_id where t.condition_id=?", (m[0],)).fetchone()
        if span[0] is None:
            continue
        a, b = (start or span[0]), (end or span[1])
        for side in ("YES", "NO"):
            t = a - a % step + step
            while t <= b + step:
                status, info = evaluate(con, m[0], side, t)
                if status == "alert":
                    out.append(dict(info, replay_as_of=t)); break
                if status == "none" and info not in ("no_ignition",):
                    out.append({"condition_id": m[0], "side": side, "level": None, "replay_as_of": t, "reason": info}); break
                t += step
    return out
