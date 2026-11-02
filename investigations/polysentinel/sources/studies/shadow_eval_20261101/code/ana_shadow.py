"""Shadow engine over the pilot's reference rows, in a private store. Usage: ana_shadow.py propre|injection"""
import gc
import gzip
import hashlib
import json
import os
import resource
import signal
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
RACINE = ETUDE.parent.parent
REJEU = ETUDE.parent / 'pipeline_replay_20261101'
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(REJEU / 'code'))
sys.path.insert(0, str(ETUDE / 'code'))

from shadow import moteur  # noqa: E402
from charge import charge  # noqa: E402
from univers import scenario_lignes, instant  # noqa: E402
from sim_core import T_DEBUT, T_ALERTES, T_FIN  # noqa: E402

GRILLE = 300
BAC = Path(os.environ.get('PS_BAC', '/private/tmp/claude-501/-Users-benjamindacunha/ddbd5b1b-5e0b-4f3f-a192-c52d7c1360eb/scratchpad/bac')) / 'shadow'
MONTANTS = (2500, 5000, 10000, 25000, 50000, 100000)
arret = False


def demande_arret(*_):
    global arret
    arret = True


def motifs():
    """Synthetic events: their wallet and event keys start with inj and can never match a real row."""
    plan, lignes = [], []
    envol = (T_FIN - T_ALERTES - 3 * 86400)
    n = 0
    for i, (nb_wallets, repetitions) in enumerate(((3, 6), (1, 3))):
        for rep in range(repetitions):
            for montant in MONTANTS:
                debut = T_ALERTES + 86400 + int(envol * (n + .5) / 54)
                ek = f'inj:{n}'
                plan.append(dict(id=n, ek=ek, wallets=nb_wallets, montant=montant, debut=debut))
                for k in range(nb_wallets):
                    ts = debut + 400 * k
                    lignes.append(dict(cle=f'inj{n}:{k}', w=f'0xinj{n}w{k}', ts=ts, obs=ts + 60, ek=ek, mid=f'cond:inj{n}', cid=f'inj{n}', tok=f'tokinj{n}', buy=True,
                                       size=montant / .2, prix=.2, tx=f'0xinj{n}t{k}'))
                n += 1
    return plan, lignes


def main():
    passe = sys.argv[1]
    if passe not in ('propre', 'injection'):
        raise SystemExit('propre ou injection')
    signal.signal(signal.SIGTERM, demande_arret)
    BAC.mkdir(parents=True, exist_ok=True)
    chemin = BAC / f'{passe}.sqlite3'
    for suffixe in ('', '-wal', '-shm'):
        Path(str(chemin) + suffixe).unlink(missing_ok=True)
    config = moteur.charge_config()
    etat = moteur.Etat(chemin)
    filtre = json.loads((REJEU / 'data/global_state.json').read_text())['filtre']
    u = charge()
    source = sorted(scenario_lignes(u, 'S_A', filtre), key=lambda r: (r[1], r[14]))
    # Row tuple order is sim_core's: TS, OBS, W, TOKEN, BUY, SIZE, PRICE, TX, MARKET, EVENT, COND, SLUG, MSLUG, OUTCOME, ID, EK.
    catalogues = {}
    for mid, versions in u.markets.items():
        ouverte = versions[0]
        fin = instant(ouverte.get('end_date'))
        fermeture = next((v['observed_at'] for v in versions if v.get('closed')), None)
        catalogues[ouverte['condition_id'].lower()] = (ouverte.get('question'), mid, ouverte['event_id'], min(x for x in (fin, fermeture, float('inf')) if x is not None), ouverte.get('raw'))
    vues = set()
    for r in source:
        cid = r[10]
        if cid not in vues:
            vues.add(cid)
            c = catalogues.get(cid)
            if c:
                etat.marche(cid, c[0], c[2], c[1], None if c[3] == float('inf') else c[3], c[4])
            else:
                etat.marche(cid, u.titres.get(cid), r[15], r[8])
    plan_inj, lignes_inj = ([], [])
    if passe == 'injection':
        plan_inj, lignes_inj = motifs()
        for m in plan_inj:
            etat.marche(f"inj{m['id']}", 'Will the synthetic announcement happen?', m['ek'], f"cond:inj{m['id']}", T_FIN + 30 * 86400)
    entree = dict(lignes=len(source), comptes=u.comptes, plan_sha256=hashlib.sha256((ETUDE / 'analysis_plan.md').read_bytes()).hexdigest(),
                  config_sha256=hashlib.sha256(Path(moteur.__file__).with_name('config.json').read_bytes()).hexdigest(), moteur_sha256=hashlib.sha256(Path(moteur.__file__).read_bytes()).hexdigest())
    del u, catalogues, vues
    gc.collect()
    arrivees = sorted(lignes_inj, key=lambda r: r['obs'])
    i = j = 0
    niveaux = Counter()
    par_jour = defaultdict(Counter)
    familles_compte = Counter()
    paires_total = sans_comparateur = 0
    priorites_jour = Counter()
    emissions = []
    inj_resultat = {m['ek']: dict(m, niveau_max=0, premier_dossier=None, familles=[]) for m in plan_inj}
    debut_exec = time.time()
    for tick in range(T_DEBUT, T_FIN, GRILLE):
        lot = []
        while i < len(source) and source[i][1] <= tick:
            r = source[i]
            lot.append(dict(cle=r[14], w=r[2], ts=r[0], obs=r[1], ek=r[15], mid=r[8], cid=r[10], tok=r[3], buy=r[4], size=r[5], prix=r[6], tx=r[7]))
            i += 1
        while j < len(arrivees) and arrivees[j]['obs'] <= tick:
            lot.append(arrivees[j])
            j += 1
        if lot:
            touchees = etat.ajoute(lot)
            sorties, bilan = moteur.cycle(etat, touchees, tick, config, emettre=tick >= T_ALERTES)
            paires_total += bilan['paires']
            sans_comparateur += bilan['sans_comparateur']
            jour = str(tick // 86400)
            moteur.budget_priorites([s for s in sorties if s['nature'] == 'discret' and not s['event'].startswith('inj:')], priorites_jour[jour], config)
            for s in sorties:
                familles = Counter(f for p in s['paires'] for f in p['familles'])
                reel = not s['event'].startswith('inj:')
                if reel:
                    niveaux[s['niveau']] += 1
                    par_jour[jour][(s['nature'], s['niveau'])] += 1
                    if s['niveau'] == 3 and s.get('niveau_avant') != 3:
                        priorites_jour[jour] += 1
                    familles_compte.update(familles)
                    emissions.append(dict(event=s['event'], titre=s.get('titre'), at=s['at'], version=s['version'], niveau=s['niveau'], nature=s['nature'], retrograde=s.get('retrograde'), m1=s['event'].startswith('unmapped:'),
                                          wallets=[p['wallet'] for p in s['paires']], familles=familles, convergence=len(s['collectif']['convergence']), montants=len(s['collectif']['montants_identiques'])))
                else:
                    res = inj_resultat[s['event']]
                    res['niveau_max'] = max(res['niveau_max'], s['niveau'])
                    res['premier_dossier'] = res['premier_dossier'] or s['at']
                    res['familles'] = sorted(set(res['familles']) | set(familles))
        if arret:
            print(json.dumps(dict(passe=passe, arret=True, tick=tick)))
            return 5
        if (tick - T_DEBUT) % (GRILLE * 288) == 0:
            print(json.dumps(dict(passe=passe, tick=tick, lignes=i, emis=len(emissions), rss_mo=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576), duree_s=round(time.time() - debut_exec))), flush=True)
    jours = (T_FIN - T_ALERTES) / 86400
    reobs = etat.cx.execute("SELECT SUM(reobservations) FROM dossiers WHERE ek NOT LIKE 'inj:%'").fetchone()[0] or 0
    sortie = dict(passe=passe, entree=entree, grille_s=GRILLE, niveaux=dict(niveaux), dossiers_niveau2plus_par_jour=(niveaux[2] + niveaux[3]) / jours,
                  par_jour={k: {f'{n}|{l}': c for (n, l), c in v.items()} for k, v in par_jour.items()}, familles=dict(familles_compte), paires_evaluees=paires_total, paires_sans_comparateur=sans_comparateur,
                  reobservations=reobs, emissions=emissions, injections=list(inj_resultat.values()), rss_max_mo=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576, duree_s=time.time() - debut_exec)
    destination = ETUDE / f'derived/{passe}.json.gz'
    with gzip.GzipFile(destination, 'wb', mtime=0) as f:
        f.write(json.dumps(sortie, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
    etat.cx.close()
    from registre import enregistrer
    enregistrer(str(ETUDE), f'shadow_{passe}', False, paires_total, 'claude', n_comparaisons=max(1, paires_total), sortie=str(destination.relative_to(ETUDE)), params=dict(grille=GRILLE), note='Exploratoire, conçu en connaissant l’affaire')
    print(json.dumps({k: sortie[k] for k in ('passe', 'niveaux', 'dossiers_niveau2plus_par_jour', 'familles', 'paires_evaluees', 'paires_sans_comparateur', 'reobservations', 'rss_max_mo', 'duree_s')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
