"""First funding status of one (chain, address) against its first payout from a source, by the definitions of PLAN.md. Reads the start of its history. A truncated or refused read gives E, never C or D. Also keeps what the address did right after, to tell clients from service deposit addresses."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import es, net
ROOT = net.ROOT
RECOGNISED = None
HUB_SET = None


def _load():
    global RECOGNISED, HUB_SET
    if RECOGNISED is None:
        RECOGNISED = {(int(r['chain']), r['contract']) for r in csv.DictReader(open(ROOT / 'state/tokens.csv')) if r['recognised'] == 'True'}
        import sources as S
        HUB_SET = {a for _, a in S.ETIQUETEE | S.CANDIDAT}


def classify(chain, addr, first_ts, first_tx):
    """Returns a dict with status and evidence. Rows read oldest first."""
    _load()
    out = dict(chain=chain, address=addr, first_ts=first_ts, first_tx=first_tx, status='E_INCONNU', why='', earliest=None, earliest_tx=None, earliest_src=None, tx_rows=0, tok_rows=0, signed_before=0, to_hub_after=0, gas_shape=False)
    try:
        tx = es.rows('txlist', addr, chain, sort='asc', offset=30)
        tok = es.rows('tokentx', addr, chain, sort='asc', offset=100)
    except Exception as e:
        out['why'] = f'lecture refusée: {type(e).__name__}'
        return out
    inb = []
    for r in tx:
        t = int(r['timeStamp'])
        if (r['to'] or '').lower() == addr and int(r['value']) > 0 and r.get('isError') == '0':
            inb.append((t, r['hash'], r['from'].lower()))
        if r['from'].lower() == addr and (t < first_ts or (t == first_ts and r['hash'] != first_tx)):
            out['signed_before'] += 1
    for r in tok:
        t = int(r['timeStamp'])
        if r['to'].lower() == addr and int(r['value']) > 0 and (chain, r['contractAddress'].lower()) in RECOGNISED:
            inb.append((t, r['hash'], r['from'].lower()))
        if r['from'].lower() == addr and r['to'].lower() in HUB_SET and t >= first_ts:
            out['to_hub_after'] += 1
    out.update(tx_rows=len(tx), tok_rows=len(tok))
    # a read cut before the payout says nothing about what came before it
    cut = (len(tx) >= 30 and int(tx[-1]['timeStamp']) < first_ts) or (len(tok) >= 100 and int(tok[-1]['timeStamp']) < first_ts)
    before = sorted(x for x in inb if x[0] < first_ts or (x[0] == first_ts and x[1] != first_tx))
    if before:
        out.update(status='D_DEJA_ACTIVE', why='valeur reçue avant', earliest=before[0][0], earliest_tx=before[0][1], earliest_src=before[0][2])
        return out
    if out['signed_before']:
        out.update(status='D_DEJA_ACTIVE', why='transaction signée avant, sans entrée lue')
        return out
    if cut:
        out['why'] = 'historique coupé avant le paiement'
        return out
    try:
        internal = es.rows('txlistinternal', addr, chain, sort='asc', offset=20)
    except Exception as e:
        out['why'] = f'internes refusées: {type(e).__name__}'
        return out
    bi = sorted((int(r['timeStamp']), r['hash'], r['from'].lower()) for r in internal if r['to'].lower() == addr and int(r['value']) > 0 and int(r['timeStamp']) <= first_ts and r['hash'] != first_tx)
    if bi:
        out.update(status='D_DEJA_ACTIVE', why='interne reçue avant', earliest=bi[0][0], earliest_tx=bi[0][1], earliest_src=bi[0][2])
        return out
    if len(internal) >= 20 and int(internal[-1]['timeStamp']) < first_ts:
        out['why'] = 'internes coupées avant le paiement'
        return out
    out.update(status='C_FIRST_FUNDED', why='aucune valeur lue avant')
    return out
