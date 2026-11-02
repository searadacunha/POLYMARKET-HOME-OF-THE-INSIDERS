#!/usr/bin/env python3
"""Phase 13 : export du paper trading (PAPER ONLY) en table, frais du marché appliqués à l'analyse. Lecture seule des journaux de p13_paper.py.
Entrée : donnees/brut_p13/paper_alerts.jsonl, paper_exits.jsonl ; sortie : phase13/paper_alerts.csv (une ligne par alerte, taille et horizon).
Toutes les alertes y figurent, y compris celles sans carnet ou sans sortie (net vide, jamais rempli)."""
import os, sys, json
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_execution import fee_per_share, market_meta  # noqa: E402

RAW13 = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p13')
OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase13/')
COLS = ['alert_id', 'type', 'source_detection', 'T_DETECT_utc', 'wallet', 'market', 'token', 'prix_wallet', 'usd', 'hist_n', 'hist_score', 'p_before',
        'latence_calcul_ms', 'latence_carnet_ms', 'best_ask', 'best_bid', 'taille_usd', 'vwap', 'restant_usd', 'horizon_s', 'brut', 'net', 'invendu']


def jread(fp):
    return [json.loads(l) for l in open(fp)] if os.path.exists(fp) else []


def main():
    al = jread(os.path.join(RAW13, 'paper_alerts.jsonl'))
    ex = {}
    for e in jread(os.path.join(RAW13, 'paper_exits.jsonl')):
        ex[(e['alert_id'], e['horizon_s'])] = e['sorties']
    meta = market_meta(extra=list({a['market'] for a in al}))
    rows = []
    for a in al:
        base = dict(alert_id=a['alert_id'], type=a['type'], source_detection=a['source_detection'], T_DETECT_utc=pd.Timestamp(a['T_DETECT_ns'], unit='ns', tz='UTC'),
                    wallet=a['wallet'], market=a['market'], token=a['token'], prix_wallet=a['prix_wallet'], usd=a['usd'], hist_n=a.get('hist_n'),
                    hist_score=a.get('hist_score'), p_before=a.get('p_before'), latence_calcul_ms=(a['T_calcul_ns'] - a['T_DETECT_ns']) / 1e6,
                    latence_carnet_ms=a.get('latence_carnet_ms'), best_ask=a.get('best_ask'), best_bid=a.get('best_bid'))
        if not a.get('entree'):
            rows.append(base)
            continue
        for S, e in a['entree'].items():
            fin = (fee_per_share(meta, a['market'], e['vwap']) or 0.0) * e['actions']
            for H in (60, 300):
                o = (ex.get((a['alert_id'], H)) or {}).get(str(S))
                r = dict(base, taille_usd=int(S), vwap=e['vwap'], restant_usd=e['restant'], horizon_s=H)
                if o:
                    q = e['actions'] - o['invendu']
                    fout = (fee_per_share(meta, a['market'], o['produit'] / q) or 0.0) * q if q > 0 else 0.0
                    r.update(brut=o['brut'], net=(o['produit'] - e['cout'] - fin - fout) / e['cout'], invendu=o['invendu'])
                rows.append(r)
    P = pd.DataFrame(rows, columns=COLS)
    P.to_csv(OUT + 'paper_alerts.csv', index=False)
    print('alertes', len(al), 'lignes', len(P), P.groupby('type').alert_id.nunique().to_dict() if len(P) else {})
    if P.net.notna().any():
        print(P[P.net.notna()].groupby(['type', 'taille_usd', 'horizon_s']).net.agg(['count', 'mean', 'median']).round(4).to_string())


if __name__ == '__main__':
    main()
