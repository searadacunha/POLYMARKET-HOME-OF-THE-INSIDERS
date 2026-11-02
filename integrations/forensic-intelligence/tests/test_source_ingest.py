import csv
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_ingest import read_changenow_transfers

BASE = {
    'case':'kraben006', 'chain_id':'1', 'block':'24520622',
    'utc':'2026-02-23 15:56:23', 'event':'erc20_transfer_log', 'log_index':'82',
    'token':'USDC', 'contract':'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
    'decimals':'6', 'raw':'654466304', 'amount':'654.466304',
    'src':'0xdd3d72c53ff982ff59853da71158bf1538b3ceee',
    'dst':'0x101b5f4dc0886c32e2b75972101aeaf9f338fb65',
    'service_label':'ChangeNOW: Hot Wallet 3', 'node_ok':'True',
    'node_proof_sha256':'dab34d0cad470c5131d82e23ad67a0ef09a513c767958b38ec58c95c0feff9af',
    'tx':'0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219',
}
SECOND = {**BASE, 'tx':'0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80',
          'block':'24520663', 'utc':'2026-02-23 16:04:35', 'log_index':'598',
          'raw':'180382489', 'amount':'180.382489',
          'node_proof_sha256':'2d2a5de437c74dafafa0176213f383738642464960254baef2b42ae11cce0734'}


def make_csv(folder, rows):
    target=Path(folder)/'input.csv'
    with target.open('w', newline='') as fh:
        writer=csv.DictWriter(fh, fieldnames=list(BASE))
        writer.writeheader(); writer.writerows(rows)
    return target

class ExistingEvidenceTest(unittest.TestCase):
    def test_two_documented_payments_exact_and_not_service_proof(self):
        with tempfile.TemporaryDirectory() as d:
            result=read_changenow_transfers(make_csv(d,[BASE,SECOND]), 'original/changenow/verified_transfers.csv')
        self.assertEqual(result['source_rows_accepted'],2)
        self.assertEqual(sum(int(x['raw_amount']) for x in result['edges']),834848793)
        self.assertTrue(all(x['protocol'] is None for x in result['edges']))
        self.assertTrue(all(x['log_index'] is not None for x in result['edges']))
        self.assertEqual(len(result['warnings']),0)

    def test_missing_log_index_visible_and_not_silently_complete(self):
        with tempfile.TemporaryDirectory() as d:
            result=read_changenow_transfers(make_csv(d,[dict(BASE,log_index='')]))
        self.assertEqual(result['warnings'][0]['kind'],'EVENT_LOG_INDEX_MISSING')

    def test_inconsistent_amount_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):read_changenow_transfers(make_csv(d,[dict(BASE,amount='999.99')]))

    def test_unverified_node_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            result=read_changenow_transfers(make_csv(d,[dict(BASE,node_ok='False')]))
        self.assertEqual(result['edges'],[])
        self.assertEqual(result['warnings'][0]['kind'],'UNVERIFIED_NODE_RECORD')

    def test_real_original_when_present(self):
        original=Path(__file__).resolve().parents[3]/'investigations/changenow-proof/sources/data/verified_transfers.csv'
        if not original.is_file():self.skipTest('GitHub original source not mounted in isolated container')
        result=read_changenow_transfers(original)
        incoming=[e for e in result['edges'] if e['from'].lower()==BASE['src'] and e['to'].lower()==BASE['dst'] and e['timestamp_utc'].startswith('2026-02-23')]
        self.assertEqual(sum(int(e['raw_amount']) for e in incoming),834848793)
        self.assertEqual(result['source_rows_accepted'],30)
        self.assertGreaterEqual(len(result['warnings']),3)

if __name__=='__main__': unittest.main()
