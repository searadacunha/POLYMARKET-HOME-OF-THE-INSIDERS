"""Attribution, kept apart from behaviour. A label says what a named source said, on what date; absence means unknown, never personal.

Sources are counted by lineage, because lists copy each other: one Etherscan tag copied in four lists is one source. Reads the
flow-trace label tables and the ChangeNOW attribution table already in the repository, without writing anything there.
"""
import csv
import importlib.util
import sys
from functools import lru_cache
from pathlib import Path

HIGH_NONCE = 1000
HIGH_PARTIES = 400
SERVICE, CONTRACT, HUB, PERSONAL, UNREAD = 'SERVICE', 'CONTRACT', 'HUB_MEASURED', 'PERSONAL_SIZED', 'UNREAD'
TERMINAL_CATEGORIES = ('exchange', 'instant_exchange', 'mixer_or_privacy', 'custodial_unattributed', 'exchange_candidate')


def _flow_trace_labels_path():
    """The original folder holds the label lists the repository does not redistribute. Read only."""
    for path in (Path.home() / 'Projects/PolySentinel-flow-trace/tools/labels.py',):
        if path.exists():
            return path
    raise FileNotFoundError('flow-trace label tables are local only: ~/Projects/PolySentinel-flow-trace')


@lru_cache(maxsize=1)
def _flow_trace():
    path = _flow_trace_labels_path()
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('flow_trace_labels', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _changenow():
    out = {}
    path = Path.home() / 'Projects/PolySentinel-ChangeNOW-outflows/data/attribution_sources.csv'
    if path.exists():
        with path.open() as f:
            for r in csv.DictReader(f):
                out.setdefault(r['address'].lower(), []).append(dict(label=r['label'], source=r['source'], lineage=r['lineage'], date=r.get('read_at'), chain=r.get('chain')))
    return out


def lookup(address, chain):
    """Best label with its source, every ChangeNOW attribution with its lineage, and a count of independent lineages."""
    found = _flow_trace().lookup(address, chain)
    cn = _changenow().get(address.lower(), [])
    if not found and not cn:
        return None
    out = dict(found or {})
    if cn:
        out.setdefault('name', cn[0]['label'])
        out.setdefault('category', 'instant_exchange')
        out.setdefault('level', 'attribution_table')
        out.setdefault('source', cn[0]['source'])
        out['changenow_lineages'] = sorted({c['lineage'] for c in cn})
    out['independent_lineages'] = len(out.get('changenow_lineages', [])) or 1
    return out


def classify(net, address, chain, parties=None):
    """Label first, then code, then measured size. A failed probe stays UNREAD, it never becomes personal."""
    label = lookup(address, chain)
    out = dict(address=address, chain=chain, label=label)
    try:
        code, _ = net.rpc('eth_getCode', [address, 'latest'], chain)
        nonce_hex, _ = net.rpc('eth_getTransactionCount', [address, 'latest'], chain)
    except Exception as exc:  # any node failure: the address stays unclassified, and the walk stops there with the reason
        out.update(cls=SERVICE if label and label.get('category') != 'other_labeled' else UNREAD, nonce=None, kind=None, probe_error=str(exc)[:160])
        return out
    delegated = bool(code) and code.startswith('0xef0100')
    is_contract = code not in ('0x', '0x0', None) and not delegated
    out.update(nonce=int(nonce_hex, 16), kind='EIP7702_DELEGATED_EOA' if delegated else 'CONTRACT' if is_contract else 'EOA')
    if label and label.get('category') != 'other_labeled':
        out['cls'] = SERVICE
    elif is_contract:
        out['cls'] = CONTRACT
    elif out['nonce'] >= HIGH_NONCE or (parties or 0) >= HIGH_PARTIES:
        out['cls'] = HUB
    else:
        out['cls'] = PERSONAL
    return out
