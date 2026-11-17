import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coverage import coverage_report, deduplicate_logs

ADDR = '0x' + 'a'*40
TOPIC = '0x' + 'b'*64
TX = '0x' + 'c'*64
SCOP = {'chain_id':137,'contract_address':ADDR,'topic0':TOPIC,
        'protocol_variant':'CLOB_V2','from_block':100,'to_block_exclusive':130}


def page(a,b,**kwargs):
    return {**{k: SCOP[k] for k in ('chain_id','contract_address','topic0','protocol_variant')},
            'from_block':a,'to_block_exclusive':b,'completed':True,
            'cursor_exhausted':True,'truncated':False,
            'observed_at_utc':'2026-10-01T00:00:00Z','provider':'synthetic', **kwargs}


class CoverageTest(unittest.TestCase):
    def test_adjacent_half_open_ranges_are_complete(self):
        report=coverage_report(SCOP,[page(100,110),page(110,130)],'2026-10-02T00:00:00Z')
        self.assertEqual(report['reported_covered_blocks'],30)
        self.assertEqual(report['missing_ranges'],[])
        self.assertEqual(report['status'],'REPORTED_RANGE_COVERED')
        self.assertEqual(report['independent_event_completeness'],'NOT_VERIFIED')

    def test_one_block_gap_is_never_silent(self):
        report=coverage_report(SCOP,[page(100,110),page(111,130)],'2026-10-02T00:00:00Z')
        self.assertEqual(report['missing_ranges'],[[110,111]])
        self.assertEqual(report['reported_covered_blocks'],29)

    def test_truncated_and_unexhausted_are_gaps(self):
        report=coverage_report(SCOP,[page(100,115,truncated=True),page(115,130,cursor_exhausted=False)], '2026-10-02T00:00:00Z')
        self.assertEqual(report['reported_covered_blocks'],0)
        self.assertEqual(len(report['rejected_scans']),2)

    def test_no_cross_chain_or_v1_to_v2_false_coverage(self):
        report=coverage_report(SCOP,[page(100,130,protocol_variant='CLOB_V1'),page(100,130,chain_id=1)],'2026-10-02T00:00:00Z')
        self.assertEqual(report['missing_ranges'],[[100,130]])
        self.assertTrue(all(r['reason']=='OTHER_CHAIN_CONTRACT_TOPIC_OR_PROTOCOL' for r in report['rejected_scans']))

    def test_future_observation_excluded(self):
        report=coverage_report(SCOP,[page(100,130,observed_at_utc='2026-10-03T00:00:00Z')], '2026-10-02T00:00:00Z')
        self.assertEqual(report['reported_covered_blocks'],0)

    def test_overlaps_not_double_counted(self):
        report=coverage_report(SCOP,[page(100,118),page(115,130)],'2026-10-02T00:00:00Z')
        self.assertEqual(report['reported_covered_blocks'],30)

    def test_invalid_range_rejected(self):
        with self.assertRaises(ValueError): coverage_report(SCOP,[page(100,100)],'2026-10-02T00:00:00Z')

    def test_dedup_and_conflicting_log(self):
        row=dict(chain_id=137,transaction_hash=TX,log_index=7,contract_address=ADDR,
                 topic0=TOPIC,block_number=125,payload_sha256='d'*64)
        self.assertEqual(len(deduplicate_logs([row,dict(row)])),1)
        with self.assertRaises(ValueError): deduplicate_logs([row,dict(row,payload_sha256='e'*64)])
        with self.assertRaises(ValueError): deduplicate_logs([dict(row,log_index=None)])

    def test_distinct_logs_same_tx_are_distinct(self):
        row=dict(chain_id=137,transaction_hash=TX,log_index=7,contract_address=ADDR,
                 topic0=TOPIC,block_number=125,payload_sha256='d'*64)
        self.assertEqual(len(deduplicate_logs([row,dict(row,log_index=8)])),2)

if __name__=='__main__': unittest.main()
