"""Phase 8 : univers de marchés défini SANS regarder les résultats.
Règles (fixées avant toute mesure) :
- marchés Polymarket fermés, endDate entre 2025-10-01 et 2026-09-15, volumeNum >= 250 000 $ (filtre de liquidité)
- exclus par motif de slug/question : sport, e-sport, prix/seuils crypto, up/down, compteurs de tweets, météo
- split temporel sur endDate : TRAIN < 2026-03-01 <= VALID < 2026-06-01 <= TEST"""
import json,re,datetime as dt,collections
from common2 import http
EXCL=re.compile(r'(^|-)(epl|nba|nfl|mlb|nhl|ncaa|cbb|cfb|ucl|uel|uecl|mls|wnba|atp|wta|ufc|mma|boxing|f1|nascar|pga|golf|lol|cs2|csgo|dota|valorant|esports|cricket|ipl|t20|laliga|la-liga|serie-a|bundesliga|ligue-1|sea|fifa|world-cup|super-bowl|stanley-cup|nba-finals|tennis|premier-league|championship|copa|afc|caf|nations-league)(-|$)|'
                r'-vs-|bitcoin|ethereum|solana|xrp|dogecoin|btc|eth-|crypto-price|up-or-down|updown|price-of|above-|below-|reach-|dip-to|hit-\$|'
                r'tweets|temperature|weather|rain|snow|hurricane-category|spread|o-u-|over-under|total-goals|-1h-|-15m|-5m|-4h|daily',re.I)
out=[]; seen=set()
start=dt.date(2025,10,1); end=dt.date(2026,9,15)
d0=start
while d0<end:
    d1=min(d0+dt.timedelta(days=7),end)
    off=0
    while True:
        r=http(f'https://gamma-api.polymarket.com/markets?closed=true&end_date_min={d0}&end_date_max={d1}&volume_num_min=250000&limit=500&offset={off}',cache=True)
        if not isinstance(r,list) or not r: break
        for m in r:
            if m['conditionId'] in seen: continue
            seen.add(m['conditionId'])
            out.append({k:m.get(k) for k in ('conditionId','slug','question','volumeNum','startDate','endDate','closedTime','outcomes','outcomePrices','clobTokenIds','negRisk','createdAt')})
        if len(r)<500: break
        off+=500
    d0=d1
keep=[m for m in out if not EXCL.search((m['slug'] or '')+' '+(m['question'] or '').lower().replace(' ','-'))]
def split(m):
    e=(m.get('endDate') or '')[:10]
    return 'TRAIN' if e<'2026-03-01' else ('VALID' if e<'2026-06-01' else 'TEST')
for m in keep: m['split']=split(m)
json.dump(keep,open('p8/universe.json','w'))
print('closed markets >=250k',len(out),'kept after exclusion',len(keep),collections.Counter(m['split'] for m in keep))
print('examples kept',[m['slug'] for m in keep[:25]])
