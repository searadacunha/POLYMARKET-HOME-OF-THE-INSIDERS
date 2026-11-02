"""Bounded official feeds: source statements, never instructions or secret-information proof."""
import hashlib
import html
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse


def date_value(text):
    if not text:
        return None
    try:
        value = parsedate_to_datetime(text)
    except (ValueError, TypeError):
        try:
            value = datetime.fromisoformat(text.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None
    return value.replace(tzinfo=value.tzinfo or timezone.utc).timestamp()


def clean_text(value):
    value = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', value or '', flags=re.S | re.I)
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', value))).strip()


def parse_feed(body, source, observed_at):
    if isinstance(body, bytes):
        body = body.decode('utf-8', errors='replace')
    if not isinstance(body, str) or '<!DOCTYPE' in body.upper() or '<!ENTITY' in body.upper():
        raise ValueError('Feed must be XML without entity declarations')
    root = ET.fromstring(body)
    entries = []
    nodes = [node for node in root.iter() if node.tag.rsplit('}', 1)[-1] in ('item', 'entry')]
    stats = {'total_entries': len(nodes), 'processed_entries': min(50, len(nodes)),
             'remaining_entries': max(0, len(nodes)-50), 'dropped_links': 0, 'content_truncated': 0}
    for node in nodes[:50]:
        values = {}
        for child in node:
            name = child.tag.rsplit('}', 1)[-1]
            if name == 'link' and child.get('href'):
                values[name] = child.get('href')
            else:
                values[name] = ''.join(child.itertext())
        url = values.get('link', '').strip()
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname not in source['allowed_hosts'] or parsed.username or parsed.password:
            stats['dropped_links'] += 1
            continue
        title = clean_text(values.get('title', ''))
        content = clean_text(values.get('description', values.get('summary', values.get('content', ''))))
        stats['content_truncated'] += int(len(title) > 600 or len(content) > 12000)
        title, content = title[:600], content[:12000]
        digest = hashlib.sha256((title + '\n' + content).encode()).hexdigest()
        entries.append({'url': url, 'title': title, 'content': content, 'content_sha256': digest,
                        'source': source['name'], 'source_url': source['url'],
                        'publication_claimed_at': date_value(values.get('pubDate', values.get('published'))),
                        'modification_claimed_at': date_value(values.get('updated')),
                        'first_observed_at': observed_at, 'proof_level': 'affirmation d’une source',
                        'independence_key': digest})
    stats['accepted_entries'] = len(entries)
    stats['truncated'] = bool(stats['remaining_entries'] or stats['content_truncated'])
    return {'items': entries, **stats}


def relevant(entry, event):
    ignored = {'will', 'there', 'which', 'what', 'before', 'after', 'winner', '2026', '2027', 'the', 'and', 'for'}
    title_words = {x for x in re.findall(r'[a-z0-9]{4,}', event.get('title', '').lower()) if x not in ignored}
    content_words = set(re.findall(r'[a-z0-9]{4,}', (entry['title'] + ' ' + entry['content']).lower()))
    return len(title_words & content_words) >= min(2, len(title_words)) if title_words else False


def milestone_kind(payload):
    if payload.get('milestone_type') in ('public_information','official_resolution'):
        return payload['milestone_type']
    if urlparse(payload.get('source_url','')).path.endswith('/resolutions'):
        return 'official_resolution'
    return 'unclassified'


def public_timing(milestone, trade_at, as_of):
    """Knowledge at assessment time; a resolution date is never an announcement date."""
    unknown=dict(status='unknown',first_public_at=None,resolution_observed_at=None)
    if not milestone or milestone['observed_at']>as_of:return unknown
    p=milestone['payload'];at=p.get('public_at')
    if not (p.get('verified') and p.get('result_available') and p.get('source_url') and p.get('evidence_id')
            and isinstance(at,(int,float)) and at<=as_of):return unknown
    kind=milestone_kind(p)
    if kind=='official_resolution':return dict(unknown,status='resolution_only',resolution_observed_at=at)
    if kind!='public_information':return unknown
    return dict(status='after_public_information' if trade_at>=at else 'before_verified_public_information',
                first_public_at=at,resolution_observed_at=None,source_url=p['source_url'],evidence_id=p['evidence_id'])


async def collect_news(store, net, config, event):
    registry = json.loads((Path(config['root']) / 'config/sources.json').read_text())
    event = event or {}
    text = (event.get('title', '') + ' ' + ' '.join(event.get('tags', []))).lower()
    selected = [s for s in registry['feeds'] if any(term in text for term in s['event_terms'])][:2]
    result = {'availability': 'première disponibilité publique inconnue', 'items': [], 'sources': [],
              'coverage': 'Flux officiels configurés uniquement ; recherche web exhaustive non disponible.',
              'public_result': False, 'official_resolution_known': False, 'observed_at': time.time()}
    for source in selected:
        parsed = urlparse(source['url'])
        if parsed.scheme != 'https' or parsed.hostname not in source['allowed_hosts'] or parsed.username or parsed.password:
            result['sources'].append({'source': source['name'], 'status': 'error', 'detail': 'URL hors liste autorisée'})
            continue
        try:
            response = await net.request(source['url'])
            parsed_feed = parse_feed(response.body, source, response.observed_at)
            entries = parsed_feed['items']
            matched = []
            for entry in entries:
                if not relevant(entry, event):
                    continue
                entry['evidence_id'] = response.evidence_id
                key = hashlib.sha256((entry['url'] + entry['content_sha256']).encode()).hexdigest()
                previous = store.get('news', key)
                if previous:
                    entry['first_observed_at'] = previous['first_seen']
                store.put('news', key, entry, observed_at=response.observed_at)
                matched.append(entry)
            result['items'].extend(matched)
            result['sources'].append({'source': source['name'],
                                      'status': 'capped' if parsed_feed['truncated'] else 'degraded' if parsed_feed['dropped_links'] else 'ok' if matched else 'empty',
                                      'items_read': len(entries), 'matches': len(matched), 'evidence_id': response.evidence_id,
                                      'coverage': {k:v for k,v in parsed_feed.items() if k != 'items'}})
        except Exception as exc:
            result['sources'].append({'source': source['name'], 'status': 'error', 'detail': f'{type(exc).__name__}: {str(exc)[:220]}'})
            if getattr(exc, 'budget_exhausted', False):
                break
    # A reviewed milestone is separate evidence; an article match alone never establishes the result.
    milestone = store.get('public_milestone', str(event.get('id', '')))
    if milestone:
        payload = milestone['payload']
        if payload.get('verified') is True and payload.get('result_available') is True and payload.get('source_url') and payload.get('evidence_id') and payload.get('public_at', float('inf')) <= result['observed_at'] and milestone['observed_at'] <= result['observed_at']:
            result['milestone'] = payload
            if milestone_kind(payload)=='public_information':
                result['public_result'] = True
                result['availability'] = 'information publique retrouvée'
            elif milestone_kind(payload)=='official_resolution':
                result['official_resolution_known'] = True
                result['availability'] = 'résolution officielle observée ; première information publique inconnue'
    if not selected:
        result['sources'].append({'source': 'configuration', 'status': 'uncovered', 'detail': 'Aucun flux officiel pertinent configuré pour cet événement'})
    result['truncated'] = any(s.get('status') == 'capped' for s in result['sources'])
    result['degraded'] = any(s.get('status') in ('error', 'uncovered', 'degraded', 'capped') for s in result['sources'])
    return result


async def resolution_state(store, net, event):
    """Exclude formally resolved conditions at observation time, never at an inferred news time."""
    event_id = str(event.get('id', ''))
    if not event_id.isdigit():
        return {'status': 'uncovered', 'reason': 'Identifiant événement Gamma numérique absent'}
    url = 'https://data-api.polymarket.com/v2/resolutions'
    response = await net.request(url, params={'event_id': event_id})
    body = response.body
    if not isinstance(body, dict) or not isinstance(body.get('data'), list):
        raise ValueError('Malformed resolution response')
    rows = body['data']
    resolved = set()
    for row in rows:
        if not isinstance(row, dict) or not row.get('condition_id') or not isinstance(row.get('status'), str):
            raise ValueError('Malformed condition resolution')
        store.put('resolution', row['condition_id'], {'row': row, 'event_id': event_id,
                  'evidence_id': response.evidence_id, 'observed_at': response.observed_at}, observed_at=response.observed_at)
        if row['status'].lower() == 'resolved':
            resolved.add(row['condition_id'])
            previous_condition = store.get('public_condition', row['condition_id'])
            first_condition = previous_condition['payload']['public_at'] if previous_condition else response.observed_at
            store.put('public_condition', row['condition_id'], {
                'condition_id': row['condition_id'], 'event_id': event_id,
                'milestone_type': 'official_resolution',
                'verified': True, 'result_available': True,
                'public_at': first_condition, 'public_observed_at': first_condition,
                'source_url': url, 'evidence_id': response.evidence_id,
                'proof_level': 'affirmation d’une source officielle : condition résolue',
                'note': 'Première lecture du résultat par le bot ; première annonce publique antérieure inconnue.'},
                observed_at=response.observed_at)
    market_rows = store.conn.execute(
        "SELECT payload FROM objects WHERE kind='market' AND CAST(json_extract(payload,'$.event_id') AS TEXT)=?", (event_id,)).fetchall()
    known_markets = [json.loads(r['payload']) for r in market_rows]
    expected = {str(m.get('condition_id', '')) for m in known_markets}
    expected.discard('')
    # Gamma may have acquired further markets since discovery; the full resolution response must also be terminal.
    all_resolved = bool(expected) and len(expected) == len(known_markets) and expected <= resolved and all(r['status'].lower() == 'resolved' for r in rows)
    if all_resolved:
        previous = store.get('public_milestone', event_id)
        first = previous['payload'].get('public_at', response.observed_at) if previous else response.observed_at
        if not previous or milestone_kind(previous['payload'])!='public_information':store.put('public_milestone', event_id, {
            'milestone_type': 'official_resolution',
            'verified': True, 'result_available': True, 'public_at': first,
            'public_observed_at': first, 'source_url': url, 'evidence_id': response.evidence_id,
            'proof_level': 'affirmation d’une source officielle : toutes les conditions connues résolues',
            'condition_ids': sorted(expected),
            'note': 'Retiré des alertes préalables à compter de l’observation ; date de première annonce inconnue.'},
            observed_at=response.observed_at)
    return {'status': 'ok' if rows else 'empty', 'conditions': len(rows),
            'resolved_conditions': sorted(resolved), 'all_known_conditions_resolved': all_resolved,
            'evidence_id': response.evidence_id, 'observed_at': response.observed_at}
