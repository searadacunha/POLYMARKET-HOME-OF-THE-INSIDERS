#!/usr/bin/env python3
"""Phase 10 : chronologies Maduro (03/01/2026) et Iran (28/02/2026), PROTOCOLE_P10 §9.
Flux complet (toutes tailles, ordre exact) du data-api, contrôlé contre les logs on-chain de la phase 2 ;
signaux du détecteur (état rejoué causalement sur le flux >= 100 $) ; événements publics marqués VÉRIFIÉ ou APPROXIMATE.
Règle d'activité inhabituelle (fixée avant lecture) : première tranche de 5 min du jour J (00:00 UTC ->) dont le volume d'achats agressifs
YES-équivalents dépasse le P99 des tranches de 5 min de la veille (12:00 -> 23:59 UTC).
Sortie : phase10/maduro_iran_timeline.csv, phase10/maduro_iran_minutes.csv, phase10/population_A_mecanismes.csv"""
import os, sys, json, datetime as dt
import numpy as np, pandas as pd

# Les pickles lus ici sont produits localement par les scripts p8/p9/p10 ; ne jamais en charger d'autres.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p9_detector import Detecteur  # noqa: E402
from p10_impact import load_tape  # noqa: E402

OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase10/')
EX = '0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e'
A8 = {'0x168b100d7a6620a2f49a455344c2c006eaf1714b': 'Chiwawas', '0x5621116629c5d640c8186f577362478cc6605245': 'TacticalInsiderNews',
      '0x38745db27f7360a287f6ca3c9b6a6a9c76149801': 'Planktonbets', '0x60280beffdfeaf962de4e6397ab49ed05a1b99e1': 'X34',
      '0x834079f62fa9b4b0bdfad5b8b7a841e8267da024': 'chileno777', '0xbf32f7a77ccea8bba647fea63d438ce1778b1762': '154x838hjd6',
      '0x56efadc9defe5b7a21af751e0d026f2cf54136db': 'Neodbs', '0xe9b80c387ba77a585423b13c850c2e126c3befd8': 'Mrs.Joker'}
CAS = {
    'Maduro': dict(tape='EVT_MADURO', cid='0x580adc1327de9bf7c179ef5aaffa3377bb5cb252b7d6390b027172d43fd6f993', jour='2026-01-03', veille='2026-01-02 12:00',
                   end='2026-01-31 12:00', fills=['fills_maduro.jsonl'], fills_win=('2026-01-03 05:00:49', '2026-01-03 06:11:45'),
                   public=[('ordre de lancement donné par Trump (non public à l\'époque)', '2026-01-03 03:46', 'APPROXIMATE', 'Wikipedia : « 22:46 EST on 2 January », à la minute, source secondaire'),
                           ('premières explosions signalées à Caracas', '2026-01-03 06:00', 'APPROXIMATE', 'Wikipedia : « around 02:00 VET »'),
                           ('annonce de la capture par Trump (Truth Social)', '2026-01-03 09:21', 'APPROXIMATE', 'Wikipedia : « 05:21 VET / 04:21 ET », heure du post non revérifiée sur le post lui-même')]),
    'Iran': dict(tape='EVT_IRAN', cid='0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20', jour='2026-02-28', veille='2026-02-27 12:00',
                 end='2026-03-01 04:59', fills=['fills_iran.jsonl'], fills_win=('2026-02-28 05:28:01', '2026-02-28 06:12:59'),
                 public=[('autorisation des frappes par Trump (non publique à l\'époque)', '2026-02-27 20:38', 'APPROXIMATE', 'Wikipedia : « 3:38 p.m. EST »'),
                         ('début des frappes', '2026-02-28 06:15', 'APPROXIMATE', 'Wikipedia : « around 9:45 a.m. IRST »'),
                         ('annonce d\'Israël (Katz, « preemptive strike ») et sirènes', '2026-02-28 06:23', 'VÉRIFIÉ', 'Times of Israel, entrée de liveblog horodatée 8:23 heure d\'Israël (UTC+2)')]),
}
TS = lambda s: int(pd.Timestamp(s, tz='UTC').timestamp())
U = lambda t: dt.datetime.fromtimestamp(int(t), dt.UTC).strftime('%Y-%m-%d %H:%M:%S')


def check_onchain(T, c):
    """Complétude du data-api contre les fills on-chain de la phase 2 sur la même fenêtre."""
    F = [json.loads(l) for f in c['fills'] for l in open(f)]
    tk = {x['tx'] for x in F if 'ts' in x and x['taker'].lower() == EX}
    a, b = TS(c['fills_win'][0]), TS(c['fills_win'][1])
    da = set(T[(T.ts >= a) & (T.ts <= b)].tx)
    return len(tk), len(da), len(tk - da), len(da - tk)


def detector_alerts(c, tape):
    """Rejoue le détecteur (flux >= 100 $ de l'univers + ce marché, dans l'ordre) jusqu'à la fin de la fenêtre ; renvoie les alertes du marché."""
    P = pd.read_pickle('p9/prints.pkl')
    end = TS(c['end'])
    t_end = int(tape.ts.max())
    x = tape[(tape.usd >= 100)].copy()
    ext = pd.DataFrame(dict(ts=x.ts.values, cid=c['cid'], cat='geopolitics/war', end=end, wallet=x.wallet.values, side=x.side.values,
                            asset=np.where(x.oi == 0, c['tokens']['Yes'], c['tokens']['No']), price=x.price.values, usd=x.usd.values, oi=x.oi.values, rid=-1))
    base = P[(P.ts <= t_end) & (P.cid != c['cid'])][['ts', 'cid', 'cat', 'end', 'wallet', 'side', 'asset', 'price', 'usd', 'oi', 'rid']]
    if c['cid'] in set(P.cid):          # Maduro est dans l'univers : on garde son flux >= 100 $ hors fenêtre
        own = P[(P.cid == c['cid']) & ((P.ts < int(tape.ts.min())) | (P.ts > t_end))][base.columns]
        base = pd.concat([base, own])
    S = pd.concat([base, ext]).sort_values('ts', kind='stable')
    det = Detecteur(differe=True)
    E = det.rejouer(S, log_every=0)
    E = E[(E.cid == c['cid']) & (E.ts >= int(tape.ts.min()))]
    return det.alertes(E)


def main(mad):
    os.chdir(mad)
    MK = json.load(open(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase2/markets.json')))
    CAS['Maduro']['tokens'] = MK['Maduro out by January 31, 2026?']['tokens']
    CAS['Iran']['tokens'] = MK['US strikes Iran by February 28, 2026?']['tokens']
    tl, mins, popa = [], [], []
    for nom, c in CAS.items():
        T = load_tape(c['tape'], 0)          # direction YES (outcome 0)
        T['yes_buy'] = T.ae
        n_oc, n_da, miss, extra = check_onchain(T, c)
        tl.append(dict(marche=nom, heure_utc='', etape='contrôle de complétude du flux data-api', source='data-api contre logs OrderFilled phase 2', niveau='MESURÉ',
                       detail=f'fenêtre {c["fills_win"][0][11:]}-{c["fills_win"][1][11:]} : {n_oc} transactions preneur on-chain, {n_da} data-api, manquantes {miss}, en trop {extra}'))
        # activité du marché par minute
        T['minute'] = T.ts // 60 * 60
        g = T.groupby('minute')
        Mn = pd.DataFrame({'prix_yes_dernier': g.pd.last(), 'n_trades': g.size(), 'n_wallets': g.wallet.nunique(),
                           'vol_achat_yes_eq': T[T.yes_buy].groupby('minute').usd.sum(), 'vol_vente_yes_eq': T[~T.yes_buy].groupby('minute').usd.sum()}).fillna(0)
        Mn['marche'] = nom
        Mn['minute_utc'] = [U(m) for m in Mn.index]
        mins.append(Mn.reset_index(drop=True))
        # activité inhabituelle
        T['b5'] = T.ts // 300 * 300
        v5 = T[T.yes_buy].groupby('b5').usd.sum()
        ref = v5[(v5.index >= TS(c['veille'])) & (v5.index < TS(c['jour']))]
        full = pd.Series(0.0, index=range(TS(c['veille']) // 300 * 300, TS(c['jour']) // 300 * 300, 300))
        full.update(ref)
        p99 = float(full.quantile(0.99))
        day = v5[v5.index >= TS(c['jour'])]
        fb = day[day > p99]
        first = int(fb.index[0]) if len(fb) else None
        pub = TS(c['public'][1][1])                         # premier événement public du jour J (heure approximative)
        pre = day[(day.index < pub)]
        n_b = len(range(TS(c['jour']), pub, 300))
        exc = pre[pre > p99]
        tl.append(dict(marche=nom, heure_utc=U(first) if first else 'aucune', etape='première tranche de 5 min au-dessus du P99 de la veille', source='flux complet', niveau='MESURÉ',
                       detail=(f'P99 veille = {p99:,.0f} $ ; tranche = {fb.iloc[0]:,.0f} $ ; entre 00:00 et l\'événement public : {len(exc)} tranches au-dessus sur {n_b} '
                               f'(attendu par hasard : {0.01 * n_b:.1f}) à ' + ', '.join(U(t)[11:16] for t in exc.index)) if first else f'P99 veille = {p99:,.0f} $'))
        # repricing : repères robustes de la phase 2 (série CLOB à la minute) + premier trade du flux complet à p_yes >= 0,5
        PS = json.load(open(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase2/price_series.json')))
        ps = PS[{'Maduro': 'Maduro out by January 31, 2026?', 'Iran': 'US strikes Iran by February 28, 2026?'}[nom]]
        rep = int(ps['t_1p5x'])
        tl.append(dict(marche=nom, heure_utc=U(rep), etape=f'repricing : série CLOB à la minute >= 1,5 x {ps["base_median_prev_hour"]} (phase 2)', source='CLOB prices-history', niveau='MESURÉ', detail=''))
        h50 = T[(T.ts >= TS(c['jour'])) & (T.pd >= 0.5)]
        tl.append(dict(marche=nom, heure_utc=U(h50.ts.iloc[0]) if len(h50) else 'aucun', etape='premier trade du flux complet à p_yes >= 0,5', source='flux complet', niveau='MESURÉ',
                       detail=f'{h50.usd.iloc[0]:,.0f} $ par {h50.wallet.iloc[0][:10]}' if len(h50) else ''))
        # 8 comptes : activité
        for w, lab in A8.items():
            x = T[T.wallet == w]
            if x.empty:
                continue
            for r in x.itertuples():
                tl.append(dict(marche=nom, heure_utc=U(r.ts), etape=f'trade de {lab}', source='flux complet', niveau='MESURÉ',
                               detail=f'{"achat" if r.side == "BUY" else "vente"} {"YES" if r.oi == 0 else "NO"} {r.usd:,.0f} $ à {r.price:.3f} (p_yes {r.pd:.3f}), {len(r.levels)} niveaux'))
        # signaux du détecteur
        AL = detector_alerts(c, T)
        for r in AL.itertuples():
            if r.ts > rep + 600:
                continue
            tl.append(dict(marche=nom, heure_utc=U(r.ts), etape=f'alerte détecteur {r.signals}', source='p9_detector.py rejoué', niveau='MESURÉ',
                           detail=f'{r.wallet[:10]}{" (" + A8[r.wallet] + ")" if r.wallet in A8 else ""} {r.direction} {r.usd:,.0f} $ p={r.p_before:.3f} hist={r.wallet_history_score:.3f} n={r.wallet_history_n:.0f}'))
        for lab, h, niv, src in c['public']:
            tl.append(dict(marche=nom, heure_utc=h + ':00', etape=lab, source=src, niveau=niv, detail=''))
        # mécanismes pour les 8 comptes (§21)
        for w, lab in A8.items():
            x = T[(T.wallet == w) & T.yes_buy]
            if x.empty:
                continue
            for r in x.itertuples():
                i = int(r.Index)
                before = T.iloc[:i]
                pb = float(before.pd.iloc[-1]) if len(before) else np.nan
                lv = sorted([((q if o == 0 else 1 - q), s) for (o, sd, q, s, ww) in r.levels], key=lambda z: z[0])
                imp = (lv[-1][0] - pb) if lv and pd.notna(pb) else np.nan
                after = T.iloc[i + 1:]
                f600 = after[(after.ts <= r.ts + 600) & after.yes_buy & (after.wallet != w)]
                popa.append(dict(marche=nom, compte=lab, heure_utc=U(r.ts), usd=r.usd, p_yes=r.pd, IMMEDIATE_IMPACT=imp,
                                 acheteurs_yes_600s_apres=f600.wallet.nunique(), volume_yes_600s_apres=f600.usd.sum(),
                                 p_yes_600s_apres=float(after[after.ts <= r.ts + 600].pd.iloc[-1]) if len(after[after.ts <= r.ts + 600]) else np.nan))
    TL = pd.DataFrame(tl)
    TL['_t'] = pd.to_datetime(TL.heure_utc.where(TL.heure_utc.str.match(r'^\d{4}-'), None), utc=True)
    TL = TL.sort_values(['marche', '_t'], na_position='first').drop(columns='_t')
    TL.to_csv(OUT + 'maduro_iran_timeline.csv', index=False)
    pd.concat(mins).to_csv(OUT + 'maduro_iran_minutes.csv', index=False)
    PA = pd.DataFrame(popa)
    PA.to_csv(OUT + 'population_A_mecanismes.csv', index=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 130)
    print(TL[['marche', 'heure_utc', 'etape', 'niveau', 'detail']].to_string())
    print(PA.round(3).to_string())


if __name__ == '__main__':
    main(sys.argv[1])
