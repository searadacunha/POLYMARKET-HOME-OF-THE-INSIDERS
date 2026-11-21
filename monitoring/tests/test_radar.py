"""Offline tests of the radar layer, on alerts produced by phi_engine itself (the scenarios of test_engine.py).
    cd monitoring && python3 -m unittest tests.test_radar -v"""
import hashlib, json, os, sys, tempfile, threading, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import test_engine as T                                    # noqa: E402  (its fake network and scenarios, unchanged)
from phi_engine import enrich, feed, store                 # noqa: E402
from radar import __main__ as cli, chain, dashboard, evaluate, notify, record   # noqa: E402

REQUIRED = ("id", "trigger_utc", "emitted_at_utc", "sealed_at_utc", "market", "wallets", "cluster", "transactions", "sources",
            "information_at_trigger", "risk", "controls", "uncertainty", "data_latency", "detector", "price_and_depth", "evidence_status")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def engine_alerts(case):
    """Real engine alerts (C1, C6, C7, R1) written to <db>.alerts.jsonl the way the engine writes them."""
    con, path = T.db(case); e = T.Evaluation.setup(case, con, T.W1, T.T0)
    rows = {T.W1: [[T.T0 - 100, "D", None, None, 40000.0, None, None, "0xdep1"], [T.T0, "T", T.COND, "BUY", 2000.0, 0.06, 0, None],
                   [T.T0 + 60, "T", T.COND, "BUY", 5000.0, 0.10, 0, None], [T.T0 + 300, "T", T.COND, "BUY", 4000.0, 0.30, 0, None]]}
    rpc = T.chain_rpc({"0xdep1": T.swap_receipt(T.W1, 39_991_000_000, 900)},
                      [(T.W1, T.FUNDER, 40_000_000_000, 880, "0xfund1"), (T.W1, T.POOL, 39_991_000_000, 900, "0xdep1")])
    alerts, _ = enrich.evaluate(con, e, rpc=rpc, get_json=T.activity(rows), now=lambda: T.T0 + 400)
    for b in alerts:
        store.append_alert_file(path, b)
    return path, alerts


def group_alert(case):
    """The engine's own C4 scenario (test_engine: second wallet of the same key)."""
    con, path = T.db(case)
    rows = lambda t: [[t - 100, "D", None, None, 5000.0, None, None, f"0xdep{t}"], [t, "T", T.COND, "BUY", 3000.0, 0.2, 0, None]]
    rec = lambda w, t: {f"0xdep{t}": T.swap_receipt(w, 4_990_000_000, 900 + t - T.T0)}
    e1 = T.Evaluation.setup(case, con, T.W1, T.T0, cash=3000.0, price=0.2)
    enrich.evaluate(con, e1, rpc=T.chain_rpc(rec(T.W1, T.T0), [(T.W1, T.FUNDER, 5_000_000_000, 890, "0xf1")]), get_json=T.activity({T.W1: rows(T.T0)}),
                    now=lambda: T.T0 + 50)
    t2 = T.T0 + 3600
    con.execute("insert into fills values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("0xentry2", 2, 600, t2, "0xe111180000d2663c0091e4f400237545b87b996b", T.W2, "0x0",
                                                                     T.TOK_YES, "BUY", 15000.0, 3000.0, 0.0, 0.2, t2 + 6.0)); con.commit()
    feed.open_entries(con, 1, get_json=T.gamma())
    e2 = dict(con.execute("select * from entries where wallet=?", (T.W2,)).fetchone())
    a2, _ = enrich.evaluate(con, e2, rpc=T.chain_rpc(rec(T.W2, t2), [(T.W2, T.FUNDER, 5_000_000_000, 4480, "0xf2")]), get_json=T.activity({T.W2: rows(t2)}),
                            now=lambda: t2 + 50)
    return {x["class"]: x for x in a2}["C4_COFUNDED_GROUP"]


class Seal(unittest.TestCase):
    def setUp(self):
        self.db, self.alerts = engine_alerts(self)
        self.out = tempfile.mkdtemp()

    def test_every_required_field_is_present_and_nothing_is_invented(self):
        recs = cli.seal(self.db, self.out, now=lambda: T.T0 + 500, env={})
        self.assertEqual(len(recs), len(self.alerts))
        for r in recs:
            for k in REQUIRED:
                self.assertIn(k, r)
            self.assertEqual(r["kind"], "ANOMALY")
            self.assertEqual(r["price_and_depth"]["depth"], record.DATA_UNAVAILABLE)          # no book was given: never a made-up depth
            self.assertEqual(r["information_at_trigger"]["inputs"]["first_public_information"], record.DATA_UNAVAILABLE)
            self.assertTrue({c["level"] for c in r["evidence_status"]} <= set(record.LEVELS))
            self.assertEqual(next(c for c in r["evidence_status"] if "private information" in c["claim"])["level"], "HYPOTHESIS")
            self.assertRegex(r["detector"]["engine"]["code_sha256"], "^[0-9a-f]{64}$")
            self.assertRegex(r["detector"]["radar"]["radar_code_sha256"], "^[0-9a-f]{64}$")
            self.assertEqual(r["emitted_t"], T.T0 + 400)                                       # trigger fill time + the engine's delay
            self.assertNotIn("win", json.dumps(r))                                            # no outcome can be in a sealed record
        by = {r["risk"]["class"]: r for r in recs}
        self.assertEqual(by["C7_HEAVY_NEWCOMER"]["controls"]["same_class_alerts_last_24h"], 0)
        self.assertEqual(by["C1_FRESH_FUNDED_BET"]["transactions"]["fills"][0]["block"], 500)

    def test_sealing_twice_adds_nothing_and_any_edit_is_found(self):
        cli.seal(self.db, self.out, env={}); cli.seal(self.db, self.out, env={})
        alerts_path, _ = cli.paths(self.out)
        n, _, errors = chain.verify(alerts_path)
        self.assertEqual((n, errors), (len(self.alerts), []))
        v = cli.verify(self.out, self.db)
        self.assertEqual((v["records_without_engine_line"], v["records_differing_from_engine_line"], v["records_sealed_twice"],
                          v["engine_lines_not_sealed"]), ([], [], [], 0))
        chain.anchor(alerts_path)
        with open(alerts_path, "rb") as f:
            data = f.read()
        last = data.rstrip(b"\n").rsplit(b"\n", 1)[-1]
        with open(alerts_path, "wb") as f:                                                     # the LAST line: only an anchor can see it
            f.write(data.replace(last, last.replace(b'"ANOMALY"', b'"PROOF__"')))
        self.assertTrue(chain.verify(alerts_path)[2])
        with open(alerts_path, "wb") as f:                                                     # dropped tail
            f.write(b"\n".join(data.split(b"\n")[:2]) + b"\n")
        self.assertTrue(chain.verify(alerts_path)[2])
        with open(alerts_path, "wb") as f:                                                     # a blank line inserted
            f.write(data.replace(b"\n", b"\n\n", 1))
        self.assertTrue(chain.verify(alerts_path)[2])

    def test_two_sealers_at_once_never_seal_a_line_twice(self):
        go = threading.Barrier(4)
        def one():
            go.wait(); cli.seal(self.db, self.out, env={})
        ts = [threading.Thread(target=one) for _ in range(4)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        self.assertEqual(cli.verify(self.out, self.db)["records_sealed_twice"], [])
        self.assertEqual(chain.verify(cli.paths(self.out)[0])[0], len(self.alerts))

    def test_a_line_being_written_waits_and_a_broken_engine_file_is_refused(self):
        with open(self.db + ".alerts.jsonl", "ab") as f:
            f.write(b'{"id": "unfinished"')                                                  # the engine is writing
        self.assertEqual(len(cli.seal(self.db, self.out, env={})), len(self.alerts))
        with open(self.db + ".alerts.jsonl", "rb") as f:
            lines = f.read().splitlines()
        with open(self.db + ".alerts.jsonl", "wb") as f:
            f.write(b"\n".join(lines[1:-1]) + b"\n")                                          # first line removed
        with self.assertRaises(SystemExit):
            cli.seal(self.db, self.out, env={})


class Later(unittest.TestCase):
    def market(self, cid=T.COND):
        return [{"conditionId": cid, "outcomes": '["Yes", "No"]', "clobTokenIds": json.dumps([T.TOK_YES, T.TOK_NO]), "closed": True,
                 "umaResolutionStatus": "resolved", "outcomePrices": '["1", "0"]', "closedTime": record.utc(T.T0 + 86400)}]

    def get_json(self, cid=T.COND):
        def g(url):
            if "gamma-api" in url:
                return self.market(cid)
            return {"history": [{"t": T.T0 + k * 600, "p": min(0.98, 0.06 + 0.01 * k)} for k in range(160)]}
        return g

    def test_evaluation_buys_after_the_alert_has_its_own_chain_and_leaves_records_untouched(self):
        db, _ = engine_alerts(self); out = tempfile.mkdtemp()
        cli.seal(db, out, env={})
        alerts_path, evals_path = cli.paths(out)
        before = sha(alerts_path)
        self.assertEqual(cli.run_evaluate(out, self.get_json(), now=lambda: T.T0 + 2 * 86400), 4)
        self.assertEqual(sha(alerts_path), before)
        ev = {e["class"]: e for _, e in chain.read(evals_path)}
        c1 = ev["C1_FRESH_FUNDED_BET"]
        self.assertEqual((c1["status"], c1["outcome_won"], c1["entry"]["kind"]), ("FINAL", True, "PRICE_HISTORY_DEPTH_UNKNOWN"))
        self.assertEqual(c1["entry"]["t"], T.T0 + 600); self.assertAlmostEqual(c1["entry"]["price"], 0.07)   # first print after the alert
        self.assertEqual(c1["trigger_fill_price"], 0.06)
        self.assertAlmostEqual(c1["shadow"]["net_return_per_usd"], 1 / 0.07 - 1, places=5)
        self.assertEqual(cli.run_evaluate(out, self.get_json(), now=lambda: T.T0 + 3 * 86400), 0)   # final: not asked again
        self.assertEqual(chain.verify(evals_path)[2], [])

    def test_another_market_is_never_scored_and_an_unchanged_answer_is_not_rewritten(self):
        db, _ = engine_alerts(self); out = tempfile.mkdtemp(); cli.seal(db, out, env={})
        self.assertEqual(cli.run_evaluate(out, self.get_json(cid="0xother"), now=lambda: T.T0 + 2 * 86400), 4)
        self.assertEqual({e["status"] for _, e in chain.read(cli.paths(out)[1])}, {"DATA_UNAVAILABLE"})
        self.assertEqual(cli.run_evaluate(out, self.get_json(cid="0xother"), now=lambda: T.T0 + 2 * 86400 + 60), 0)

    def test_nothing_is_evaluated_before_its_first_horizon_and_final_needs_every_horizon(self):
        db, _ = engine_alerts(self); out = tempfile.mkdtemp(); cli.seal(db, out, env={})
        self.assertEqual(cli.run_evaluate(out, lambda url: self.fail(url), now=lambda: T.T0 + 10), 0)
        rec = next(o for _, o in chain.read(cli.paths(out)[0]))
        e = evaluate.evaluate(rec, self.get_json(), T.T0 + 8 * 3600)
        self.assertEqual((e["status"], e["printed_price_after_emission"]["24h"]), ("PARTIAL", "NOT_YET"))

    def test_sparse_history_cannot_fill_earlier_marks_or_use_a_future_point(self):
        rec = {"id": "r", "emitted_t": T.T0, "market": {"condition_id": T.COND, "outcome": "Yes"},
               "risk": {"class": "C1"}, "price_and_depth": {"price_at_alert": 0.2, "depth": {"asks": []}}}
        urls = []
        def source(url):
            urls.append(url)
            return self.market() if "gamma-api" in url else {"history": [{"t": T.T0 + 86400, "p": 0.9}]}
        early = evaluate.evaluate(rec, source, T.T0 + 3600)
        self.assertIn(f"endTs={T.T0 + 3600}", urls[-1])
        self.assertIsNone(early["entry"]["t"])
        self.assertIsNone(early["horizon_observations"]["1h"])
        self.assertIsNone(early["outcome_won"])
        mature = evaluate.evaluate(rec, source, T.T0 + 2 * 86400)
        self.assertEqual(mature["status"], "PARTIAL")
        self.assertEqual(mature["horizon_observations"]["24h"], {"t": T.T0 + 86400, "price": 0.9, "delay_s": 0})
        self.assertEqual(mature["entry"]["kind"], "DATA_UNAVAILABLE")
        self.assertIsNone(mature["shadow"]["net_return_per_usd"])

    def test_boundary_duplicate_and_conflicting_prices(self):
        h = evaluate.PriceHistory([(601, 0.4), (600, 0.3), (600, 0.3), (9000, 0.2), (9000, 0.8)])
        self.assertEqual(h.first(0, 600)["delay_s"], 600)
        self.assertIsNone(h.first(-1, 1000))
        self.assertIsNone(h.first(0, 599))
        self.assertIsNone(h.first(9000, 9600))
        with self.assertRaises(ValueError):
            evaluate.PriceHistory([(1, float("nan"))])

    def test_v2_uses_position_id_and_chart_never_confirms_book_execution(self):
        rec = {"id": "r", "emitted_t": T.T0, "market": {"condition_id": T.COND, "outcome": "No"},
               "risk": {"class": "C1"}, "price_and_depth": {"depth": {"some_depth": 30}}}
        market = dict(self.market()[0], version="v2", positionIds=["17", "18"], clobTokenIds=None)
        def source(url):
            if "gamma-api" in url:
                return [market]
            self.assertIn("market=18&", url)
            return {"history": [{"t": T.T0, "p": 0.4}]}
        result = evaluate.evaluate(rec, source, T.T0 + 3600)
        self.assertEqual(result["entry"]["kind"], "PRICE_HISTORY_DEPTH_UNKNOWN")
        self.assertIsNone(result["outcome_won"])
        market["positionIds"] = ["17", "17"]
        self.assertEqual(evaluate.evaluate(rec, source, T.T0 + 3600)["status"], "DATA_UNAVAILABLE")

    def test_old_final_is_corrected_once_without_changing_old_chain_bytes(self):
        db, _ = engine_alerts(self)
        with tempfile.TemporaryDirectory() as out:
            cli.seal(db, out, env={})
            alerts_path, evals_path = cli.paths(out)
            rec = chain.read(alerts_path)[0][1]
            chain.append(evals_path, {"alert": rec["id"], "status": "FINAL"})
            old = chain.read(evals_path)[0][0]
            def run():
                return cli.run_evaluate(out, self.get_json(), now=lambda: T.T0 + 2 * 86400)
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(2) as pool:
                counts = list(pool.map(lambda _: run(), range(2)))
            self.assertEqual(sum(counts), 4)
            self.assertEqual(chain.read(evals_path)[0][0], old)
            self.assertEqual(chain.verify(evals_path)[2], [])
            self.assertTrue(all(e["evaluation_version"] == evaluate.VERSION for e in cli.latest_evaluations(evals_path)))
            self.assertEqual(run(), 0)

    def test_resolution_and_fee_conventions(self):
        m = self.market()[0]
        self.assertEqual(evaluate.resolution(m, 0), (True, "uma"))
        self.assertEqual(evaluate.resolution(dict(m, umaResolutionStatus="proposed"), 0)[0], None)
        self.assertEqual(evaluate.resolution(dict(m, outcomePrices='["0.6", "0.4"]'), 0)[0], None)
        self.assertIsNone(evaluate.resolution(dict(m, umaResolutionStatus=None, outcomePrices=[0.995, 0.005]), 0)[0])
        self.assertIsNone(evaluate.resolution(dict(m, outcomePrices=[1]), 1)[0])
        self.assertEqual(evaluate.shadow(0.5, True, 0.02), 0.96)                              # all-in: (1 - 0.02) / 0.5 - 1
        self.assertEqual(evaluate.shadow(0.5, False, 0.02), -1.0)
        self.assertEqual(evaluate.as_list(["Yes", "No"]), evaluate.as_list('["Yes", "No"]'))


class Page(unittest.TestCase):
    def test_market_text_cannot_end_the_script_or_open_a_comment(self):
        rec = {"id": "x", "trigger_utc": "2030-01-01", "market": {"question": "Who wins? <!--<script></script><img src=x onerror=alert(1)>", "outcome": "Yes"},
               "risk": {"class": "C1"}, "price_and_depth": {"price_at_alert": float("nan")}, "controls": {"out_of_sample": {}}, "wallets": [], "cluster": None}
        html = dashboard.render([rec], [])
        data = html.split('<script id="data" type="application/json">')[1].split("</script>")[0]
        self.assertFalse(set(data) & set("<>&"))                                              # nothing the HTML parser could act on
        self.assertEqual(html.count("</script>"), 2)
        self.assertIn("null", data)                                                           # NaN written as null, the page still parses


class Group(unittest.TestCase):
    def test_a_real_group_alert_keeps_both_wallets_and_the_controller_stays_a_hypothesis(self):
        a = group_alert(self)
        r = record.build(a, "0" * 64, 0)
        self.assertEqual((r["cluster"]["key"], sorted(r["wallets"])), (T.FUNDER, sorted([T.W1, T.W2])))
        self.assertEqual(sorted(r["cluster"]["members_known_at_trigger"]), sorted([T.W1, T.W2]))
        levels = {c["claim"]: c["level"] for c in r["evidence_status"]}
        self.assertEqual(levels["the linked wallets have one controller"], "HYPOTHESIS")
        self.assertEqual(levels["the linked wallets were funded by the same plain key"], "SUPPORTED")

    def test_an_older_alert_with_missing_parts_is_sealed_with_unknowns_not_guesses(self):
        r = record.build({"id": "x", "class": "C4_COFUNDED_GROUP", "wallets": {"wallet": "0xa", "linked_wallet": "0xb"}}, "0" * 64, 0)
        self.assertEqual((r["information_at_trigger"]["inputs"]["wallet_history"], r["cluster"], r["wallets"]), (record.DATA_UNAVAILABLE, None, ["0xa"]))


class Notify(unittest.TestCase):
    rec = {"id": "r", "risk": {"class": "C1"}, "trigger_utc": "t", "market": {"question": "q", "outcome": "Yes"},
           "price_and_depth": {"price_at_alert": 0.1}, "controls": {"out_of_sample": {"study_verdict": "NOT_SUPPORTED"}}}

    def test_off_without_configuration_https_only_and_a_failure_never_raises(self):
        self.assertEqual(notify.send(self.rec, env={}), [])
        self.assertEqual(notify.send(self.rec, env={"RADAR_WEBHOOK_URL": "http://example.invalid/h"}), [])
        def boom(url, body):
            raise OSError("down")
        self.assertEqual(notify.send(self.rec, env={"RADAR_WEBHOOK_URL": "https://example.invalid/h"}, post=boom), [("webhook", "OSError")])
        self.assertIn("not a finding about a person", notify.text(self.rec))

    def test_an_old_backlog_is_not_notified(self):
        db, _ = engine_alerts(self); out = tempfile.mkdtemp(); sent = []
        env = {"RADAR_WEBHOOK_URL": "https://example.invalid/h"}
        orig = notify.send
        notify.send = lambda rec, env=None, post=None: sent.append(rec["id"]) or []
        try:
            cli.seal(db, out, now=lambda: T.T0 + 10 * 86400, env=env)
        finally:
            notify.send = orig
        self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
