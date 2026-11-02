"""Turn the collected files into scenario rows and a time-stamped catalogue. No score logic here."""
import gzip
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code/vendor'))
sys.path.insert(0, str(ETUDE / 'code'))

from polysentinel import collect, priority  # noqa: E402
from sim_core import T_ROT, T_DEBUT, T_FIN  # noqa: E402

RAPIDE, LENT = 215 * 60, 14214 * 60  # measured queue rotation, see the plan
GLOBAL_DELAI = 60
RETARD_INITIAL = 3780
TAGS = ['awards', 'earnings', 'token-launch', 'nominations', 'economic-data', 'fed', 'science', 'business', 'politics', 'ipo', 'listings']
REJETS = {}
# umaResolutionStatus stays out: its present value says 'resolved', which is the future of the open version.
ATTRS_BRUTS = ('createdAt', 'closedTime', 'startDate', 'endDate', 'resolutionSource', 'sportsMarketType', 'gameId', 'negRisk', 'groupItemTitle')
_LITTERAL = "ballon d['’]or|"
_REGLES_PRODUCTION = list(priority._RULES)
_REGLES_NEUTRES = [(c, re.compile(p.pattern.replace(_LITTERAL, ''), p.flags)) if c == 'awards' else (c, p) for c, p in _REGLES_PRODUCTION]
if _REGLES_NEUTRES[0][1].pattern == _REGLES_PRODUCTION[0][1].pattern:
    raise RuntimeError('Le littéral postérieur à l’affaire n’a pas été retiré de la règle')


def regles(neutre):
    """The production rule names this very case and was written after it; the reference scenario drops that word."""
    priority._RULES = _REGLES_NEUTRES if neutre else _REGLES_PRODUCTION


def instant(value):
    if value in (None, ''):
        return None
    text = str(value).strip().replace('Z', '+00:00').replace(' ', 'T', 1)
    if text.endswith('+00'):
        text += ':00'
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp()


def _iter_gz(path):
    if not Path(path).exists():
        raise FileNotFoundError(path)
    with gzip.open(path, 'rt') as f:
        for line in f:
            yield json.loads(line)


def normalise_api(raw, occurrence):
    """Real production normaliser, with the occurrence counter of its walk."""
    row = collect.normalize_trade(raw, T_FIN + 10_000_000, {}, {}, occurrence)
    row.pop('raw')
    return row


def lignes_flux(path):
    """API-shaped file, newest first: occurrence counters reset when the timestamp changes."""
    counts, current = {}, None
    for raw in _iter_gz(path):
        ts = int(raw['timestamp'])
        if ts != current:
            counts, current = {}, ts
        try:
            probe = normalise_api(raw, 1)
        except collect.SourceError as exc:
            # Same quarantine as the production walk: rejected, counted, never silently absorbed.
            cle = Path(path).name + ': ' + str(exc)
            REJETS[cle] = REJETS.get(cle, 0) + 1
            continue
        counts[probe['signature']] = counts.get(probe['signature'], 0) + 1
        probe['id'] = f"{probe['signature']}:{counts[probe['signature']]}"
        probe['title'] = raw.get('title')
        yield probe


def versions_gamma(event, at_default):
    """Open and closed versions from one current Gamma event; title, tags, end date are present-day values."""
    base_event = collect.normalize_event(event, 0.0, TAGS)
    base_event['raw'] = {k: event.get(k) for k in ATTRS_BRUTS if event.get(k) is not None}
    t_event = instant(event.get('createdAt')) or at_default
    closed_event = instant(event.get('closedTime'))
    ev = [dict(base_event, active=True, closed=False, observed_at=t_event + 600, version=None)]
    if closed_event and closed_event <= T_FIN:
        ev.append(dict(base_event, active=True, closed=True, observed_at=closed_event, version=None))
    ms = {}
    for raw in event.get('markets', []):
        m = collect.normalize_market(raw, base_event, 0.0)
        m['raw'] = {k: raw.get(k) for k in ATTRS_BRUTS if raw.get(k) is not None}
        m['liquidity'] = None  # present-day liquidity must never reach the detector
        t_open = instant(raw.get('createdAt')) or t_event
        closed = instant(raw.get('closedTime'))
        vs = [dict(m, active=True, closed=False, observed_at=t_open + 600, version=None)]
        if closed and closed <= T_FIN:
            vs.append(dict(m, active=True, closed=True, observed_at=closed, version=None))
        ms[m['id']] = (m['condition_id'].lower(), vs)
    return base_event['id'], ev, ms


class Univers:
    def __init__(self):
        self.markets, self.events, self.by_condition = {}, {}, {}
        self.family_events, self.control_events = set(), set()
        self.rows = {}  # id -> compact fields; the only big structure here
        self.sources = {}
        self.titres = {}

    def ajoute_gamma(self, event, kind):
        eid, ev, ms = versions_gamma(event, T_ROT)
        self.events[eid] = ev
        for mid, (condition, vs) in ms.items():
            self.markets[mid] = vs
            self.by_condition[condition] = (mid, eid)
        (self.family_events if kind == 'family' else self.control_events).add(eid)

    def ajoute_ligne(self, row, source):
        identifiant = row['id']
        if identifiant in self.rows:
            self.sources[identifiant] |= source
            return
        condition = row['condition_id'].lower()
        mid, eid = self.by_condition.get(condition, (row.get('market_id') or '', row.get('event_id') or ''))
        # A market key per condition keeps the multi-market rule possible on events without catalogue.
        mid = mid or 'cond:' + condition
        slug = row.get('event_slug') or eid
        self.rows[identifiant] = (int(row['timestamp']), row['wallet'].lower(), sys.intern(str(row['token_id'])), row['side'] == 'BUY',
                                  float(row['size']), float(row['price']), row['transaction_hash'], sys.intern(mid), sys.intern(eid),
                                  sys.intern(condition), sys.intern(slug), sys.intern(row.get('market_slug') or ''), sys.intern(row.get('outcome') or ''))
        self.sources[identifiant] = source
        if row.get('title'):
            self.titres.setdefault(condition, row['title'])

    def synthetique(self, key, titre):
        # Hypothesis M1 of the plan: no metadata, so assumed open, flagged m1 in every output.
        if key not in self.events:
            self.events[key] = [dict(id=key, title=titre, slug=key.replace('unmapped:', ''), active=True, closed=False, tags=[],
                                     end_date=None, observed_at=T_ROT - 1, raw={}, hypothese='M1 sans métadonnée')]


CENSUS, FAMILY, CONTROL = 1, 2, 4
DEPUIS_DEBUT = ('S_G', 'S_A', 'S_B', 'S_L')


def rotation(u, market_id):
    """Real announcement_scope on the open version; returns (period, market open time)."""
    vs = u.markets.get(market_id)
    if not vs:
        return LENT, T_ROT
    market = vs[0]
    t = max(market['observed_at'], T_ROT)
    event = (u.events.get(market['event_id']) or [{}])[0]
    event = dict(event, observed_at=min(event.get('observed_at', t), t))
    scope = priority.announcement_scope(dict(market, observed_at=t), event, t)
    return (RAPIDE if scope['eligible'] else LENT), t


def visite(ts, period, phase):
    k = max(0, (ts - T_ROT - phase + period - 1) // period)
    return T_ROT + phase + k * period


def scenario_lignes(u, scenario, filtre, delai=GLOBAL_DELAI, ecartees=None):
    """Yield row tuples for sim_core, applying only the visibility the plan assigns to the scenario."""
    if scenario not in ('S_C', 'S_G', 'S_A', 'S_B', 'S_L'):
        raise ValueError(scenario)
    regles(neutre=scenario != 'S_L')
    ecartees = Counter() if ecartees is None else ecartees
    rotations = {}
    for identifiant, r in u.rows.items():
        ts, wallet, token, buy, size, price, tx, mid, eid, condition, slug, mslug, outcome = r
        source = u.sources[identifiant]
        nominal = size * price
        echantillon = bool(source & (FAMILY | CONTROL))
        obs = None
        # Same history floor everywhere the census takes part: it starts at T_DEBUT.
        if scenario in DEPUIS_DEBUT and ts < T_DEBUT:
            ecartees['avant_T_DEBUT'] += 1
            continue
        if scenario == 'S_C':
            obs = ts + delai if echantillon else None
            if obs is None:
                ecartees['hors_echantillon'] += 1
                continue
        elif scenario == 'S_G':
            if source & CENSUS or (echantillon and nominal >= filtre):
                obs = ts + delai
            else:
                ecartees['sous_le_filtre'] += 1
                continue
        else:
            if source & CENSUS or (echantillon and nominal >= 1000):
                obs = ts + delai
            elif echantillon:
                if mid not in rotations:
                    period, t_open = rotation(u, mid)
                    phase = int(hashlib.sha256(mid.encode()).hexdigest()[:12], 16) % period
                    rotations[mid] = (period, phase, visite(t_open, period, phase))
                period, phase, first = rotations[mid]
                if ts >= first - RETARD_INITIAL:
                    obs = visite(ts, period, phase)
                else:
                    ecartees['avant_premiere_visite'] += 1
                    continue
        if obs >= T_FIN:
            ecartees['vue_apres_T_FIN'] += 1
            continue
        key = eid or 'unmapped:' + (slug or condition)
        if not eid:
            u.synthetique(key, u.titres.get(condition))
        yield (ts, obs, wallet, token, buy, size, price, tx, mid, eid, condition, slug, mslug, outcome, identifiant, sys.intern(key))
