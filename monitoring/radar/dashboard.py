"""One static HTML page from the sealed alerts and their evaluations: filters by market, wallet, cluster, class,
evidence level and period. No server, no network, no external script: open the file in a browser. Every text from
the alerts (market titles come from Polymarket) is inserted as text, never as HTML."""
import json

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Radar alerts</title><style>
:root{--bg:#fbfbf8;--fg:#1d1d1b;--mute:#6b6b66;--line:#dcdcd4;--accent:#2f5d8a;--warn:#8a5a00}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--fg:#ecece6;--mute:#9a9a92;--line:#33332f;--accent:#8db4dc;--warn:#e0b25c}}
body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:16px}
h1{font-size:18px;margin:0 0 4px}p.note{color:var(--mute);margin:0 0 12px;max-width:70em}
form{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}input,select{font:inherit;padding:4px 6px;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:4px}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--mute);font-weight:600}td.num{text-align:right;font-variant-numeric:tabular-nums}code{font-size:12px}
details summary{cursor:pointer;color:var(--accent)}pre{white-space:pre-wrap;word-break:break-all;font-size:12px;max-width:90vw}
.lvl{color:var(--warn)}.wrap{overflow-x:auto}
</style></head><body>
<h1>Radar alerts</h1><p class="note">Each row is an anomaly seen in public data, sealed when it was raised. It is not a finding about a person,
and the out-of-sample result of its class is shown with it. Evaluations come later, from a separate file.</p>
<form id="f"><input name="q" placeholder="market or outcome"><input name="wallet" placeholder="wallet or cluster key">
<select name="cls"><option value="">every class</option></select><input name="from" type="date"><input name="to" type="date">
<span id="n"></span></form><div class="wrap"><table><thead><tr><th>Trigger (UTC)</th><th>Class</th><th>Market and outcome</th><th>Price</th>
<th>Wallets</th><th>Out of sample</th><th>Evaluation</th><th></th></tr></thead><tbody id="b"></tbody></table></div>
<script id="data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent),f=document.getElementById('f'),b=document.getElementById('b');
const E={};for(const e of D.evaluations){E[e.alert]=e}
const cls=[...new Set(D.alerts.map(a=>a.risk.class))].sort();for(const c of cls){const o=document.createElement('option');o.value=c;o.textContent=c;f.cls.appendChild(o)}
function td(t,c){const x=document.createElement('td');x.textContent=t==null?'':String(t);if(c)x.className=c;return x}
function draw(){b.textContent='';const q=f.q.value.toLowerCase(),w=f.wallet.value.toLowerCase(),c=f.cls.value,fr=f.from.value,to=f.to.value;let n=0;
for(const a of D.alerts){const day=(a.trigger_utc||'').slice(0,10),mk=((a.market.question||'')+' '+(a.market.outcome||'')).toLowerCase();
const keys=(a.wallets||[]).concat(a.cluster?[a.cluster.key]:[]).join(' ').toLowerCase();
if(q&&!mk.includes(q))continue;if(w&&!keys.includes(w))continue;if(c&&a.risk.class!==c)continue;if(fr&&day<fr)continue;if(to&&day>to)continue;n++;
const r=document.createElement('tr'),e=E[a.id],o=a.controls.out_of_sample||{};
r.append(td(a.trigger_utc),td(a.risk.class),td((a.market.question||'')+' / '+(a.market.outcome||'')),td(a.price_and_depth.price_at_alert,'num'),
td((a.wallets||[]).join(' ')+(a.cluster?' (cluster '+a.cluster.key+')':'')),td((o.study_verdict||o.status||'')+(o.excess!=null?' '+(100*o.excess).toFixed(1)+' pts':''),'lvl'),
td(e?(e.status+(e.outcome_won==null?'':e.outcome_won?' won':' lost')+(e.shadow&&e.shadow.net_return_per_usd!=null?' '+e.shadow.net_return_per_usd:'')):'not yet'));
const x=document.createElement('td'),d=document.createElement('details'),s=document.createElement('summary'),p=document.createElement('pre');
s.textContent='record';p.textContent=JSON.stringify({alert:a,evaluation:e||null},null,1);d.append(s,p);x.append(d);r.append(x);b.append(r)}
document.getElementById('n').textContent=n+' of '+D.alerts.length+' alerts'}
f.addEventListener('input',draw);draw();
</script></body></html>"""


def _clean(x):
    """NaN and infinities become null: JSON.parse would reject the whole page otherwise."""
    if isinstance(x, float) and (x != x or x in (float("inf"), float("-inf"))):
        return None
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean(v) for v in x]
    return x


def render(alerts, evaluations):
    """The page as a string. In the embedded JSON every <, > and & is written as a \\u escape, so no value can end the
    script element or open an HTML comment inside it."""
    data = json.dumps(_clean({"alerts": alerts, "evaluations": evaluations}), sort_keys=True, allow_nan=False)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return PAGE.replace("__DATA__", data)
