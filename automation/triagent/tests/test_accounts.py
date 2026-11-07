"""Shadow record of new accounts: factory decoding (real log), checkpoint, first payer (real receipt), bursts that
read only what was observed in time and leave services out."""
import json

from tests.base import Case, fixture
from triagent import accounts
from triagent.store import now

EXP = fixture("expected.json")
# Real log of tx 0x801a7a54… (block 96230817), listed in investigations/ballon-dor-census wallet_deploy.json
REAL_LOG = {"address": accounts.FACTORY_2026, "blockNumber": hex(96230817), "blockTimestamp": hex(1793051597),
            "transactionHash": "0x801a7a544e5b4fa718d1a553a2555f98d85be1e6b6d20beac276b03c314d1dd9",
            "topics": [accounts.NEW_2026, "0x" + "0" * 24 + "001796acef71c0954a05694d5591e66612a4fe27",
                       "0x" + "0" * 24 + "be950f1df4a1c12af1d554ed8be3b322980daf2b",
                       "0x" + "0" * 24 + "be950f1df4a1c12af1d554ed8be3b322980daf2b"],
            "data": "0x" + "0" * 24 + "7a18edfe055488a3128f01f563e5b479d92ffc3a", "removed": False}


def rpc_post(responses):
    def post(url, method="POST", body=None, **kw):
        key = body["method"] if body["method"] != "eth_getLogs" else ("logs", body["params"][0]["address"])
        result = responses(key, body["params"])
        return 200, json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode()
    return post


class AccountTests(Case):
    mode = "live"

    def test_real_factory_log_decodes_to_the_documented_proxy(self):
        self.assertEqual(accounts.decode(REAL_LOG), ("0x001796acef71c0954a05694d5591e66612a4fe27",
                                                     "0xbe950f1df4a1c12af1d554ed8be3b322980daf2b"))
        self.assertIsNone(accounts.decode({**REAL_LOG, "topics": ["0x" + "1" * 64, *REAL_LOG["topics"][1:]]}))
        safe = {"address": accounts.SAFE_FACTORY, "topics": [accounts.SAFE_TOPIC + "0" * 56],
                "data": "0x" + "0" * 24 + "ab" * 20 + "0" * 64}
        self.assertEqual(accounts.decode(safe), ("0x" + "ab" * 20, ""))

    def test_scan_is_checkpointed_idempotent_and_skips_removed_logs(self):
        removed = {**REAL_LOG, "removed": True, "topics": [REAL_LOG["topics"][0], "0x" + "0" * 24 + "c" * 40,
                                                            *REAL_LOG["topics"][2:]]}
        post = rpc_post(lambda key, p: hex(96230900 + 64) if key == "eth_blockNumber" else
                        ([REAL_LOG, removed] if key == ("logs", accounts.FACTORY_2026) else []))
        self.assertEqual(accounts.scan_creations(self.cfg, self.store, post), 1)
        row = self.store.query("SELECT * FROM new_accounts")[0]
        self.assertEqual((row["proxy"], row["created_ts"]), ("0x001796acef71c0954a05694d5591e66612a4fe27", 1793051597))
        self.assertEqual(int(self.store.get_kv("accounts_block")), 96230900)
        self.store.set_kv("accounts_block", 96230000)
        self.assertEqual(accounts.scan_creations(self.cfg, self.store, post), 0)  # same log again: no duplicate

    def test_first_payer_from_the_real_deposit_receipt(self):
        self.store.execute("INSERT INTO new_accounts(proxy,factory,block,tx_hash,created_ts,observed_at) "
                           "VALUES (?,?,?,?,?,?)", (EXP["proxy"], accounts.FACTORY_2026, 1, "0x1", now() - 3600,
                                                    now() - 3600))
        act = fixture("activity_v2_deposit_withdrawal.json")
        receipt = fixture("receipt_deposit.json")["result"]

        def fetch(url):
            if "activity" in url:
                return act
            return {"addresses": {}}  # Blockscout: no public tag for the payer
        post = rpc_post(lambda key, p: receipt if key == "eth_getTransactionReceipt" else None)
        out = accounts.trace_first_deposits(self.cfg, self.store, fetch, post)
        self.assertEqual(out, {"checked": 1, "funded": 1, "traced": 1})
        row = self.store.query("SELECT * FROM new_accounts")[0]
        self.assertEqual((row["funder"], row["first_deposit_ts"]), (EXP["funder"], act["data"][0]["timestamp"]))
        self.assertTrue(row["receipt_sha256"])
        self.assertEqual(accounts.trace_first_deposits(self.cfg, self.store, fetch, post)["checked"], 0)

    def add(self, proxy, funder, dep_ts, observed, tags="[]"):
        self.store.execute("INSERT INTO new_accounts(proxy,factory,block,tx_hash,created_ts,observed_at,checked_at,"
                           "first_deposit_tx,first_deposit_ts,funder) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (proxy, accounts.FACTORY_2026, 1, "0x1", dep_ts - 60, observed, observed, "0x2", dep_ts, funder))
        self.store.execute("INSERT OR REPLACE INTO labels(address,tags_json,source,fetched_at) VALUES (?,?,?,?)",
                           (funder, tags, "test", now()))

    def test_bursts_read_only_the_past_and_leave_services_out(self):
        t = now() - 7200
        for i in range(3):
            self.add(f"0x{i:040x}", "0x" + "f" * 40, t + 600 * i, t + 600 * i + 900)
        self.add("0x" + "9" * 40, "0x" + "f" * 40, t + 5000, t + 5000)  # same payer, outside the 1 h window
        for i in range(3):
            self.add(f"0x{i + 10:040x}", "0x" + "e" * 40, t + 60 * i, t + 600, tags='["Relay: Solver"]')
        found = accounts.bursts(self.store, as_of=now())
        self.assertEqual([(b["funder"], b["accounts"]) for b in found], [("0x" + "f" * 40, 3)])
        self.assertEqual(accounts.bursts(self.store, as_of=t + 1200 + 899), [])  # third deposit not yet observed
        self.assertEqual(len(accounts.bursts(self.store, as_of=t + 1200 + 900)), 1)
        self.assertEqual(accounts.bursts(self.store, as_of=now(), fanout_cap=3), [])  # 4 accounts > cap: a service
        self.assertEqual(self.store.query("SELECT count(*) n FROM alerts")[0]["n"], 0)  # shadow: never an alert
        self.assertEqual(self.store.query("SELECT count(*) n FROM bus")[0]["n"], 0)

    def test_unfunded_accounts_follow_a_bounded_schedule(self):
        self.store.execute("INSERT INTO new_accounts(proxy,factory,block,tx_hash,created_ts,observed_at) VALUES "
                           "(?,?,?,?,?,?)", ("0x" + "a" * 40, accounts.FACTORY_2026, 1, "0x1", now() - 700, now() - 700))
        empty = lambda url: {"data": [], "pagination": {"next_cursor": None}}  # noqa: E731
        runs = []
        for shift in (0, 0, 3000, 0, 18000, 70000, 10**6):
            self.store.execute("UPDATE new_accounts SET observed_at=observed_at-?", (shift,))
            runs.append(accounts.trace_first_deposits(self.cfg, self.store, empty, None)["checked"])
        self.assertEqual(runs, [1, 0, 1, 0, 1, 1, 0])  # 10 min, 1 h, 6 h, 24 h, then never again
