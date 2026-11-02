"""Events of an address on a chain with no free explorer, from finished SQD scans. Coverage is the union of what was scanned, stated as such."""
import json
from pathlib import Path

from .env import data_root
from .sqd import Scan


class Index:
    def __init__(self, root=None):
        self.root = Path(root) if root else data_root() / 'raw' / 'sqd'
        self.by_chain = {}
        if self.root.exists():
            for path in self.root.glob('*.state.json'):
                state = json.loads(path.read_text())
                self.by_chain.setdefault(state['chain'], []).append(state)

    def events(self, address, chain):
        states = [s for s in self.by_chain.get(chain, []) if address.lower() in s['addresses']]
        if not states:
            return None
        rows, ranges = [], []
        for s in states:
            scan = Scan(s['chain'], s['addresses'], s['from_block'], s['to_block'], s.get('traces', False), root=self.root)
            ranges.append([s['from_block'], s['next_block']])
            rows += [e for e in scan.events() if address.lower() in (e['from'], e['to'])]
        complete = all(s['done'] for s in states)
        return rows, dict(chain_id=chain, address=address, source='sqd-portal', status='WINDOW_COMPLETE' if complete else 'INCOMPLETE', ranges=ranges, rows=len(rows), note='Only these block ranges were read.')
