"""Synthetic offline tests; historical CSV remains unchanged."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'replay.py'
spec = importlib.util.spec_from_file_location('cycle_negative_control', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestReplay(unittest.TestCase):
    def write(self, names, records):
        fh = tempfile.NamedTemporaryFile(mode='w', newline='', encoding='utf-8', delete=False)
        with fh:
            writer = csv.DictWriter(fh, fieldnames=names)
            writer.writeheader()
            writer.writerows(records)
        self.addCleanup(Path(fh.name).unlink)
        return fh.name

    def sample(self):
        return [dict(proxy='0x1', market='M', side='BUY', won='False', price='0.10',
                     usdc='100', payout_if_redeemed='0', trade_tx='0xa', funding_lineage='CHILD'),
                dict(proxy='0x2', market='M', side='BUY', won='True', price='0.20',
                     usdc='200', payout_if_redeemed='999', trade_tx='0xb', funding_lineage='CHILD')]

    def test_price_relative_arithmetic_not_probability(self):
        records = self.sample()
        s = mod.railgun(self.write(list(records[0]), records))
        self.assertEqual((s['rows'], s['wins'], s['losses']), (2, 1, 1))
        self.assertEqual(s['price_sum'], '0.300000')
        self.assertEqual(s['arithmetic_win_minus_mean_entry_price'], '0.350000')
        self.assertEqual(s['potential_payout_if_redeemed_usdc'], '999.000000')

    def test_duplicate_wallet_rejected(self):
        records = self.sample()
        records[1]['proxy'] = '0x1'
        with self.assertRaisesRegex(ValueError, 'duplicate trading wallet'):
            mod.railgun(self.write(list(records[0]), records))

    def test_invalid_prices_rejected(self):
        records = self.sample()
        records[0]['price'] = 'NaN'
        with self.assertRaisesRegex(ValueError, 'non-finite'):
            mod.railgun(self.write(list(records[0]), records))

    def test_winner_payout_mismatch_rejected(self):
        records = self.sample()
        records[1]['payout_if_redeemed'] = '0'
        with self.assertRaisesRegex(ValueError, 'payout label'):
            mod.railgun(self.write(list(records[0]), records))

    def test_missing_schema_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing columns'):
            mod.railgun(self.write(['proxy'], [{'proxy':'0x1'}]))

    def test_kpmg_reconciliation(self):
        x = dict(sender='a', recipient='b', status='CONFIRMED', L1_polygon_tx='x', L2_polygon_tx='y',
                 seconds_L1_to_L2='18', intermediary_credit_usdc_atomic='1234',
                 intermediary_debit_usdc_atomic='1234')
        out = mod.kpmg(self.write(list(x), [x]))
        self.assertEqual(out['delay_seconds_min'], 18)
        x['intermediary_debit_usdc_atomic'] = '1233'
        with self.assertRaisesRegex(ValueError, 'does not reconcile'):
            mod.kpmg(self.write(list(x), [x]))

    def test_noncausal_handoff_rejected(self):
        x = dict(sender='a', recipient='b', status='CONFIRMED', L1_polygon_tx='x', L2_polygon_tx='y',
                 seconds_L1_to_L2='-1', intermediary_credit_usdc_atomic='2',
                 intermediary_debit_usdc_atomic='2')
        with self.assertRaisesRegex(ValueError, 'non-causal'):
            mod.kpmg(self.write(list(x), [x]))

if __name__ == '__main__':
    unittest.main()
