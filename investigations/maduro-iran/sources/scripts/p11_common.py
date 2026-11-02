"""Phase 11 : règles partagées (univers, catégories, chemins). Les règles d'exclusion et de catégorie sont celles des phases 8-9, inchangées."""
import os, re, json, time, hashlib, urllib.request

ROOT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran')
RAW = os.path.join(ROOT, 'donnees', 'brut_p11')
OUT = os.path.join(ROOT, 'phase11')
DATA = '/private/tmp/claude-501/-Users-benjamindacunha-Downloads/b2d4e943-355c-4fe5-9c72-2438aead8117/scratchpad/mad'  # p8/, p9/ (historique)

# p8_universe.py (exclusions par motif) + règle « codes d'équipes + date » ajoutée en phase 8
EXCL = re.compile(r'(^|-)(epl|nba|nfl|mlb|nhl|ncaa|cbb|cfb|ucl|uel|uecl|mls|wnba|atp|wta|ufc|mma|boxing|f1|nascar|pga|golf|lol|cs2|csgo|dota|valorant|esports|cricket|ipl|t20|laliga|la-liga|serie-a|bundesliga|ligue-1|sea|fifa|world-cup|super-bowl|stanley-cup|nba-finals|tennis|premier-league|championship|copa|afc|caf|nations-league)(-|$)|'
                  r'-vs-|bitcoin|ethereum|solana|xrp|dogecoin|btc|eth-|crypto-price|up-or-down|updown|price-of|above-|below-|reach-|dip-to|hit-\$|'
                  r'tweets|temperature|weather|rain|snow|hurricane-category|spread|o-u-|over-under|total-goals|-1h-|-15m|-5m|-4h|daily', re.I)
GAME = re.compile(r'^[a-z0-9]{2,6}(-[a-z0-9]{2,6}){1,3}-20\d\d-\d\d-\d\d')


def excluded(slug, question=''):
    s = (slug or '') + ' ' + (question or '').lower().replace(' ', '-')
    return bool(EXCL.search(s)) or bool(GAME.search(slug or ''))


def category(slug):
    s = slug or ''
    if 'earnings' in s:
        return 'earnings'
    if re.search(r'elect|president|prime-minister|senate|house|governor|mayor|parliament|party|vote|nominee|primary|cabinet|resign|impeach|approval', s):
        return 'election/politics'
    if re.search(r'strike|war|ceasefire|invade|capture|military|attack|missile|troops|nato|ukraine|russia|israel|iran|gaza|china|taiwan|venezuela|maduro', s):
        return 'geopolitics/war'
    if re.search(r'fed|rate|cpi|inflation|gdp|recession|tariff|jobs|unemployment', s):
        return 'macro/fed'
    return 'other'


def get(url, data=None, timeout=30, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                         headers={'User-Agent': 'curl/8.4.0', 'Content-Type': 'application/json'})
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        except Exception as e:
            err = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f'GET {url[:120]} : {err!r}'[:300])


def sig_hist_version():
    """Empreinte de la définition SIG_HIST (spécification gelée + modèles + code du détecteur)."""
    h = hashlib.sha256()
    for f in ('phase9/frozen_spec.json', 'phase9/modeles/frozen_model.pkl', 'phase9/modeles/frozen_model_wallet.pkl', 'phase9/modeles/frozen_model_ctx.pkl',
              'scripts/p9_detector.py'):
        h.update(open(os.path.join(ROOT, f), 'rb').read())
    return h.hexdigest()
