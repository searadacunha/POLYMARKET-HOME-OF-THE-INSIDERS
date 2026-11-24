"""Offline audit of external binary-market labels against reviewed crosswalks."""
import argparse
import csv
import json
import re
import unittest
from collections import Counter


def audit(external, reviewed):
    refs = {}
    for row in reviewed:
        cid = row['condition_id'].lower()
        outcome = row['outcome'].upper()
        if not re.fullmatch(r'0x[0-9a-f]{64}', cid) or outcome not in ('YES', 'NO'):
            raise ValueError('invalid reviewed identity or outcome')
        if not row['source'].strip() or cid in refs:
            raise ValueError('missing provenance or duplicate reviewed condition')
        refs[cid] = (outcome, row['source'])
    counts = Counter(row['market_id_prefix'].lower() for row in external)
    results = []
    for row in external:
        prefix = row['market_id_prefix'].lower()
        reported = row['resolution_outcome'].upper()
        matches = [cid for cid in refs if cid.startswith(prefix)]
        cid = None
        expected = None
        if not re.fullmatch(r'0x[0-9a-f]{8}', prefix) or reported not in ('YES', 'NO'):
            status = 'INVALID_EXTERNAL'
        elif counts[prefix] != 1 or len(matches) > 1:
            status = 'AMBIGUOUS'
        elif not matches:
            status = 'UNREVIEWED'
        else:
            cid = matches[0]
            expected, _ = refs[cid]
            status = 'CONCORDANT_REVIEWED' if reported == expected else 'CONFLICT'
        results.append(dict(prefix=prefix, condition_id=cid, reported=reported,
                            reviewed_outcome=expected, status=status,
                            source=refs[cid][1] if cid else None))
    return results


class Tests(unittest.TestCase):
    def setUp(self):
        self.cid = '0x12345678' + 'a' * 56
        self.ref = dict(condition_id=self.cid, outcome='YES', source='fixture')
        self.row = dict(market_id_prefix='0x12345678', resolution_outcome='NO')

    def test_conflict(self):
        self.assertEqual(audit([self.row], [self.ref])[0]['status'], 'CONFLICT')

    def test_concordant(self):
        row = dict(self.row, resolution_outcome='YES')
        self.assertEqual(audit([row], [self.ref])[0]['status'], 'CONCORDANT_REVIEWED')

    def test_missing(self):
        self.assertEqual(audit([self.row], [])[0]['status'], 'UNREVIEWED')

    def test_collision(self):
        other = dict(self.ref, condition_id='0x12345678' + 'b' * 56)
        self.assertEqual(audit([self.row], [self.ref, other])[0]['status'], 'AMBIGUOUS')

    def test_duplicate(self):
        self.assertEqual(audit([self.row, self.row], [self.ref])[0]['status'], 'AMBIGUOUS')

    def test_invalid(self):
        with self.assertRaises(ValueError):
            audit([self.row], [dict(self.ref, condition_id='0x12345678')])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('external')
    parser.add_argument('reviewed')
    args = parser.parse_args()
    with open(args.external, newline='', encoding='utf-8-sig') as f:
        external = list(csv.DictReader(f))
    with open(args.reviewed, newline='', encoding='utf-8-sig') as f:
        reviewed = list(csv.DictReader(f))
    results = audit(external, reviewed)
    print(json.dumps(dict(counts=Counter(r['status'] for r in results), rows=results), indent=2))
    return int(not results or any(r['status'] != 'CONCORDANT_REVIEWED' for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
