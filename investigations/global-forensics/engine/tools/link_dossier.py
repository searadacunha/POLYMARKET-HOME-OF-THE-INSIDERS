"""Re-read a suspected money link hop by hop, then answer three separate questions about one address: did it fund the accounts, is it a service, who holds it.

Usage: link_dossier.py <spec.json> <out.json>. The spec lists the hops to prove, the subject address and the accounts. Each hop is read from two nodes; the level comes from the receipts, never from the spec. Every number in the output comes from a read made here.
"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import bridges, env, explorer, labels, proof
from gf.net import Net, Refused

env.redirect_temp()


def read_hop(net, hop):
    chain, tx = hop['chain'], hop['tx']
    moves, record = proof.read_tx(net, chain, tx)
    source, target = hop['from'].lower(), hop['to'].lower()
    hits = [m for m in moves if m['from'] == source and m['to'] == target and (m.get('token') == hop['token'])]
    out = dict(hop, status=record['status'], block_number=record['block_number'], block_hash=record['block_hash'], timestamp=record['timestamp'], second_host=record.get('second_host'), submitter=record.get('submitter'), found=bool(hits and record['status'] == 1))
    if hits:
        out.update(level=hits[0]['level'], log_index=hits[0].get('log_index'), raw_amount=hits[0]['raw_amount'], decimals=hits[0]['decimals'], usd_note=None)
    return out


def read_bridge(net, b):
    """Same Relay id read on both chains, from the nodes only."""
    onchain = bridges.relay_onchain_origin(net, b['payout_tx'], b['payout_at'], b['payout_chain'])
    tied = bool(onchain and onchain.get('proof') is True and any(h.lower() == b['deposit_tx'].lower() for _, h in onchain['in_txs']))
    return dict(b, same_id_on_both_chains=tied, relay_id=(onchain or {}).get('id'), sender_read=(onchain or {}).get('sender'))


def subject_questions(net, subject, accounts):
    """Each question is answered from this address's full listed history on the chains read. Absent chains stay absent."""
    chains, rows = {}, []
    for chain in (1, 137, 42161, 10):
        events, coverage = explorer.history(net, subject, chain)
        chains[chain] = dict(status=coverage['status'], rows=coverage.get('rows'))
        rows += [dict(e, chain=chain) for e in events if e.get('success', True) and int(e['raw_amount']) > 0 and (e.get('token_known') or e['kind'] != 'erc20')]
    for chain in (8453, 56):
        chains[chain] = explorer.presence(net, subject, chain)
    info = labels.classify(net, subject, 1)
    wanted = {a.lower() for a in accounts}
    parties_out = {e['to'] for e in rows if e['from'] == subject}
    parties_in = {e['from'] for e in rows if e['to'] == subject}
    return dict(address=subject, chains=chains, classify=info, value_rows=len(rows), value_parties_in=sorted(parties_in), value_parties_out=sorted(parties_out),
                funded_an_account_directly=sorted(parties_out & wanted),
                is_labelled_service=bool(info.get('label')), is_contract=info.get('kind') == 'CONTRACT', high_party_count=len(parties_in | parties_out) >= labels.HIGH_PARTIES,
                ownership='OWNERSHIP_NOT_ESTABLISHED')


def main(spec_path, out):
    spec = json.loads(Path(spec_path).read_text())
    net = Net(budget=spec.get('budget', 3000))
    result = dict(question=spec['question'], hops=[], bridges=[], problems=[])
    for hop in spec['hops']:
        try:
            result['hops'].append(read_hop(net, hop))
        except Refused as exc:
            result['problems'].append(dict(tx=hop['tx'], error=str(exc)[:200]))
    for b in spec['bridges']:
        result['bridges'].append(read_bridge(net, b))
    result['subjects'] = [subject_questions(net, s, spec['accounts']) for s in spec['subjects']]
    result['calls'] = net.calls
    Path(out).write_text(json.dumps(result, indent=1))
    print(json.dumps(dict(hops=len(result['hops']), found=sum(h['found'] for h in result['hops']), reverified=sum(h.get('level') == 'REVERIFIED' for h in result['hops']), bridges_tied=sum(b['same_id_on_both_chains'] for b in result['bridges']), of=len(result['bridges']), problems=len(result['problems']), calls=net.calls)))


if __name__ == '__main__':
    main(*sys.argv[1:])
