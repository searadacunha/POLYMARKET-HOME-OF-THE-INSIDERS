import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from weekly_funding import collect
from weekly_funding.archive import historic_cohort
from weekly_funding.bridge import fill_match
from weekly_funding.common import HOME, RPC, TOKENS, TRANSFER, addr_topic, bounds, digest, save
from weekly_funding.frame import frame_members
from weekly_funding.statistics import eligible_panel

A = "0x" + "a" * 40
B = "0x" + "b" * 40
T = "0x" + "1" * 64
H = "0x" + "2" * 64


class Coverage(unittest.TestCase):
    def test_short_market_id_is_not_padded_and_trade_is_retained(self):
        from weekly_funding.accounts import market_ref

        value = "0x03" + "f" * 60
        self.assertEqual(market_ref(value, "123"), "api:" + value)
        self.assertEqual(market_ref("", "123"), "token:123")

    def test_historic_rows_not_distinct_accounts(self):
        cohort = historic_cohort()
        self.assertEqual(
            (cohort["payees"], cohort["bettor_records"], cohort["distinct_trading_addresses"]),
            (3408, 158, 153),
        )

    def test_exhausted_budget_is_gap_not_zero(self):
        with patch.object(collect, "pull", side_effect=ValueError("limit")) as rpc:
            spans, rows, gaps = collect.ranges(137, "tornado", 1, 10001, RPC, [1])
            self.assertFalse(spans)
            self.assertFalse(rows)
            self.assertEqual(sum(b - a + 1 for a, b, _ in gaps), 10001)
            self.assertEqual(rpc.call_count, 1)

    def test_empty_frame_requires_successful_ranges(self):
        p = {
            "week": "2026-W46",
            "chain": 137,
            "ranges": [[1, 8, 0], [20, 27, 0], [50, 57, 0]],
            "fills": [],
        }
        self.assertEqual(frame_members(p, "2026-W46"), set())
        p["ranges"][1][2] = 1
        with self.assertRaises(ValueError):
            frame_members(p, "2026-W46")

    def test_bridge_collision_and_wrong_recipient(self):
        token = next(iter(TOKENS))
        o = dict(out_tx=T, out_token=token, out_units=422, recipient=A)
        raw = dict(
            address=token,
            topics=[TRANSFER, addr_topic(B), addr_topic(A)],
            data=hex(422),
            transactionHash=T,
            blockHash=H,
            logIndex="0x2",
        )
        rc = dict(transactionHash=T, blockHash=H, status="0x1", logs=[raw])
        self.assertEqual(fill_match(o, rc), raw)
        self.assertIsNone(fill_match(o, dict(rc, logs=[raw, dict(raw, logIndex="0x3")])))
        self.assertIsNone(fill_match(dict(o, recipient=B), rc))

    def test_matching_covariates_must_predate_funding(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "matched_panel.json"
            lock = digest(HOME / "PROTOCOL.md")
            lo, hi = bounds("2026-W46")
            save(
                f,
                dict(
                    protocol_sha256=lock,
                    rows=[dict(wallet=A, week="2026-W46", feature_asof=lo + 2, funded_at=lo + 1)],
                ),
            )
            with self.assertRaisesRegex(ValueError, "post-funding"):
                eligible_panel(f, {"2026-W46": {}}, lock, hi)


if __name__ == "__main__":
    unittest.main()
