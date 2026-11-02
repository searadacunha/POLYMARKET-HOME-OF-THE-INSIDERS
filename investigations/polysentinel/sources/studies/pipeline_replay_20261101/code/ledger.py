"""Bounded public GET with a durable request ledger: 300 requests, ever, for the whole pilot.

Errors raise; nothing here turns a failure into an empty result. Every attempt is counted,
including failures, because the budget is what was asked of the API, not what it answered.
"""
import gzip
import hashlib
import http.client
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
LEDGER = ETUDE / 'data' / 'requests.jsonl'
LIMITE = 300
TAILLE_MAX = 16_000_000
HOTES = {'data-api.polymarket.com', 'gamma-api.polymarket.com'}


class BudgetEpuise(RuntimeError):
    pass


class ReponseInvalide(RuntimeError):
    pass


def compteur():
    if not LEDGER.exists():
        return 0
    with LEDGER.open() as f:
        return sum(1 for _ in f)


def appel(url, params, *, phase, tentatives=3):
    """Return the parsed JSON body and its receipt. Each attempt spends one request."""
    if urllib.parse.urlsplit(url).hostname not in HOTES:
        raise ReponseInvalide('Hôte hors du plan: ' + url)
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    full = url + ('?' + query if query else '')
    for essai in range(tentatives):
        if compteur() >= LIMITE:
            raise BudgetEpuise(f'{LIMITE} requêtes atteintes')
        recu = dict(n=compteur() + 1, phase=phase, url=url, params=params, at=time.time(), essai=essai)
        erreur = None
        try:
            req = urllib.request.Request(full, headers={'User-Agent': 'PolySentinel/0.1 public-read-only',
                                                        'Accept-Encoding': 'gzip'})
            with urllib.request.urlopen(req, timeout=40) as r:
                brut = r.read(TAILLE_MAX + 1)
                recu['status'] = r.status
                if r.headers.get('Content-Encoding') == 'gzip':
                    brut = gzip.decompress(brut)
            recu.update(bytes=len(brut), sha256=hashlib.sha256(brut).hexdigest())
        except urllib.error.HTTPError as exc:
            recu['status'] = exc.code
            erreur = exc
            brut = None
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException, EOFError) as exc:
            recu['status'] = None
            recu['erreur'] = str(exc)[:300]
            erreur = exc
            brut = None
        with LEDGER.open('a') as f:
            f.write(json.dumps(recu, sort_keys=True) + '\n')
            f.flush()
            os.fsync(f.fileno())
        if brut is not None and len(brut) > TAILLE_MAX:
            raise ReponseInvalide(f'Réponse > {TAILLE_MAX} octets: {full}')
        if brut is not None:
            return json.loads(brut), recu
        if isinstance(erreur, urllib.error.HTTPError) and erreur.code not in (429, 500, 502, 503, 504):
            raise ReponseInvalide(f'HTTP {erreur.code}: {full}') from erreur
        time.sleep(min(30, 3 * 2 ** essai) * (1 + random.random() / 4))
    raise ReponseInvalide(f'Échec après {tentatives} tentatives: {full}') from erreur
