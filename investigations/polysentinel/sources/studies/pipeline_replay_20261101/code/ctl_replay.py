"""Synthetic controls of the whole replay path, run before any real score. Exit code 0 only if all pass.

Null stays silent, medium and strong fire where the rules say, and every tick matches a full
kernel call. Fixtures are synthetic: they prove the mechanics, not any detection power.
"""
import json
import os
import random
import shutil
import sys
import tempfile
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
import sim_core  # noqa: E402
from sim_core import Sim, SimTime, T_DEBUT, Store, pdb, pbridge, as_dict  # noqa: E402
import univers  # noqa: E402

CONFIG = json.loads((ETUDE / 'data/config_production.json').read_text())
HEX = '0123456789abcdef'
FIN = T_DEBUT + 6 * 3600


def addr(rng):
    return '0x' + ''.join(rng.choice(HEX) for _ in range(40))


def row(ts, wallet, token, buy, size, price, event, market, n, delay=60):
    key = event or 'unmapped:slug-' + token
    return (ts, ts + delay, wallet, token, buy, size, price, '0x' + f'{n:064x}', market, event, f'0xcond{token}', 'slug-' + token, '', 'Yes', f'id{n:08d}', key)


def meta(rows, closed_at=None):
    markets, events = {}, {}
    for r in rows:
        if r[9]:
            events.setdefault(r[9], [dict(id=r[9], title='t', slug='s', active=True, closed=False, tags=[], end_date=None, observed_at=T_DEBUT - 7200, raw={})])
            vs = [dict(id=r[8], event_id=r[9], condition_id=r[10], question='q', active=True, closed=False, tokens=[], end_date=None, liquidity=None, observed_at=T_DEBUT - 7200, raw={})]
            if closed_at:
                vs.append(dict(vs[0], closed=True, observed_at=closed_at))
            markets.setdefault(r[8], vs)
        else:
            events.setdefault(r[15], [dict(id=r[15], title='t', slug='s', active=True, closed=False, tags=[], end_date=None, observed_at=T_DEBUT - 7200, raw={})])
    return markets, events


def fond(rng, n=400):
    """Background retail: small rows on a few events, no rule should fire."""
    rows = []
    wallets = [addr(rng) for _ in range(60)]
    for i in range(n):
        ts = T_DEBUT + rng.randrange(0, FIN - T_DEBUT)
        event = str(rng.randrange(1, 6))
        rows.append(row(ts, rng.choice(wallets), event + '0', True, rng.uniform(1, 200), rng.uniform(.1, .9), event, 'm' + event, 1000 + i))
    return rows


def run_all_ticks(rows, markets, events, horizon=None):
    tmp = tempfile.mkdtemp(prefix='ctl_replay_')
    try:
        store = Store(tmp)
        clock = SimTime()
        pdb.time, pbridge.time = clock, clock
        sim = Sim('ctl', rows, markets, events, CONFIG, horizon, tmp)
        sim.tick = T_DEBUT
        count = 0
        while sim.tick < FIN:
            # Oracle at every tick: this is the equivalence proof for the fast path.
            sim.step(store, clock, oracle=True)
            count += 1
        store.close()
        return sim, count
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def controles():
    rapport = {}
    rng = random.Random(20261101)

    base = fond(random.Random(1))
    sim, ticks = run_all_ticks(base, *meta(base))
    assert not sim.queue, 'nul: priorité inattendue'
    rapport['nul'] = dict(lignes=len(base), ticks=ticks, oracles=sim.oracles, dossiers=len(sim.queue))

    # Medium: one concentrated large buyer, one family only: score 1, never a priority.
    w = addr(rng)
    medium = base + [row(T_DEBUT + 3600, w, '77', True, 4000, .5, '7', 'm7', 1)]
    sim, _ = run_all_ticks(medium, *meta(medium))
    assert not sim.queue and (w, '7') in sim.first_behavior, 'moyen'
    rapport['moyen'] = dict(comportement_a=sim.first_behavior[w, '7'][0] - T_DEBUT, dossiers=len(sim.queue))

    # Strong: baseline of 25 small buys, then a break: concentration + size shift, score 2.
    w2 = addr(rng)
    fort = list(base)
    for i in range(25):
        fort.append(row(T_DEBUT + 60 + 120 * i, w2, '88', True, 300, .5, '8', 'm8', 100 + i))
    t_break = T_DEBUT + 3 * 3600
    fort.append(row(t_break, w2, '88', True, 30000, .5, '8', 'm8', 500))
    sim, _ = run_all_ticks(fort, *meta(fort))
    entries = [q for q in sim.queue if q['wallet'] == w2]
    assert entries and entries[0]['score'] >= 2 and 'wallet_size_shift' in entries[0]['rules'], 'fort'
    assert t_break + 60 <= entries[0]['at'] <= t_break + 180, 'heure du fort'
    rapport['fort'] = dict(priorite_apres_rupture_s=entries[0]['at'] - t_break, regles=entries[0]['rules'], rang=entries[0]['rank_tick'])

    # A market that closes before the break must block the priority, as in production.
    sim, _ = run_all_ticks(fort, *meta(fort, closed_at=t_break - 600))
    assert not [q for q in sim.queue if q['wallet'] == w2], 'marché fermé'
    rapport['ferme'] = 'priorité bloquée'

    # Horizon: with a 1 h cap the baseline is gone, so the size shift cannot fire.
    sim, _ = run_all_ticks(fort, *meta(fort), horizon=3600)
    assert not [q for q in sim.queue if q['wallet'] == w2 and 'wallet_size_shift' in q['rules']], 'plafond'
    rapport['plafond'] = 'rupture invisible avec plafond de 1 h'

    # Synchrony: three wallets, 90 s, then expiry must re-evaluate partners (oracle checks every tick).
    a, b, c = addr(rng), addr(rng), addr(rng)
    sync = base + [row(T_DEBUT + 1000 + 30 * i, x, '99', True, 2500, .5, '9', 'm9', 700 + i) for i, x in enumerate((a, b, c))]
    sim, _ = run_all_ticks(sync, *meta(sync))
    assert any(q['wallet'] in (a, b, c) and 'synchronized_entries' in q['rules'] for q in sim.queue), 'synchronie'
    rapport['synchronie'] = 'détectée, trois wallets'

    # Late rows from the rotation change a baseline: oracle equality covers out-of-order arrival.
    tard = list(fort)
    tard = [r[:1] + (r[1] + (5400 if i % 3 == 0 else 0),) + r[2:] for i, r in enumerate(tard)]
    sim, _ = run_all_ticks(tard, *meta(tard))
    rapport['arrivees_tardives'] = dict(oracles=sim.oracles)

    # Unmapped event: M1 event, synthetic key, large exposure only.
    w3 = addr(rng)
    libre = base + [row(T_DEBUT + 1800, w3, '55', True, 9000, .5, '', '', 800)]
    sim, _ = run_all_ticks(libre, *meta(libre))
    assert (w3, 'unmapped:slug-55') in sim.first_behavior, 'non référencé'
    rapport['non_reference'] = 'clé unmapped conservée'

    # A due date passing must re-evaluate without any new row (oracle at every tick would raise otherwise).
    w4 = addr(rng)
    du = base + [row(T_DEBUT + 1800, w4, '66', True, 9000, .5, '6', 'm6', 900)]
    m_du, e_du = meta(du)
    for vs in (m_du['m6'], e_du['6']):
        for v in vs:
            v['end_date'] = T_DEBUT + 7200
    sim, _ = run_all_ticks(du, m_du, e_du)
    assert (w4, '6') in sim.first_behavior and sim.oracles['ok'] > 300, 'échéance'
    rapport['echeance'] = dict(oracles=sim.oracles)

    # A behaviour is dated at its first score of at least one, never at a weight-zero annotation.
    assert all(v[1] >= 1 for v in sim.first_behavior.values()), 'premier comportement'

    # Partial oracle: over the frame ceiling a closed sample of wallets is still compared.
    limite, sim_core.ORACLE_MAX_LIGNES = sim_core.ORACLE_MAX_LIGNES, 100
    try:
        sim, _ = run_all_ticks(fort, *meta(fort))
    finally:
        sim_core.ORACLE_MAX_LIGNES = limite
    assert sim.oracles['partiels'] > 0, 'oracle partiel'
    rapport['oracle_partiel'] = sim.oracles

    # Rotation arithmetic and what decides it.
    assert univers.visite(univers.T_ROT, 100, 7) == univers.T_ROT + 7
    assert univers.visite(univers.T_ROT + 8, 100, 7) == univers.T_ROT + 107
    marche_ouvert = lambda statut=None: {'createdAt': '2026-10-01T00:00:00Z', 'resolutionSource': 'https://example.org/results', **({'umaResolutionStatus': statut} if statut else {})}
    gamma = dict(id='1', title="Ballon d'Or Winner 2026", slug='ballon', createdAt='2026-10-01T00:00:00Z', endDate='2026-12-30T00:00:00Z', tags=[],
                 markets=[dict(id='2', conditionId='0x' + '1' * 64, question="Will X win the Ballon d'Or?", clobTokenIds='["1","2"]', outcomes='["Yes","No"]', endDate='2026-12-30T00:00:00Z', **marche_ouvert('resolved'))])
    u = univers.Univers()
    u.ajoute_gamma(gamma, 'family')
    assert 'umaResolutionStatus' not in u.markets['2'][0]['raw'], 'statut de résolution présent dans la version ouverte'
    univers.regles(neutre=False)
    assert univers.rotation(u, '2')[0] == univers.RAPIDE, 'littéral de production'
    univers.regles(neutre=True)
    assert univers.rotation(u, '2')[0] == univers.LENT, 'règle neutre'
    rapport['rotation'] = 'visites correctes ; un marché résolu plus tard garde sa période ; le littéral est isolé dans S_L'

    # Every scenario but S_C shares one history floor: a pre-T_DEBUT sampled row stays out.
    u.ajoute_ligne(dict(id='a:1', wallet='0x' + 'a' * 40, condition_id='0x' + '1' * 64, token_id='1', side='BUY', size=4000, price=.5, timestamp=T_DEBUT - 5000, transaction_hash='0x' + 'b' * 64, event_slug='ballon'), univers.FAMILY)
    assert not list(univers.scenario_lignes(u, 'S_A', 2500)) and not list(univers.scenario_lignes(u, 'S_B', 2500)) and not list(univers.scenario_lignes(u, 'S_G', 2500))
    assert list(univers.scenario_lignes(u, 'S_C', 2500))
    univers.regles(neutre=True)
    rapport['plancher_historique'] = 'identique sauf S_C'

    # Identity fields never survive collection.
    sys.path.insert(0, str(ETUDE / 'code'))
    import col_global
    clean = col_global.minimal(dict(proxy_wallet='0x', name='alias', pseudonym='alias', bio='b', icon='i', profile_image='p', profile_image_optimized='p', title='t'))
    assert not {'name', 'pseudonym', 'bio', 'icon', 'profile_image', 'profile_image_optimized'} & set(clean)
    rapport['aveugle'] = 'champs d’identité retirés'
    return rapport


def main():
    rapport = controles()
    sortie = ETUDE / 'controles/ctl_replay.json'
    sortie.write_text(json.dumps(rapport, indent=1, sort_keys=True))
    from registre import enregistrer
    enregistrer(str(ETUDE), 'ctl_replay', False, len(rapport), 'claude', donnees='synthetiques', n_comparaisons=len(rapport), sortie='controles/ctl_replay.json',
                note='Contrôles synthétiques du rejeu ; aucune puissance réelle')
    print(json.dumps(rapport, indent=0))


if __name__ == '__main__':
    main()
