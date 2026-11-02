"""Phase 9 : étude de cas au bloc, Maduro (03/01/2026) et Iran (28/02/2026).
Chaîne : première activité inhabituelle -> repricing -> information publique.
Sources : fills OrderFilled on-chain de la phase 2 (bloc + logIndex), série CLOB à la minute de la phase 2, flux data-api (phase 8),
et l'état du détecteur p9_detector.py rejoué causalement jusqu'à l'heure de chaque achat (historique du wallet à T).
Règle d'activité inhabituelle (descriptive, fixée avant lecture des fenêtres d'événement) : première tranche de 5 min dont le volume
d'achats agressifs YES-équivalents dépasse le P99 des tranches de 5 min de la fenêtre de référence (autres jours, même marché)."""
import json, sys, os, datetime as dt, collections
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p9_detector import Detecteur
OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase9/')
EX = '0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e'
MK = json.load(open(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase2/markets.json')))
PS = json.load(open(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase2/price_series.json')))
A = {'0x168b100d7a6620a2f49a455344c2c006eaf1714b': 'Chiwawas', '0x5621116629c5d640c8186f577362478cc6605245': 'TacticalInsiderNews',
     '0x38745db27f7360a287f6ca3c9b6a6a9c76149801': 'Planktonbets', '0x60280beffdfeaf962de4e6397ab49ed05a1b99e1': 'X34',
     '0x834079f62fa9b4b0bdfad5b8b7a841e8267da024': 'chileno777', '0xbf32f7a77ccea8bba647fea63d438ce1778b1762': '154x838hjd6',
     '0x56efadc9defe5b7a21af751e0d026f2cf54136db': 'Neodbs', '0xe9b80c387ba77a585423b13c850c2e126c3befd8': 'Mrs.Joker'}
CAS = {
    'Maduro': dict(titre='Maduro out by January 31, 2026?', evt=['fills_maduro.jsonl'], ref=['fills_maduroY.jsonl', 'fills_maduroX.jsonl'],
                   public=[('premières explosions signalées à Caracas', '2026-01-03 06:00', 'Wikipedia « 2026 United States intervention in Venezuela » : « around 02:00 VET », à la minute non établi'),
                           ('annonce de la capture par Trump (Truth Social)', '2026-01-03 09:21', 'Wikipedia, même article : « 05:21 VET / 04:21 ET »')],
                   non_public=[('ordre de lancement donné par Trump (non public à l\'époque)', '2026-01-03 03:46', 'Wikipedia : « 22:46 EST on 2 January »')]),
    'Iran': dict(titre='US strikes Iran by February 28, 2026?', evt=['fills_iran.jsonl'], ref=['fills_iranA.jsonl', 'fills_iranB.jsonl'],
                 public=[('début des frappes (« around 9:45 a.m. IRST »)', '2026-02-28 06:15', 'Wikipedia « 2026 Iran war », heure approximative'),
                         ('annonce d\'Israël (Katz, « preemptive strike ») et sirènes', '2026-02-28 06:23', 'Times of Israel, entrée de liveblog datée 8:23 am heure d\'Israël (UTC+2)')],
                 non_public=[('autorisation des frappes par Trump (non publique à l\'époque)', '2026-02-27 20:38', 'Wikipedia : « 3:38 p.m. EST »')]),
}
U = lambda t: dt.datetime.fromtimestamp(int(t), dt.UTC).strftime('%Y-%m-%d %H:%M:%S')
TS = lambda s: int(pd.Timestamp(s, tz='UTC').timestamp())


def agressifs(files):
    """Fills côté preneur (taker = exchange) -> achats/ventes agressifs, en YES-équivalent."""
    seen, rows = set(), []
    for f in files:
        for l in open(f):
            x = json.loads(l)
            if 'ts' not in x or x['taker'].lower() != EX or (x['tx'], x['li']) in seen:
                continue
            seen.add((x['tx'], x['li']))
            if x['mAsset'] == 'USDC':
                side, tok, px, usd = 'BUY', x['tAsset'], x['mAmt'] / x['tAmt'], x['mAmt']
            else:
                side, tok, px, usd = 'SELL', x['mAsset'], x['tAmt'] / x['mAmt'], x['tAmt']
            if tok not in ('Yes', 'No') or not (0 < px < 1):
                continue
            yeq = (side == 'BUY') == (tok == 'Yes')
            rows.append(dict(block=x['block'], li=x['li'], ts=x['ts'], tx=x['tx'], wallet=x['maker'].lower(), side=side, token=tok, price=px, usd=usd,
                             yes_eq_buy=yeq, p_yes=px if tok == 'Yes' else 1 - px))
    return pd.DataFrame(rows).sort_values(['block', 'li']).reset_index(drop=True)


def main(mad):
    os.chdir(mad)
    tl, buyers, bins = [], [], []
    queries = []
    data = {}
    for nom, c in CAS.items():
        E, R = agressifs(c['evt']), agressifs(c['ref'])
        ps = PS[c['titre']]
        E['bin'] = E.ts // 300 * 300
        R['bin'] = R.ts // 300 * 300
        rv = R[R.yes_eq_buy].groupby('bin').usd.sum().reindex(range(R.bin.min(), R.bin.max() + 300, 300), fill_value=0)
        p99, rmax = float(rv.quantile(0.99)), float(rv.max())
        g = E.groupby('bin').apply(lambda d: pd.Series(dict(vol_achat_yes_eq=d[d.yes_eq_buy].usd.sum(), vol_vente_yes_eq=d[~d.yes_eq_buy].usd.sum(),
                                                               n_acheteurs=d[d.yes_eq_buy].wallet.nunique(), vwap_p_yes=np.average(d.p_yes, weights=d.usd))), include_groups=False)
        g = g.reindex(range(E.bin.min(), E.bin.max() + 300, 300))
        g['vol_achat_yes_eq'] = g.vol_achat_yes_eq.fillna(0)
        g['depasse_P99_ref'] = g.vol_achat_yes_eq > p99
        for b, r in g.iterrows():
            bins.append(dict(marche=nom, tranche_utc=U(b), **r.to_dict(), P99_reference=p99))
        first_bin = g[g.depasse_P99_ref].index.min()
        big = R[R.yes_eq_buy].usd.quantile(0.99)
        fb = E[E.yes_eq_buy & (E.usd > big)]
        rep = ps['t_1p5x']
        tl += [dict(marche=nom, etape='fenêtre on-chain analysée', heure_utc=f'{U(E.ts.min())} -> {U(E.ts.max())}', source='fills OrderFilled phase 2 (bloc, logIndex)', niveau='MESURÉ',
                    detail=f'{len(E)} fills preneurs ; référence {len(R)} fills ({U(R.ts.min())} -> {U(R.ts.max())}), P99 5 min = {p99:,.0f} $, max = {rmax:,.0f} $'),
               dict(marche=nom, etape='prix de référence (médiane de l\'heure précédente)', heure_utc='', source='CLOB prices-history, phase 2', niveau='MESURÉ', detail=f"p_yes = {ps['base_median_prev_hour']}"),
               dict(marche=nom, etape='première tranche de 5 min au-dessus du P99 de référence', heure_utc=U(first_bin) if pd.notna(first_bin) else 'aucune', source='fills', niveau='MESURÉ',
                    detail=(f"volume {g.loc[first_bin,'vol_achat_yes_eq']:,.0f} $, {int(g.loc[first_bin,'n_acheteurs'])} acheteurs, p_yes {g.loc[first_bin,'vwap_p_yes']:.3f}" if pd.notna(first_bin) else '')),
               dict(marche=nom, etape=f'premier achat agressif YES-éq. > P99 des tailles de référence ({big:,.0f} $)', heure_utc=U(fb.ts.iloc[0]) if len(fb) else 'aucun', source='fills', niveau='MESURÉ',
                    detail=(f"{fb.usd.iloc[0]:,.0f} $ à p_yes {fb.p_yes.iloc[0]:.3f}, wallet {fb.wallet.iloc[0][:10]}" + (f" ({A[fb.wallet.iloc[0]]})" if fb.wallet.iloc[0] in A else '')) if len(fb) else ''),
               dict(marche=nom, etape='repricing (p_yes >= 1,5 x référence)', heure_utc=U(rep), source='CLOB à la minute, phase 2', niveau='MESURÉ', detail=''),
               dict(marche=nom, etape='p_yes >= 0,5', heure_utc=U(ps['t_ge_0p5']), source='CLOB à la minute, phase 2', niveau='MESURÉ', detail='')]
        for lab, h, src in c['non_public']:
            tl.append(dict(marche=nom, etape=lab, heure_utc=h + ':00', source=src, niveau='SOURCE SECONDAIRE', detail='non observable par le marché'))
        for lab, h, src in c['public']:
            tl.append(dict(marche=nom, etape=lab, heure_utc=h + ':00', source=src, niveau='SOURCE SECONDAIRE', detail=''))
        pre = E[E.yes_eq_buy & (E.ts < rep)]
        for r in pre.itertuples(index=False):
            queries.append((r.ts, nom, r.wallet, r.usd, r.p_yes, r.block, r.tx))
        data[nom] = (E, g, rep)
    # historique causal de chaque acheteur au moment de son achat : on rejoue le flux data-api jusqu'à T
    det = Detecteur(differe=True)
    P = pd.read_pickle('p9/prints.pkl')
    P = P[P.ts <= max(q[0] for q in queries)]
    queries.sort()
    cols = ['ts', 'cid', 'cat', 'end', 'wallet', 'side', 'asset', 'price', 'usd', 'oi', 'rid']
    arr = [P[c].values for c in cols]
    qi = 0
    for row in zip(*arr):
        while qi < len(queries) and queries[qi][0] < row[0]:
            t, nom, w, usd, py, blk, tx = queries[qi]
            det._resoudre(t)
            n, l = det.hist[w]
            hs = (l + 10 * det.p0) / (n + 10)
            buyers.append(dict(marche=nom, heure_utc=U(t), bloc=blk, tx=tx, wallet=w, compte_popA=A.get(w, ''), usd=round(usd, 2), p_yes=round(py, 4),
                               trades_anterieurs_univers=det.n_univ[w], hist_n=n, hist_lead=l, hist_score=round(hs, 4),
                               eligible_SIG_HIST=bool(n >= 5 and hs >= det.hthr)))
            qi += 1
        det.traiter(dict(zip(cols, row)))
        det.lignes = []
    B = pd.DataFrame(buyers)
    for nom, (E, g, rep) in data.items():
        b = B[B.marche == nom]
        tl.append(dict(marche=nom, etape='acheteurs agressifs YES-éq. avant repricing', heure_utc='', source='fills + état du détecteur à T', niveau='MESURÉ',
                       detail=f"{b.wallet.nunique()} wallets, {len(b)} fills, {b.usd.sum():,.0f} $ ; éligibles SIG_HIST : {b[b.eligible_SIG_HIST].wallet.nunique()} ; "
                              f"historique >= 5 événements : {b[b.hist_n >= 5].wallet.nunique()} ; population A : {', '.join(sorted(set(b.compte_popA) - {''})) or 'aucun'}"))
    # alertes du détecteur sur le marché Maduro (seul des deux dans l'univers data-api) avant le repricing
    AL = pd.read_csv(sys.argv[2]) if len(sys.argv) > 2 else None
    if AL is not None:
        cid = MK[CAS['Maduro']['titre']]['conditionId']
        rep = data['Maduro'][2]
        a = AL[(AL.market == cid) & (AL.ts >= rep - 6 * 3600) & (AL.ts < rep)]
        tl.append(dict(marche='Maduro', etape='alertes du détecteur dans les 6 h avant le repricing (flux data-api >= 100 $)', heure_utc=', '.join(U(t)[11:] for t in a.ts) or 'aucune',
                       source='p9_detector.py rejoué', niveau='MESURÉ',
                       detail='; '.join(f"{r.signals} {r.wallet[:10]} {r.usd:,.0f} $ p={r.p_before:.3f}" for r in a.itertuples()) or 'aucune alerte'))
        cidI = MK[CAS['Iran']['titre']]['conditionId']
        tl.append(dict(marche='Iran', etape='alertes du détecteur', heure_utc='', source='', niveau='INCONNU',
                       detail='marché hors univers de la phase 8 (aucun trade data-api collecté) ; seul l\'état des wallets (historique) est évalué'))
    pd.DataFrame(tl).to_csv(OUT + 'etude_cas_maduro_iran.csv', index=False)
    B.to_csv(OUT + 'etude_cas_acheteurs_avant_repricing.csv', index=False)
    pd.DataFrame(bins).to_csv(OUT + 'etude_cas_tranches_5min.csv', index=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 140)
    print(pd.DataFrame(tl)[['marche', 'etape', 'heure_utc', 'detail']].to_string())


if __name__ == '__main__':
    main(sys.argv[1])
