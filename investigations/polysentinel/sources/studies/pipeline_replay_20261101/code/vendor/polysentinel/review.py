"""Current investigation scope, separate from historical anomaly scores."""
import time
from .priority import announcement_scope


def case_scope(store, case, now=None, cache=None):
    now = time.time() if now is None else now
    cache = {} if cache is None else cache
    def known(kind, key):
        identity = kind, str(key)
        if identity not in cache:
            cache[identity] = store.get(*identity)
        row = cache[identity]
        if not row or row['observed_at'] > now:
            return {}
        payload_at=row['payload'].get('observed_at')
        at=max(row['observed_at'],payload_at) if isinstance(payload_at,(int,float)) else row['observed_at']
        return dict(row['payload'], observed_at=at)
    event = known('event', case.get('event_id', ''))
    public = known('public_milestone', case.get('event_id', ''))
    scopes = []
    for mid in sorted({str(a['market_id']) for a in case.get('alerts', []) if a.get('market_id')}):
        market = known('market', mid)
        scope = announcement_scope(market, event, now)
        resolution = known('public_condition', market.get('condition_id', ''))
        if any(p.get('verified') and p.get('result_available') for p in (public, resolution)):
            scope = dict(scope, eligible=False, reason='Résultat public déjà observé')
        coverage = known('market_coverage', mid)
        scopes.append(dict(market_id=mid, **scope, coverage={k:coverage.get(k) for k in
            ('status','last_success','cutoff','initial_cutoff','range_oldest','range_newest','pending_walks','rejected')}))
    relevant = any(s['eligible'] for s in scopes)
    ready = relevant and case.get('current', True) and case.get('priority') and case.get('preliminary')
    return dict(assessed_at=now, eligible_for_automatic_investigation=bool(ready),
                announcement_candidate=relevant, markets=scopes,
                reason='Annonce à examiner, sans preuve de secret' if ready else
                       'Annonce admissible absente ou dossier non prioritaire/préalable',
                historical_score_unchanged=True, history_complete=False,
                limitations=['La date de fin est une échéance contractuelle, pas une heure d’annonce certifiée.',
                             'Une source de résolution ne prouve ni absence d’annonce antérieure ni accès privilégié.',
                             'Les fenêtres interrogées ne constituent pas un historique complet.'])
