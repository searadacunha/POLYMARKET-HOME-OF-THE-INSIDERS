"""Adversarial tests against code already in the repository. Synthetic inputs only, no network, nothing modified.

A test named test_defect_* passes while the defect exists: it documents the behaviour and how to see it. When the audited
code is fixed it fails, which is the signal to update AUDIT.md. A test named test_holds_* checks a defence that really works.
"""
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
REPO = Path(os.environ['PHI_REPO']) if os.environ.get('PHI_REPO') else next((p for p in HERE.parents if (p / 'scripts/phi_lib.py').exists()), Path.home() / 'Projects/Polymarket-Home-of-the-Insiders')
ENGINE = REPO / 'investigations/polysentinel/sources/signal_engine'
sys.path.insert(0, str(ENGINE.parent))
if 'httpx' not in sys.modules:  # fund_flow.client imports it at load; these tests make no request
    fake = types.ModuleType('httpx')
    fake.HTTPError = Exception
    fake.Client = object
    sys.modules['httpx'] = fake

from signal_engine import collective_behavior as cb  # noqa: E402
from signal_engine import evidence_scoring as scoring  # noqa: E402
from signal_engine import funding_graph as fg  # noqa: E402

BUILT = 'lien directement observable'
A, B, C = '0x' + 'a' * 40, '0x' + 'b' * 40, '0x' + 'c' * 40
HOT = '0x' + 'f' * 40


def edge(source, target, tx, log_index, raw=100_000_000, **extra):
    return dict(source=source, target=target, transaction_hash=tx, log_index=log_index, token='0x' + '1' * 40, symbol='USDC', amount=raw / 1e6, amount_raw=raw, timestamp=1000 + (log_index or 0), proof_level=BUILT, **extra)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Store:
    """The two tables collective_signals reads, in memory."""

    def __init__(self):
        self.cx = sqlite3.connect(':memory:')
        self.cx.row_factory = sqlite3.Row
        self.cx.execute('CREATE TABLE trades(wallet TEXT, token_id TEXT, tx TEXT, ts INT, nominal REAL, event_key TEXT, is_buy INT, observed_at REAL)')
        self.cx.execute('CREATE TABLE pairs(wallet TEXT, event_key TEXT, evaluated_at REAL, anomalies TEXT)')

    def trade(self, wallet, ts, tx, nominal=5000, token='T', observed=None):
        self.cx.execute('INSERT INTO trades VALUES(?,?,?,?,?,?,?,?)', (wallet, token, tx, ts, nominal, 'E', 1, ts if observed is None else observed))

    def flag(self, wallet, at, event='E'):
        self.cx.execute('INSERT INTO pairs VALUES(?,?,?,?)', (wallet, event, at, '{"x":1}'))


CONFIG = json.loads((ENGINE / 'config.json').read_text())


class FundingGraph(unittest.TestCase):
    """Risk 1 of the mission: a shared funder without a real split between private wallets and central infrastructure."""

    def test_defect_exchange_hot_wallet_without_flag_becomes_shared_funder(self):
        """A hub pays two customers. Without the `infrastructure` flag, set only for addresses in a hand list, the link is SHARED_FUNDER and it corroborates."""
        links = fg.build_funding_links([edge(HOT, A, '0x01', 1), edge(HOT, B, '0x02', 2)], [A, B])
        shared = [l for l in links if l['kind'] == fg.SHARED_FUNDER]
        self.assertEqual(len(shared), 1)
        self.assertEqual(fg.corroborating_funding(links), shared)

    def test_defect_label_alone_does_not_stop_a_shared_funder(self):
        """Even a named exchange stays SHARED_FUNDER if only counterparty_label is present."""
        links = fg.build_funding_links([edge(HOT, A, '0x01', 1, counterparty_label='Binance 14'), edge(HOT, B, '0x02', 2, counterparty_label='Binance 14')], [A, B])
        self.assertEqual([l['kind'] for l in links], [fg.SHARED_FUNDER])
        self.assertEqual(links[0]['counterparty_label'], 'Binance 14')

    def test_defect_shared_funder_has_no_time_limit(self):
        """close_in_time is computed and never gated on: payments a year apart keep the same kind and the same corroboration."""
        far = edge(HOT, B, '0x02', 2)
        far['timestamp'] = 1000 + 365 * 86400
        links = fg.build_funding_links([edge(HOT, A, '0x01', 1), far], [A, B])
        self.assertFalse(links[0]['close_in_time'])
        self.assertEqual(fg.corroborating_funding(links), links)

    def test_defect_unindexed_rows_of_one_transaction_cancel_each_other(self):
        """Two different moves listed without a log index collide on (tx, None): both vanish as a conflict."""
        unique, conflicts = fg.unique_edges([edge(A, B, '0x01', None), edge(A, C, '0x01', None)])
        self.assertEqual(unique, [])
        self.assertEqual(len(conflicts), 1)

    def test_holds_flagged_infrastructure_is_not_a_funder(self):
        links = fg.build_funding_links([edge(HOT, A, '0x01', 1, infrastructure=True), edge(HOT, B, '0x02', 2, infrastructure=True)], [A, B])
        self.assertEqual([l['kind'] for l in links], [fg.SHARED_INFRASTRUCTURE])
        self.assertEqual(fg.corroborating_funding(links), [])

    def test_holds_never_states_common_owner(self):
        links = fg.build_funding_links([edge(A, B, '0x01', 1), edge(HOT, A, '0x02', 2), edge(HOT, B, '0x03', 3)], [A, B])
        self.assertTrue(links and all(l['common_owner_established'] is False for l in links))


class CollectiveBehaviour(unittest.TestCase):
    """Risk 2 of the mission: convergence without a really tight window."""

    def setUp(self):
        self.store = Store()
        self.now = 200_000

    def three_wallets(self, gap):
        for i, wallet in enumerate((A, B, C)):
            self.store.trade(wallet, self.now - 3 * gap + i * gap, f'0x{i}')
            self.store.flag(wallet, self.now - 10)

    def test_defect_convergence_over_almost_a_full_day(self):
        """Three flagged buys 8 hours apart are `convergence`, and the spread is computed without gating anything."""
        self.three_wallets(8 * 3600)
        out = cb.collective_signals(self.store, 'E', self.now, CONFIG)
        self.assertEqual(out['convergence'], {'T': sorted((A, B, C))})
        self.assertEqual(out['convergence_spread_s']['T'], 16 * 3600)

    def test_defect_that_convergence_alone_sets_the_top_category(self):
        """classify returns CORROBORATED_BEHAVIOR on convergence alone: no window, no comparator, no money."""
        self.three_wallets(8 * 3600)
        collective = cb.collective_signals(self.store, 'E', self.now, CONFIG)
        pairs = [dict(wallet=w, wallet_findings=[], position_findings=[]) for w in (A, B, C)]
        self.assertEqual(scoring.classify(pairs, collective, dict(level='low'), [], CONFIG), scoring.CORROBORATED_BEHAVIOR)

    def test_defect_replay_sees_flags_set_after_its_clock(self):
        """Flags have a lower time bound only. On a filled database, a replay at T reads anomalies evaluated after T: future information."""
        for i, wallet in enumerate((A, B, C)):
            self.store.trade(wallet, self.now - 100 - i, f'0x{i}')
            self.store.flag(wallet, self.now + 86400)
        out = cb.collective_signals(self.store, 'E', self.now, CONFIG)
        self.assertEqual(out['convergence'], {'T': sorted((A, B, C))})

    def test_defect_repeated_pairs_read_the_future_too(self):
        for wallet in (A, B):
            self.store.flag(wallet, self.now + 86400, event='LATER')
        pairs = cb.repeated_pairs(self.store, {A, B}, 'E', self.now, CONFIG)
        self.assertEqual(pairs[0]['events'], ['E', 'LATER'])

    def test_holds_trades_not_yet_observed_are_invisible(self):
        for i, wallet in enumerate((A, B, C)):
            self.store.trade(wallet, self.now - 100 - i, f'0x{i}', observed=self.now + 5)
            self.store.flag(wallet, self.now - 10)
        self.assertEqual(cb.collective_signals(self.store, 'E', self.now, CONFIG)['convergence'], {})


class EvidenceValidation(unittest.TestCase):
    """Risk 3 of the mission: the central validation checks references, it recomputes nothing and reads no chain."""

    def setUp(self):
        sys.path.insert(0, str(REPO / 'scripts'))
        self.validate = load(REPO / 'scripts/validate_evidence.py', 'validate_evidence_under_test')
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.inv = Path(self.tmp.name)
        (self.inv / 'results').mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def findings(self, claim, source_text):
        (self.inv / 'results/x.md').write_text(source_text)
        (self.inv / 'FINDINGS.md').write_text(f'# Findings\n\n## F-001 | CONFIRMED | {claim}\n- Sources: results/x.md\n- Method: none\n- Limits: none\n- Links: none\n')
        errors = []
        self.validate.check_findings(self.inv, errors)
        return errors

    def test_defect_a_number_elsewhere_in_the_file_validates_any_claim(self):
        """The file says the wallet LOST 5,170. The finding says it WON 5,170 as a CONFIRMED fact, and validation passes."""
        self.assertEqual(self.findings('The wallet won 5,170.00 USDC on Kane', 'The wallet lost 5,170.00 USDC. It won nothing.'), [])

    def test_defect_an_invented_hash_passes_once_written_in_a_source(self):
        fake = '0x' + 'ab' * 32
        self.assertEqual(self.findings(f'Transfer proven by {fake}', f'see {fake}'), [])

    def test_holds_a_number_absent_from_the_source_is_refused(self):
        self.assertTrue(self.findings('The wallet won 5,170.00 USDC', 'nothing here'))


class ForensicIntelligenceBranch(unittest.TestCase):
    """PR 11's modules, tested before any reuse. Skipped when this tree does not carry them."""

    def setUp(self):
        path = REPO / 'integrations/forensic-intelligence'
        if not path.exists():
            self.skipTest('PR 11 modules absent from this tree')
        sys.path.insert(0, str(path))
        self.ledger = load(path / 'ledger.py', 'ledger')
        sys.modules['ledger'] = self.ledger
        self.temporal = load(path / 'temporal.py', 'temporal')

    def row(self, value, log_index=None):
        return dict(chain_id=1, transaction_hash='0x' + 'a' * 64, block_number=1, timestamp_utc='2026-01-01T00:00:00Z', log_index=log_index, **{'from': A, 'to': B}, token_contract=None, token_decimals=18, raw_amount=str(value), normalized_amount=str(value / 1e18), usd_value_when_supported=None, protocol=None, source='test', relation_type='internal_transfer', evidence_level='ONCHAIN_CONFIRMED')

    def test_defect_two_equal_internal_moves_of_a_transaction_merge_into_one(self):
        """Two internal transfers of 1 ETH between the same addresses in one transaction count as 1 ETH."""
        edges = self.ledger.canonical_edges([self.row(10 ** 18), self.row(10 ** 18)])
        self.assertEqual(len(edges), 1)

    def test_defect_two_different_internal_moves_of_a_transaction_are_refused(self):
        """Two legal internal moves of different amounts raise, so a whole import stops on an ordinary transaction."""
        with self.assertRaises(ValueError):
            self.ledger.canonical_edges([self.row(10 ** 18), self.row(2 * 10 ** 18)])

    def test_defect_requested_90_second_window_is_absent(self):
        self.assertNotIn(90, self.temporal.WINDOWS)

    def test_holds_contradictory_logs_are_refused(self):
        with self.assertRaises(ValueError):
            self.ledger.canonical_edges([self.row(10 ** 18, 7), self.row(2 * 10 ** 18, 7)])


class FundFlowTrace(unittest.TestCase):
    """Truncation in the existing tracer."""

    def test_defect_scan_can_exceed_the_receipt_cap_while_capped_stays_false(self):
        """The cap is enforced by sorting hashes and cutting, and `capped` keeps the value it had before the scan added rows."""
        source = (ENGINE / 'fund_flow/trace.py').read_text()
        self.assertIn('capped=len(money) > max_receipts', source)
        self.assertIn('chosen = sorted(set(chosen) | counterparties)[:max_receipts]', source)
        self.assertNotIn("report['flows_examined'].update(capped", source)
        money, scan = ['0x%02d' % i for i in range(5)], {'0x%02d' % i for i in range(5, 60)}
        chosen = sorted(set(money) | scan)[:40]
        self.assertFalse(len(money) > 40)
        self.assertEqual(len(chosen), 40)
        self.assertEqual(len(set(money) | scan) - len(chosen), 20)  # 20 receipts dropped, by hash order, capped still False


class FlowTraceWalk(unittest.TestCase):
    def test_defect_deep_nodes_keep_eight_flows_and_record_nothing_else(self):
        """Past depth 0 only the 8 largest flows and the first are followed, with no stop written for the others."""
        source = (REPO / 'investigations/ballon-dor-flow-trace/sources/tools/walk.py').read_text()
        cut = source[source.index('if depth > 0:  # deep nodes'):source.index('next_nodes = []')]
        self.assertIn('[:8]', cut)
        self.assertNotIn('self.stop', cut)

    def test_defect_relay_hop_is_followed_whatever_its_chain_proof_says(self):
        """The on-chain id check is stored next to the hop, and the walk continues even when it is False or None."""
        source = (REPO / 'investigations/ballon-dor-flow-trace/sources/tools/walk.py').read_text()
        cut = source[source.index('proof = relay_proof(rec)'):source.index("note = None\n            if cls['cls']")]
        self.assertIn('next_nodes.append((far_l, far_chain', cut)
        self.assertNotIn('if proof', cut)


if __name__ == '__main__':
    unittest.main(verbosity=1)
