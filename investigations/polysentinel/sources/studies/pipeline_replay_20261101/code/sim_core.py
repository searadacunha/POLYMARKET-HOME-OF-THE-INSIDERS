"""Chronological replay around the frozen detector, one simulated minute at a time.

The kernel is polysentinel.signals.evaluate, called unchanged on the wallets a tick can change.
Rows stay compact tuples and only become dicts for the wallets being evaluated, which is what
keeps the process under the pilot's memory ceiling. Fixed oracle ticks compare the incremental
state with one full kernel call; a difference stops the run.
"""
import gzip
import hashlib
import heapq
import json
import os
import pickle
import resource
import signal
import sys
import time as real_time
from bisect import bisect_left, bisect_right, insort
from collections import Counter, defaultdict
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code/vendor'))

from polysentinel import db as pdb, prospective_bridge as pbridge  # noqa: E402
from polysentinel import signals, reports, review  # noqa: E402
from polysentinel.db import Store  # noqa: E402
from polysentinel.engine import material  # noqa: E402

NOYAU_SHA = '45d1a5c0c109c573c4057269fb1783f768fc41da3973bb73d7e17a29b78ded90'
T_ROT, T_DEBUT, T_ALERTES, T_FIN = 1790176669, 1791691200, 1791849600, 1792768669
ORACLE_MAX_LIGNES = 25000
ORACLES = 64
LOT_LIGNES = 3000
# Row tuple positions.
TS, OBS, W, TOKEN, BUY, SIZE, PRICE, TX, MARKET, EVENT, COND, SLUG, MSLUG, OUTCOME, ID, EK = range(16)


def verifie_noyau():
    if hashlib.sha256(Path(signals.__file__).read_bytes()).hexdigest() != NOYAU_SHA:
        raise RuntimeError('Noyau différent de la version gelée')


class SimTime:
    """Stands in for the time module in the production modules that stamp writes."""
    def __init__(self):
        self.now = float(T_DEBUT)
        self.n = 0

    def time(self):
        return self.now

    def time_ns(self):
        self.n += 1
        return int(self.now * 1e9) + self.n


def as_dict(r):
    return dict(id=r[ID], wallet=r[W], token_id=r[TOKEN], side='BUY' if r[BUY] else 'SELL', size=r[SIZE], price=r[PRICE],
                nominal=r[SIZE] * r[PRICE], timestamp=r[TS], observed_at=r[OBS], transaction_hash=r[TX], market_id=r[MARKET],
                event_id=r[EVENT], condition_id=r[COND], event_slug=r[SLUG], market_slug=r[MSLUG], outcome=r[OUTCOME],
                fee=None, order_hash=None)


class Sim:
    """State is plain containers so that one pickle restores a run after a clean stop."""

    def __init__(self, name, rows, markets, events, config, horizon, root, grid=60, screen=True):
        verifie_noyau()
        self.name, self.config, self.horizon, self.root, self.grid, self.screen = name, config, horizon, root, grid, screen
        self.pending = sorted(rows, key=lambda r: (r[OBS], r[ID]))  # (obs, id) is stable across runs
        self.i = 0
        self.by_wallet = defaultdict(list)
        self.first_ts = {}
        self.sync = defaultdict(list)
        self.expiry = []  # (expires_at, wallet, event_key, is_recent_marker)
        self.prune = []  # (leaves_frame_at, wallet)
        self.recent_pairs = Counter()
        self.scores = Counter()
        self.current = defaultdict(dict)  # wallet -> event_key -> (score, priority, fingerprint)
        self.event_wallets = defaultdict(set)
        self.first_priority = {}
        self.first_behavior = {}
        self.queue = []
        self.reobservations = Counter()
        self.daily_new = Counter()
        self.max_score = {}
        self.comparisons = 0
        self.kernel_calls = 0
        self.kernel_rows = 0
        self.oracles = dict(ok=0, partiels=0, wallets_partiels=0, sautes=0, ecart_denominateur=0)
        self.tick = T_DEBUT
        self.markets = markets  # market_id -> versions ordered by observed_at
        self.events = events  # event_key -> versions
        # A passing due date changes the kernel's answer without any new row or version.
        echeances = lambda vs: {t for t in (signals.epoch(v.get('end_date')) for v in vs) if t is not None and T_DEBUT <= t <= T_FIN}
        self.meta_times = sorted({(float(v['observed_at']), 'm', key) for key, vs in markets.items() for v in vs} |
                                 {(float(v['observed_at']), 'e', key) for key, vs in events.items() for v in vs} |
                                 {(t, 'm', key) for key, vs in markets.items() for t in echeances(vs)} |
                                 {(t, 'e', key) for key, vs in events.items() for t in echeances(vs)})
        self.meta_i = 0
        self.dossiers = 0
        self.done = False

    # ---- ingestion -------------------------------------------------------------------------
    def _arrive(self, r, affected):
        w = r[W]
        self.by_wallet[w].append(r)
        self.first_ts[w] = min(self.first_ts.get(w, r[TS]), r[TS])
        self.event_wallets[r[EK]].add(w)
        if self.horizon:
            heapq.heappush(self.prune, (r[TS] + self.horizon, w))
        affected.add(w)  # a late old row can still change a baseline
        if r[TS] + 86400 >= self.tick:
            heapq.heappush(self.expiry, (r[TS] + 86400, w, r[EK], r[BUY]))
            if r[BUY]:
                self.recent_pairs[w, r[EK]] += 1
                insort(self.sync[r[TOKEN]], (r[TS], w))

    def _frame(self, w):
        rows = self.by_wallet.get(w, ())
        return [r for r in rows if r[TS] >= self.tick - self.horizon] if self.horizon else list(rows)

    def _neighbors(self, w, now):
        found = set()
        for r in self.by_wallet.get(w, ()):
            if r[BUY] and r[TS] >= now - 86400 - 180:  # a partner's expiry can break this wallet's cluster
                values = self.sync.get(r[TOKEN], ())
                lo = bisect_left(values, (r[TS] - 90,))
                hi = bisect_right(values, (r[TS] + 90, '￿'))
                found.update(x for _, x in values[lo:hi])
        return found

    def _can_signal(self, w, now):
        """No rule can fire without 250 of recent BUY nominal on one event; the oracle checks this."""
        spent = defaultdict(float)
        for r in self.by_wallet.get(w, ()):
            if r[BUY] and r[TS] >= now - 86400:
                spent[r[EK]] += r[SIZE] * r[PRICE]
        return any(v >= 250 for v in spent.values())

    def _meta_for(self, rows, now):
        ms, es = [], []
        for key in {r[MARKET] for r in rows if r[MARKET]}:
            ms.extend(v for v in self.markets.get(key, ()) if v['observed_at'] <= now)
        for key in {r[EK] for r in rows}:
            es.extend(v for v in self.events.get(key, ()) if v['observed_at'] <= now)
        return ms, es

    def _kernel(self, rows, now):
        rows = sorted(rows, key=lambda r: (r[TS], r[ID]))
        markets, events = self._meta_for(rows, now)
        # Evaluate stores metadata under g['event_id']; unmapped events carry their synthetic key.
        hist = {w: dict(first_timestamp=self.first_ts[w], observations=0) for w in {r[W] for r in rows}}
        return signals.evaluate([as_dict(r) for r in rows], markets, events, now=now, config=self.config, wallet_history=hist)

    # ---- one simulated minute -------------------------------------------------------------
    def step(self, store, clock, oracle=False):
        now = self.tick
        clock.now = float(now)
        affected = set()
        while self.i < len(self.pending) and self.pending[self.i][OBS] <= now:
            self._arrive(self.pending[self.i], affected)
            self.i += 1
        while self.prune and self.prune[0][0] < now:
            _, w = heapq.heappop(self.prune)
            self.by_wallet[w] = self._frame(w)
            affected.add(w)
        while self.expiry and self.expiry[0][0] < now:
            _, w, ek, buy = heapq.heappop(self.expiry)
            if buy:
                self.recent_pairs[w, ek] -= 1
                if self.recent_pairs[w, ek] <= 0:
                    del self.recent_pairs[w, ek]
            affected.add(w)
        while self.meta_i < len(self.meta_times) and self.meta_times[self.meta_i][0] <= now:
            _, kind, key = self.meta_times[self.meta_i]
            self.meta_i += 1
            for ek in ([key] if kind == 'e' else {v['event_id'] for v in self.markets.get(key, ())}):
                affected.update(self.event_wallets.get(ek, ()))
        if affected:
            self._evaluate(affected, now, store)
        if oracle:
            self._oracle(now)
        self.tick += self.grid

    def _evaluate(self, affected, now, store):
        targets = set(affected)
        for w in tuple(affected):
            targets |= self._neighbors(w, now)
        emissions = []
        batch, context, rows_in_batch = [], set(), 0

        def flush():
            nonlocal batch, context, rows_in_batch
            if not batch:
                return
            rows = [r for w in context for r in self._frame(w)]
            cases = self._kernel(rows, now)
            self.kernel_calls += 1
            self.kernel_rows += len(rows)
            self.comparisons += len({(r[W], r[EK]) for r in rows})
            wanted = set(batch)
            fresh = defaultdict(list)
            for case in cases:
                if case['wallet'] in wanted:
                    fresh[case['wallet']].append(case)
            for w in batch:
                self._apply(w, fresh.get(w, ()), now, emissions)
            batch, context, rows_in_batch = [], set(), 0

        for w in sorted(targets):
            if self.screen and not self._can_signal(w, now):
                self._apply(w, (), now, emissions)
                continue
            members = self._neighbors(w, now) | {w}
            batch.append(w)
            context |= members
            rows_in_batch += sum(len(self.by_wallet.get(x, ())) for x in members)
            if rows_in_batch >= LOT_LIGNES:
                flush()
        flush()
        self._emit(emissions, now, store)

    def _apply(self, wallet, cases, now, emissions):
        seen = set()
        mine = self.current[wallet]
        for case in cases:
            pair = (wallet, case['event_id'])
            seen.add(case['event_id'])
            old = mine.get(case['event_id'])
            if old:
                self.scores[old[0]] -= 1
            fp = case['material_fingerprint']
            mine[case['event_id']] = (case['score'], bool(case['priority']), fp)
            self.scores[case['score']] += 1
            self.max_score[pair] = max(self.max_score.get(pair, 0), case['score'])
            if case['score'] >= 1 and pair not in self.first_behavior:
                self.first_behavior[pair] = (now, case['score'], sorted({s['rule'] for s in case['signals']}))
            if case['priority'] and (not old or not old[1] or old[2] != fp):
                emissions.append(case)
        for event_key in [e for e in mine if e not in seen]:
            self.scores[mine[event_key][0]] -= 1
            del mine[event_key]
        if not mine:
            del self.current[wallet]

    def _emit(self, emissions, now, store):
        new_pairs = []
        for case in emissions:
            pair = (case['wallet'], case['event_id'])
            if pair in self.first_priority:
                self.reobservations[str(int(now // 86400))] += 1
                if case['score'] <= self.first_priority[pair]['max_score']:
                    continue
                self.first_priority[pair]['max_score'] = case['score']
            else:
                rank = 1 + sum(n for s, n in self.scores.items() if s > case['score'])
                entry = dict(wallet=case['wallet'], event_id=case['event_id'], at=now, score=case['score'], max_score=case['score'],
                             rules=sorted({s['rule'] for s in case['signals']}), rank_tick=rank,
                             pairs_tick=len(self.recent_pairs), tied_tick=self.scores[case['score']],
                             trigger=max((a for a in case['alerts']), key=lambda a: a['timestamp'], default={}).get('transaction_hash'),
                             marches=sorted({a['market_id'] for a in case['alerts']}),
                             buys=len(case['alerts']), title=case.get('event_title'))
                self.first_priority[pair] = entry
                self.queue.append(entry)
                self.daily_new[str(int(now // 86400))] += 1
                new_pairs.append(pair)
            self._write_case(case, now, store)
        return new_pairs

    def _write_case(self, case, now, store):
        m1 = case['event_id'].startswith('unmapped:')
        case = dict(case, current=True, simulated=True, simulation_scenario=self.name)
        if m1:
            case['hypothese_m1'] = 'Événement sans catalogue dans ce rejeu : ouverture supposée, fermeture et échéance inconnues.'
        try:
            with store.transaction() as cx:
                for mid in {a['market_id'] for a in case['alerts'] if a.get('market_id')}:
                    for v in self.markets.get(mid, ()):
                        if v['observed_at'] <= now:
                            store.put('market', mid, v, v['observed_at'], conn=cx)
                for v in self.events.get(case['event_id'], ()):
                    if v['observed_at'] <= now:
                        store.put('event', case['event_id'], v, v['observed_at'], conn=cx)
            scope = review.case_scope(store, case, now)
            case['review_context'] = scope
            # Unknown is not False: without a catalogue this field cannot be read.
            self.first_priority[case['wallet'], case['event_id']].setdefault('announcement', None if m1 else bool(scope['announcement_candidate']))
            case['report'] = reports.export_dossier(self.root, case)
            pbridge.publish_cases(store, [case], None, None, None)
        except OSError as exc:
            raise RuntimeError('Écriture du bac à sable: ' + str(exc)) from exc
        self.dossiers += 1

    def _echantillon_oracle(self, now):
        """Too big for one kernel call: a hashed sample of wallets, closed under the only cross-wallet rule."""
        cibles, contexte, lignes = set(), set(), 0
        for w in sorted(self.by_wallet, key=lambda x: hashlib.sha256(f'{now}|{x}'.encode()).hexdigest()):
            membres = (self._neighbors(w, now) | {w}) - contexte
            taille = sum(len(self._frame(x)) for x in membres)
            if lignes + taille > ORACLE_MAX_LIGNES:
                if lignes:
                    break
                continue
            cibles.add(w)
            contexte |= membres
            lignes += taille
        return cibles, [r for w in contexte for r in self._frame(w)]

    def _oracle(self, now):
        frame = [r for w in self.by_wallet for r in self._frame(w)]
        cibles = None
        if len(frame) > ORACLE_MAX_LIGNES:
            del frame
            cibles, frame = self._echantillon_oracle(now)
            if not cibles:
                self.oracles['sautes'] += 1
                return
        diagnostics = {}
        rows = sorted(frame, key=lambda r: (r[TS], r[ID]))
        markets, events = self._meta_for(rows, now)
        hist = {w: dict(first_timestamp=self.first_ts[w], observations=0) for w in {r[W] for r in rows}}
        cases = signals.evaluate([as_dict(r) for r in rows], markets, events, now=now, config=self.config, wallet_history=hist, diagnostics=diagnostics)
        full = {(c['wallet'], c['event_id']): (c['score'], bool(c['priority']), c['material_fingerprint']) for c in cases}
        mine = {(w, e): v for w, d in self.current.items() for e, v in d.items()}
        if cibles is not None:
            full = {p: v for p, v in full.items() if p[0] in cibles}
            mine = {p: v for p, v in mine.items() if p[0] in cibles}
        if full != mine:
            only_full = sorted(set(full) - set(mine))[:5]
            only_mine = sorted(set(mine) - set(full))[:5]
            changed = sorted(p for p in set(full) & set(mine) if full[p] != mine[p])[:5]
            raise RuntimeError(f'Oracle divergent à {now}: complet seul {only_full}, incrémental seul {only_mine}, différents {changed}')
        if cibles is not None:
            self.oracles['partiels'] += 1
            self.oracles['wallets_partiels'] += len(cibles)
            return
        if diagnostics['examined_recent_buy_pairs'] != len(self.recent_pairs):
            self.oracles['ecart_denominateur'] += 1
        self.oracles['ok'] += 1

    # ---- run -----------------------------------------------------------------------------
    def run(self, store, clock, checkpoint=None, every=4000, stop=lambda: False, progress=None, avant_sauvegarde=None):
        ticks = list(range(T_DEBUT, T_FIN, self.grid))
        n = len(ticks)
        oracle_ticks = {ticks[(i * (n - 1)) // (ORACLES - 1)] for i in range(ORACLES)}
        count = 0
        while self.tick < T_FIN:
            self.step(store, clock, oracle=self.tick in oracle_ticks)
            count += 1
            if progress and count % 1000 == 0:
                progress(self)
            if stop():
                if avant_sauvegarde:
                    avant_sauvegarde()
                self.save(checkpoint)
                return False
            if checkpoint and count % every == 0:
                self.save(checkpoint)
        self.done = True
        return True

    def save(self, path):
        if not path:
            return
        tmp = Path(str(path) + '.tmp')
        with tmp.open('wb') as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(path)


def rss_mo():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576  # macOS reports bytes
