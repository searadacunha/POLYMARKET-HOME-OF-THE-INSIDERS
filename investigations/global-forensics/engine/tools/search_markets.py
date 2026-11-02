"""Find catalogue markets through Polymarket's public search. Prints id, slug, dates and condition ids. Only reads."""
import json, sys, urllib.parse
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf.net import Net
net = Net()
for q in sys.argv[1:]:
    body, _ = net.get('https://gamma-api.polymarket.com/public-search', dict(q=q, limit_per_type=12, events_status='all', keep_closed_markets=1), pause=.3)
    print('##', q, 'events', len((body or {}).get('events') or []) if isinstance(body, dict) else body)
    for e in (body or {}).get('events') or []:
        print(' E', e.get('id'), e.get('slug'), str(e.get('startDate'))[:10], str(e.get('endDate'))[:10], 'vol', round(float(e.get('volume') or 0)), 'mk', len(e.get('markets') or []))
