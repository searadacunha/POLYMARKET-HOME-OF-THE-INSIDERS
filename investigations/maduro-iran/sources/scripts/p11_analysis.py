#!/usr/bin/env python3
"""Phase 11 : agrégats (PROTOCOLE_P11 §3-§7) et chronologies Maduro / Iran (§8).
  --live    : à partir des sorties de p11_execution.py -> live_alerts.csv, execution_simulation.csv, latency_curve.csv, capacity_curve.csv,
              lead_time_distribution.csv, self_impact.csv, follower_impact.csv
  --cases   : Maduro et Iran sur les flux historiques complets de la phase 10 -> maduro_timeline.csv, iran_timeline.csv
Aucun résultat intermédiaire ne modifie une règle du protocole."""
import os, sys, json, argparse, collections
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW, OUT, DATA  # noqa: E402

WORK = os.path.join(RAW, 'travail')
NS = 10 ** 9
rng = np.random.default_rng(11)


def stats(x, pre=''):
    x = pd.Series(x).dropna()
    if not len(x):
        return {pre + 'n': 0}
    return {pre + 'n': len(x), pre + 'moyenne': x.mean(), pre + 'mediane': x.median(), pre + 'P10': x.quantile(.1), pre + 'P25': x.quantile(.25),
            pre + 'P75': x.quantile(.75), pre + 'P90': x.quantile(.9), pre + 'min': x.min(), pre + 'max': x.max(), pre + 'part_positive': (x > 0).mean()}


def boot(df, col='net', n=2000):
    x = df[['market', col]].dropna()
    if len(x) < 10:
        return np.nan, np.nan
    mk = x.market.values; v = x[col].values
    um = np.unique(mk); idx = {m: np.nonzero(mk == m)[0] for m in um}
    bs = [v[np.concatenate([idx[m] for m in rng.choice(um, len(um))])].mean() for _ in range(n)]
    return np.quantile(bs, .025), np.quantile(bs, .975)


def live():
    X = pd.read_pickle(os.path.join(WORK, 'exec_long.pkl'))          # pickle local produit par p11_execution.py
    EV = pd.read_csv(os.path.join(WORK, 'events.csv'))
    LT = pd.read_csv(os.path.join(WORK, 'lead_time_detail.csv'))
    fp = os.path.join(WORK, 'followers_detail.csv')
    FO = pd.read_csv(fp) if os.path.exists(fp) and os.path.getsize(fp) > 2 else pd.DataFrame()
    A = EV[EV.groupe == 'SIG_HIST'].merge(LT, on=['event_id', 'groupe', 'market', 'wallet', 'usd'], how='left', suffixes=('', '_lt'))
    A.to_csv(os.path.join(OUT, 'live_alerts.csv'), index=False)
    rows = []
    for key, g in X[X.carnet == True].groupby(['groupe', 'L', 'S', 'H'], dropna=False):  # noqa: E712
        n_ev = EV[EV.groupe == key[0]].shape[0]
        ok = g[g.get('sortie', False) == True] if 'sortie' in g else g.iloc[0:0]  # noqa: E712
        r = dict(groupe=key[0], latence_s=key[1], taille_usd=key[2], sortie_s=key[3], n_evenements=n_ev, n_carnet=g.event_id.nunique(),
                 taux_remplissage_moy=g.taux_remplissage.mean(), part_remplissage_complet=(g.taux_remplissage >= 0.999).mean(),
                 VWAP_moy=g.VWAP_EXECUTION.mean(), slippage_vs_mid_moy=g.SLIPPAGE_VS_MID.mean(), spread_moy=g.spread.mean(),
                 frais_moy_pct=((g.frais_entree + g.get('frais_sortie', 0)) / g.rempli_usd).mean() if len(g) else np.nan,
                 MAE_moy=ok.MAE.mean() if len(ok) else np.nan, MFE_moy=ok.MFE.mean() if len(ok) else np.nan)
        r.update(stats(ok.brut if len(ok) else [], 'brut_'))
        r.update(stats(ok.net if len(ok) else [], 'net_'))
        if key[2] == 500 and len(ok):
            r['net_ic_lo'], r['net_ic_hi'] = boot(ok)
        rows.append(r)
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(OUT, 'execution_simulation.csv'), index=False)
    S[(S.taille_usd == 500) & (S.sortie_s == 300)].to_csv(os.path.join(OUT, 'latency_curve.csv'), index=False)
    cap = S[(S.latence_s == 0) & (S.sortie_s == 300)].copy()
    cap['statut'] = np.where(cap.n_carnet == 0, 'UNOBSERVABLE', 'mesuré')
    cap.to_csv(os.path.join(OUT, 'capacity_curve.csv'), index=False)
    # délais d'avance
    lt = []
    for g, x in LT.groupby('groupe'):
        for c in ('retard_T_obs_s', 'lt_ask_s', 'lt_mid_0.5pt_s', 'lt_mid_1pt_s', 'lt_mid_3pt_s'):
            if c in x:
                d = stats(x[c]); d.update(groupe=g, mesure=c, n_evenements=len(x), part_atteinte=x[c].notna().mean())
                lt.append(d)
        for ref in ('T0', 'Tobs'):
            prev = None
            for off in (0.25, 0.5, 1, 2, 3, 5):
                ca, cm = f'ask_{ref}+{off}s', f'mid_{ref}+{off}s'
                if ca in x and 'ask0' in x:
                    d = stats(x[ca] - x.ask0); d.update(groupe=g, mesure=f'ask({ref}+{off}s) - ask avant le trade')
                    lt.append(d)
                    d = stats(x[cm] - x.mid0); d.update(groupe=g, mesure=f'mid({ref}+{off}s) - mid avant le trade')
                    lt.append(d)
    pd.DataFrame(lt).to_csv(os.path.join(OUT, 'lead_time_distribution.csv'), index=False)
    # impact propre
    LT['SELF_IMPACT'] = np.where(LT.IMMEDIATE_IMPACT.isna(), 'INCONNU',
                                 np.where((LT.IMMEDIATE_IMPACT <= 0.005) & (LT.part_profondeur_2pt <= 0.5), 'LOW_SELF_IMPACT', 'HIGH_SELF_IMPACT'))
    prim = X[(X.L == 0) & (X.S == 500) & (X.H == 300)][['event_id', 'net', 'brut']]
    si = LT.merge(prim, on='event_id', how='left')
    rows = []
    for (g, c), x in si.groupby(['groupe', 'SELF_IMPACT']):
        r = dict(groupe=g, classe=c, n=len(x), impact_moy=x.IMMEDIATE_IMPACT.mean(), part_profondeur_moy=x.part_profondeur_2pt.mean(),
                 lt_mid_1pt_med=x.get('lt_mid_1pt_s', pd.Series(dtype=float)).median(), part_mid_1pt=x.get('lt_mid_1pt_s', pd.Series(dtype=float)).notna().mean())
        r.update(stats(x.net, 'net_'))
        rows.append(r)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'self_impact.csv'), index=False)
    # suiveurs et mécanisme
    rows = []
    if len(FO):
        for (ge, gs, sens), x in FO.groupby(['groupe', 'groupe_suiveur', 'sens']):
            n_ev = EV[EV.groupe == ge].shape[0]
            per = x.groupby('event_id').agg(n=('wallet', 'nunique'), vol=('usd', 'sum'), d=('delai_s', 'median'))
            rows.append(dict(groupe=ge, suiveur=gs, sens=sens, part_evenements=len(per) / max(n_ev, 1), wallets_moy=per.n.mean(), volume_moy=per.vol.mean(),
                             delai_median_s=x.delai_s.median(), delai_P25_s=x.delai_s.quantile(.25)))
    MECH = os.path.join(WORK, 'mechanism.csv')
    if os.path.exists(MECH) and os.path.getsize(MECH) > 2:
        M = pd.read_csv(MECH)
        for (g, H), x in M.groupby(['groupe', 'H']):
            r = dict(groupe=g, suiveur='DÉCOMPOSITION DU MID', sens=f'T0 -> T0 + {H} s', n=len(x), variation_mid_moy=x.variation_mid.mean())
            for c in ('SELF_IMPACT', 'KNOWN_FOLLOWER_IMPACT', 'UNKNOWN_TRADER_IMPACT', 'QUOTES'):
                r[c + '_moy'] = x[c].mean()
            rows.append(r)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'follower_impact.csv'), index=False)
    print(S[(S.taille_usd == 500) & (S.sortie_s == 300)][['groupe', 'latence_s', 'n_carnet', 'part_remplissage_complet', 'slippage_vs_mid_moy', 'net_n', 'net_moyenne', 'net_mediane']].round(4).to_string())


# ------------------------------------------------------------------ cas historiques (flux complet de la phase 10)
A8 = {'0x168b100d7a6620a2f49a455344c2c006eaf1714b': 'Chiwawas', '0x5621116629c5d640c8186f577362478cc6605245': 'TacticalInsiderNews',
      '0x38745db27f7360a287f6ca3c9b6a6a9c76149801': 'Planktonbets', '0x60280beffdfeaf962de4e6397ab49ed05a1b99e1': 'X34',
      '0x834079f62fa9b4b0bdfad5b8b7a841e8267da024': 'chileno777', '0xbf32f7a77ccea8bba647fea63d438ce1778b1762': '154x838hjd6',
      '0x56efadc9defe5b7a21af751e0d026f2cf54136db': 'Neodbs', '0xe9b80c387ba77a585423b13c850c2e126c3befd8': 'Mrs.Joker'}


def case(name, tape, t_start, t_end, public, alerts_csv):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from p10_impact import load_tape
    os.chdir(DATA)
    T = load_tape(tape, 0)                      # direction YES
    T = T[(T.ts >= t_start) & (T.ts <= t_end)].reset_index(drop=True)
    P = pd.read_pickle(os.path.join(DATA, 'p9', 'prints.pkl'))   # historique >= 100 $ (pickle local)
    first_seen = P.groupby('wallet').ts.min()
    n_prior = P.groupby('wallet').size()
    TL = pd.read_csv(alerts_csv)
    al = TL[TL.etape.str.startswith('alerte détecteur') & (TL.marche == name)]
    rows = []
    prev_p = None
    for i, r in T.iterrows():
        lv = sorted(r.lv, key=lambda z: z[0]) if r.ae else sorted(r.lv, key=lambda z: -z[0])
        marg = lv[-1][0] if lv else r.pd
        impact = (marg - prev_p) if prev_p is not None else np.nan
        nxt = T.iloc[i + 1:]
        nxt = nxt[(nxt.ts <= r.ts + 600) & (nxt.wallet != r.wallet)]
        fol = nxt[nxt.ae == r.ae]
        sig = al[al.heure_utc == pd.to_datetime(r.ts, unit='s', utc=True).strftime('%Y-%m-%d %H:%M:%S')]
        sig = sig[sig.detail.str.startswith(r.wallet[:10])]
        rows.append(dict(heure_utc=pd.to_datetime(r.ts, unit='s', utc=True).strftime('%Y-%m-%d %H:%M:%S'), ts=int(r.ts), seq=int(r.seq), wallet=r.wallet,
                         compte_A=A8.get(r.wallet, ''), sens='achat YES-éq.' if r.ae else 'vente YES-éq.', usd=round(r.usd, 2), p_yes=round(r.pd, 4),
                         niveaux=len(lv), self_impact=None if pd.isna(impact) else round(impact, 4), acheteurs_meme_sens_600s=fol.wallet.nunique(),
                         volume_meme_sens_600s=round(fol.usd.sum(), 2), p_yes_600s=round(float(nxt.pd.iloc[-1]), 4) if len(nxt) else None,
                         trades_anterieurs_univers=int(n_prior.get(r.wallet, 0)), premier_trade_univers=str(pd.to_datetime(first_seen.get(r.wallet), unit='s')) if r.wallet in first_seen else 'jamais (>= 100 $)',
                         signal=sig.etape.iloc[0].replace('alerte détecteur ', '') if len(sig) else '', tx=r.tx))
        prev_p = r.pd
    D = pd.DataFrame(rows)
    ev = pd.DataFrame([dict(heure_utc=h + ':00', ts=int(pd.Timestamp(h, tz='UTC').timestamp()), evenement=lab, niveau=niv, source=src) for lab, h, niv, src in public])
    return D, ev


def cases():
    TLP = os.path.join(os.path.dirname(OUT), 'phase10', 'maduro_iran_timeline.csv')
    mad_pub = [('ordre de lancement donné par Trump (non public à l\'époque)', '2026-01-03 03:46', 'APPROXIMATE', 'Wikipedia : « 22:46 EST on 2 January »'),
               ('premières explosions signalées à Caracas', '2026-01-03 06:00', 'APPROXIMATE', 'Wikipedia : « around 02:00 VET »'),
               ('annonce de la capture par Trump (Truth Social)', '2026-01-03 09:21', 'APPROXIMATE', 'Wikipedia : « 05:21 VET / 04:21 ET »')]
    ir_pub = [('autorisation des frappes (non publique à l\'époque)', '2026-02-27 20:38', 'APPROXIMATE', 'Wikipedia : « 3:38 p.m. EST »'),
              ('début des frappes', '2026-02-28 06:15', 'APPROXIMATE', 'Wikipedia : « around 9:45 a.m. IRST »'),
              ('annonce d\'Israël (Katz) et sirènes', '2026-02-28 06:23', 'VERIFIED', 'Times of Israel, entrée de liveblog horodatée 8:23 IST')]
    t = lambda s: int(pd.Timestamp(s, tz='UTC').timestamp())
    D, ev = case('Maduro', 'EVT_MADURO', t('2026-01-03 01:00'), t('2026-01-03 09:30'), mad_pub, TLP)
    out = pd.concat([D.assign(type='trade'), ev.assign(type='événement public')]).sort_values(['ts', 'seq'], na_position='last')
    out.to_csv(os.path.join(OUT, 'maduro_timeline.csv'), index=False)
    D2, ev2 = case('Iran', 'EVT_IRAN', t('2026-02-27 12:00'), t('2026-02-28 07:00'), ir_pub, TLP)
    out2 = pd.concat([D2.assign(type='trade'), ev2.assign(type='événement public')]).sort_values(['ts', 'seq'], na_position='last')
    out2.to_csv(os.path.join(OUT, 'iran_timeline.csv'), index=False)
    return D, D2


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--cases', action='store_true')
    a = ap.parse_args()
    if a.cases:
        cases()
    if a.live:
        live()
