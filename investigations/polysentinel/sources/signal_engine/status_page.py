"""One page that says what is running, what is sealed and what is missing, with a state word for each.

An empty table is ambiguous, so every section names its state, including NO_VERIFIED_RESULT. A partial
result never appears as a detection, and this page shows no wallet address.
"""
import json
import re
import sqlite3
import subprocess
import time
from collections import Counter
from pathlib import Path

from polysentinel import reports

ROOT = Path(__file__).resolve().parent.parent
PAGE_NAME = 'etat-polysentinel.html'
REPLAY = 'studies/pipeline_replay_20261101'
SCENARIOS = ('S_A', 'S_C', 'S_G', 'S_B', 'S_L')
STALE = dict(collection=180, registry=900, shadow=900)
MODES = dict(normal='COLLECTION_ACTIVE', reduced='COLLECTION_REDUCED', paused='COLLECTION_PAUSED')


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def collection(root, now):
    beat = read_json(root / 'metrics/heartbeat.json')
    if not beat:
        return dict(state='COLLECTION_UNKNOWN', detail='Battement illisible.')
    age = now - beat.get('at', 0)
    latest = None
    try:
        cx = sqlite3.connect(f"file:{root / 'data/polysentinel.sqlite3'}?mode=ro", uri=True, timeout=2)
        latest = cx.execute('SELECT MAX(trade_time) FROM trade_index').fetchone()[0]
        cx.close()
    except sqlite3.Error:
        pass
    state = 'COLLECTION_STALE' if age > STALE['collection'] else MODES.get(beat.get('resource_mode'), 'COLLECTION_UNKNOWN')
    return dict(state=state, heartbeat_age_s=age, latest_trade_age_s=now - latest if latest else None, quota_gb=beat.get('quota_accounted_bytes', 0) / 1e9, free_gb=beat.get('free_bytes', 0) / 1e9, blockers=beat.get('resource_blockers') or [])


def registry(root, now):
    v2 = read_json(root / 'evidence/prospective_v2_status.json')
    if not v2:
        return dict(state='REGISTRY_UNKNOWN', detail='État du registre illisible.')
    age = now - (v2.get('last_sealed_at') or 0)
    return dict(state='REGISTRY_STALE' if age > STALE['registry'] else 'REGISTRY_ACTIVE', last_sealed_age_s=age, last_alert_sealed_age_s=now - (v2.get('last_alert_sealed_at') or 0), observations=v2.get('observation_count'), distinct_alerts=v2.get('distinct_alert_keys'),
                sealing_failures=v2.get('capture_failure_count'), continuity=v2.get('continuity'), used_gb=(v2.get('cap_bytes', 0) - v2.get('remaining_bytes', 0)) / 1e9 if v2.get('remaining_bytes') is not None else None)


def shadow(root, now):
    status = read_json(root / 'evidence/signal_engine_v1/status.json')
    if not status:
        return dict(state='SHADOW_NOT_RUN')
    age = now - status.get('at', 0)
    refused = (status.get('last_run') or {}).get('refused')
    state = 'SHADOW_ERROR' if status.get('error') else 'SHADOW_STALE' if age > STALE['shadow'] else 'SHADOW_REFUSED' if refused else 'SHADOW_ACTIVE'
    return dict(state=state, age_s=age, engine=status.get('engine'), refused=refused, error=status.get('error'), last_run=status.get('last_run'), cases_by_category=status.get('cases_by_category'), reviews_today=status.get('reviews_today'), continuous_market_cases_today=status.get('continuous_market_cases_today'))


def case_files(root):
    """Latest verdict per case version, from the sealed journal; an empty count says so."""
    counts, reviews = Counter(), 0
    try:
        with (root / 'evidence/signal_engine_v1/journal.jsonl').open() as f:
            for line in f:
                link = json.loads(line)
                if link['kind'] in ('case', 'enrichment'):
                    counts[link['content'].get('verification') or 'NOT_CHECKED_OLDER_VERSION'] += 1
                elif link['kind'] == 'notification':
                    reviews += 1
    except OSError:
        pass
    return dict(state='VERIFIED_CASES_PRESENT' if counts.get('PASS') else 'NO_VERIFIED_CASE', verification=dict(counts), notified=reviews)


def running_replay():
    """The interpreter running the script itself: a shell or a guard quoting its name does not count."""
    lines = subprocess.run(['/bin/ps', '-axo', 'command='], capture_output=True, text=True).stdout.splitlines()
    return any(re.match(r'^\S*[Pp]ython\S*\s+\S*code/ana_replay\.py\s+\S+\s*$', line) for line in lines)


def simulation(root, running):
    study = root / REPLAY
    if not study.exists():
        return dict(state='NO_SIMULATION', result='NO_VERIFIED_RESULT', finished=[], remaining=[])
    finished = [s for s in SCENARIOS if (study / f'derived/R1_{s}.json.gz').exists()]
    remaining = [s for s in SCENARIOS if s not in finished]
    sealed = (study / 'derived/pre_label_seal.json').exists()
    compared = (study / 'derived/R3_labels.json.gz').exists()
    if compared:
        state = 'SIMULATION_COMPARED'
    elif sealed:
        state = 'SIMULATION_SEALED'
    elif running:
        state = 'SIMULATION_RUNNING'
    elif remaining:
        state = 'SIMULATION_PAUSED'
    else:
        state = 'SIMULATION_FINISHED_NOT_SEALED'
    return dict(state=state, result='CONDITIONAL_REPLAY_COMPARED' if compared else 'NO_VERIFIED_RESULT', finished=finished, remaining=remaining, sealed=sealed)


def collect(root=ROOT, now=None, running=None):
    now = time.time() if now is None else now
    return dict(at=now, collection=collection(root, now), registry=registry(root, now), shadow=shadow(root, now), case_files=case_files(root), simulation=simulation(root, running_replay() if running is None else running))


def seconds(value):
    return '—' if value is None else f'{value:.0f} s' if value < 3600 else f'{value / 3600:.1f} h'


def row(title, state, detail):
    return f'<tr><td><strong>{reports.esc(title)}</strong></td><td><code>{reports.esc(state)}</code></td><td>{reports.esc(detail)}</td></tr>'


def html(s):
    c, r, h, d, m = s['collection'], s['registry'], s['shadow'], s['case_files'], s['simulation']
    body = f'<article><p>Relevé {reports.times(s["at"])}. Un dossier ou une alerte désigne un comportement à examiner : rien ici n’établit un délit d’initié, une identité ou un propriétaire commun.</p></article>'
    body += '<h2>Ce qui tourne</h2><div class="scroll"><table><tr><th>Composant</th><th>État</th><th>Détail</th></tr>'
    body += row('Collecte', c['state'], f"battement {seconds(c.get('heartbeat_age_s'))}, dernier trade {seconds(c.get('latest_trade_age_s'))}, quota {c.get('quota_gb', 0):.2f} Go, disque libre {c.get('free_gb', 0):.2f} Go" + (f", blocages : {len(c['blockers'])}" if c.get('blockers') else ''))
    body += row('Registre prospectif', r['state'], f"dernier scellement {seconds(r.get('last_sealed_age_s'))}, dernière alerte scellée {seconds(r.get('last_alert_sealed_age_s'))}, {r.get('observations')} observations, {r.get('distinct_alerts')} alertes distinctes, {r.get('sealing_failures')} échecs de scellement historiques, continuité {r.get('continuity')}")
    body += row('Moteur shadow', h['state'], f"{h.get('engine') or '—'}, dernier passage {seconds(h.get('age_s'))}" + (f", refus : {h['refused']}" if h.get('refused') else '') + (f", erreur : {h['error']}" if h.get('error') else ''))
    body += row('Simulation historique', m['state'], f"terminés : {', '.join(m['finished']) or 'aucun'} ; restants : {', '.join(m['remaining']) or 'aucun'}")
    body += '</table></div><h2>Ce qui est établi</h2><div class="scroll"><table><tr><th>Élément</th><th>État</th><th>Détail</th></tr>'
    body += row('Résultat de la simulation', m['result'], 'Rejeu conditionnel après scellement, jamais une détection historique réelle.' if m['result'] != 'NO_VERIFIED_RESULT' else 'Aucun résultat vérifié pour l’instant : ce n’est pas une absence de détection.')
    body += row('Résultats historiques scellés', 'SEALED' if m.get('sealed') else 'NOT_SEALED', 'Empreintes écrites avant toute comparaison aux comptes publics.' if m.get('sealed') else 'Pas de scellement : rien n’est comparable.')
    body += row('Dossiers du moteur shadow', d['state'], ', '.join(f'{k} : {v}' for k, v in sorted(d['verification'].items())) or 'Aucun dossier encore.')
    body += row('Notifications de revue', 'REVIEW_QUEUE' if d['notified'] else 'NO_REVIEW', f"{d['notified']} depuis le début ; catégories : {json.dumps(h.get('cases_by_category') or {}, ensure_ascii=False)}")
    body += row('Écartés de la revue', 'EXCLUDED_CONTINUOUS_MARKETS', f"{h.get('continuous_market_cases_today') or 0} dossiers aujourd’hui sur marchés continus, sans notification par construction.")
    body += row('Données insuffisantes', 'NO_COMPARATOR' if (h.get('last_run') or {}).get('no_comparator') else 'COMPARATORS_AVAILABLE', f"{(h.get('last_run') or {}).get('no_comparator', 0)} paires sans comparateur au dernier passage, sur {(h.get('last_run') or {}).get('pairs', 0)}.")
    body += '</table></div><p class="muted">Un processus actif ne prouve pas une collecte : voir l’âge du dernier trade. Ces états sont calculés à chaque passage du moteur shadow ; une page vieille de plus de dix minutes signifie que ce moteur ne tourne plus.</p>'
    return reports.page('État de PolySentinel', body, refresh=True)


def write(root=ROOT):
    state = collect(root)
    reports.atomic_write(root / 'reports' / PAGE_NAME, html(state))
    return state
