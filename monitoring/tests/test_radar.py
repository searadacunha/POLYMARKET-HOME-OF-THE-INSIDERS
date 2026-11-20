"""Offline tests of the radar layer, on alerts produced by phi_engine itself (the scenario of test_engine.py).
    cd monitoring && python3 -m unittest tests.test_radar -v"""
import hashlib, json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, HERE)
import test_engine as T                                    # noqa: E402  (its fake network and scenario, unchanged)
from phi_engine import enrich, store                       # noqa: E402
from radar import __main__ as cli, chain, dashboard, notify, record   # noqa: E402

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
            self.assertNotIn("win", json.dumps(r))                                            # no outcome can be in a sealed record
        by = {r["risk"]["class"]: r for r in recs}
        self.assertEqual(by["C7_HEAVY_NEWCOMER"]["controls"]["same_class_alerts_last_24h"], 0)
        self.assertEqual(by["C1_FRESH_FUNDED_BET"]["transactions"]["fills"][0]["block"], 500)

    def test_sealing_twice_adds_nothing_and_any_edit_breaks_the_chain(self):
        cli.seal(self.db, self.out, env={}); cli.seal(self.db, self.out, env={})
        alerts_path, _ = cli.paths(self.out)
        n, _, errors = chain.verify(alerts_path)
        self.assertEqual((n, errors), (len(self.alerts), []))
        self.assertEqual(cli.verify(self.out, self.db)["records_without_engine_line"], [])
        with open(alerts_path, "rb") as f:
            data = f.read()
        with open(alerts_path, "wb") as f:
            f.write(data.replace(b'"ANOMALY"', b'"PROOF__"', 1))
        self.assertTrue(chain.verify(alerts_path)[2])                                         # a changed record is detected

    def test_a_broken_engine_file_is_refused(self):
        with open(self.db + ".alerts.jsonl", "rb") as f:
            lines = f.read().splitlines()
        with open(self.db + ".alerts.jsonl", "wb") as f:
            f.write(b"\n".join(lines[1:]) + b"\n")                                           # first line removed
        with self.assertRaises(SystemExit):
            cli.seal(self.db, self.out, env={})


class Later(unittest.TestCase):
    def test_evaluation_has_its_own_chain_and_leaves_records_untouched(self):
        db, _ = engine_alerts(self); out = tempfile.mkdtemp()
        cli.seal(db, out, env={})
        alerts_path, evals_path = cli.paths(out)
        before = sha(alerts_path)

        def get_json(url):
            if "gamma-api" in url:
                return [{"outcomes": '["Yes", "No"]', "clobTokenIds": json.dumps([T.TOK_YES, T.TOK_NO]), "closed": True,
                         "umaResolutionStatus": "resolved", "outcomePrices": '["1", "0"]', "closedTime": "2030-01-02"}]
            return {"history": [{"t": T.T0 + k * 600, "p": 0.06 + 0.01 * k} for k in range(160)]}
        n = cli.run_evaluate(out, get_json, now=lambda: T.T0 + 2 * 86400)
        self.assertEqual(n, 4)
        self.assertEqual(sha(alerts_path), before)
        ev = {e["class"]: e for _, e in chain.read(evals_path)}
        c1 = ev["C1_FRESH_FUNDED_BET"]
        self.assertEqual((c1["status"], c1["outcome_won"], c1["shadow"]["entry"]), ("FINAL", True, "PRINTED_PRICE_DEPTH_UNKNOWN"))
        self.assertAlmostEqual(c1["shadow"]["net_return_per_usd"], 1 / 0.06 - 1, places=5)
        self.assertEqual(cli.run_evaluate(out, get_json, now=lambda: T.T0 + 3 * 86400), 0)   # a final evaluation is not repeated
        self.assertEqual(chain.verify(evals_path)[2], [])

    def test_nothing_is_evaluated_before_its_first_horizon(self):
        db, _ = engine_alerts(self); out = tempfile.mkdtemp(); cli.seal(db, out, env={})
        self.assertEqual(cli.run_evaluate(out, lambda url: self.fail(url), now=lambda: T.T0 + 10), 0)


class Page(unittest.TestCase):
    def test_market_text_cannot_close_the_script_or_inject_html(self):
        rec = {"id": "x", "trigger_utc": "2030-01-01", "market": {"question": "</script><img src=x onerror=alert(1)>", "outcome": "Yes"},
               "risk": {"class": "C1"}, "price_and_depth": {"price_at_alert": 0.1}, "controls": {"out_of_sample": {}}, "wallets": [], "cluster": None}
        html = dashboard.render([rec], [])
        self.assertNotIn("</script><img", html)
        self.assertEqual(html.count("</script>"), 2)                                         # only the page's own two script elements


class Group(unittest.TestCase):
    def test_a_group_alert_names_its_key_and_keeps_the_controller_a_hypothesis(self):
        a = {"id": "g", "class": "C4_COFUNDED_GROUP", "t_alert": 1, "wallets": {"wallet": "0xa", "linked_wallet": {"other": "0xb", "root": "0xkey"},
             "deposits": [{"payer_kind": "plain key"}]}, "evidence": {"fills": [{"tx": "0x1"}], "data_quality": {"history_complete": True}},
             "market": {"price_at_alert": 0.4}, "anomaly": {"readings": {}}, "validation": {}}
        r = record.build(a, "0" * 64, 0)
        self.assertEqual((r["cluster"]["key"], r["wallets"]), ("0xkey", ["0xa", "0xb"]))
        levels = {c["claim"]: c["level"] for c in r["evidence_status"]}
        self.assertEqual(levels["the linked wallets have one controller"], "HYPOTHESIS")
        self.assertEqual(levels["the linked wallets were funded by the same plain key"], "SUPPORTED")


class Notify(unittest.TestCase):
    def test_off_without_configuration_and_a_failure_never_raises(self):
        rec = {"id": "r", "risk": {"class": "C1"}, "trigger_utc": "t", "market": {"question": "q", "outcome": "Yes"},
               "price_and_depth": {"price_at_alert": 0.1}, "controls": {"out_of_sample": {"study_verdict": "NOT_SUPPORTED"}}}
        self.assertEqual(notify.send(rec, env={}), [])
        def boom(url, body):
            raise OSError("down")
        self.assertEqual(notify.send(rec, env={"RADAR_WEBHOOK_URL": "https://example.invalid/h"}, post=boom), [("webhook", "OSError")])
        self.assertIn("not a finding about a person", notify.text(rec))


if __name__ == "__main__":
    unittest.main()
