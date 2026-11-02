"""Local, escaped HTML and immutable JSON evidence exports."""
import datetime as dt
import hashlib
import gzip
import html
import json
import os
import re
from pathlib import Path
from zoneinfo import ZoneInfo

from .db import encode
from .storage_budget import guard_export

STYLE = '''body{font:15px system-ui;background:#0b1220;color:#e2e8f0;margin:0}main{max-width:1200px;margin:auto;padding:28px}h1,h2{color:#f8fafc}h1{font-size:32px}h2{font-size:21px;margin-top:32px}a{color:#67e8f9}small,.muted{color:#94a3b8}.cards{display:flex;gap:16px;flex-wrap:wrap}.card,article{background:#162235;border:1px solid #334155;border-radius:12px;padding:20px;margin:12px 0}.card strong{display:block;font-size:28px}.ok{color:#86efac}.warn{color:#fcd34d}.bad{color:#fda4af}table{border-collapse:collapse;width:100%;font-size:13px}td,th{border-bottom:1px solid #334155;text-align:left;padding:10px;vertical-align:top}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#101a2c;padding:15px;border-radius:8px}code{overflow-wrap:anywhere}details{margin:12px 0}summary{cursor:pointer;font-weight:600}.scroll{overflow-x:auto}footer{margin:32px 0;color:#94a3b8}@media(max-width:640px){main{padding:14px}h1{font-size:26px}td,th{padding:6px}}'''

def esc(value):
    return html.escape(str(value if value is not None else 'non calculable'), quote=True)

def times(value):
    if not isinstance(value, (int, float)):
        return esc(value or 'inconnu')
    d = dt.datetime.fromtimestamp(value,dt.timezone.utc)
    return f'{d:%Y-%m-%d %H:%M:%S} UTC · {d.astimezone(ZoneInfo("Europe/Lisbon")):%H:%M:%S %Z}'

def page(title, content, refresh=False):
    refresh_tag = '<meta http-equiv="refresh" content="30">' if refresh else ''
    return f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{refresh_tag}<title>{esc(title)}</title><style>{STYLE}</style></head><body><main><header><a href="/">PolySentinel</a> · surveillance publique locale</header><h1>{esc(title)}</h1>{content}<footer>Seuils exploratoires. Un score ne prouve aucune information privilégiée. Horodatages UTC de référence, heure de Lisbonne affichée en complément.</footer></main></body></html>'

def detail(value):
    return '<pre>'+esc(json.dumps(value,ensure_ascii=False,indent=2))+'</pre>'

def dossier_html(case, investigation=None):
    content = f'<p class="warn">{esc(case.get("status", "données insuffisantes"))}</p>'
    content += f'<p>Adresse/proxy : <code>{esc(case.get("wallet"))}</code> · Événement : {esc(case.get("event_id"))}</p>'
    content += f'<p>Calcul : {times(case.get("calculated_at"))}</p>'
    if case.get('review_context'):
        content+='<h2>Périmètre d’enquête et complétude</h2>'+detail(case['review_context'])
    alerts=case.get('alerts',[])
    if alerts:
        content+='<h2>Chronologie des opérations</h2><div class="scroll"><table><tr><th>Heure</th><th>Issue / sens</th><th>Prix</th><th>Parts</th><th>Nominal</th><th>Transaction</th></tr>'
        for a in alerts[:50]:
            tx=a.get('transaction_hash') or (a.get('transactions') or [''])[0]
            link=f'<a href="https://polygonscan.com/tx/{tx}">{tx[:14]}…</a>' if re.fullmatch(r'0x[0-9a-fA-F]{64}',str(tx)) else esc(tx)
            content+=f'<tr><td>{times(a.get("timestamp"))}</td><td>{esc(a.get("outcome"))} / {esc(a.get("side"))}</td><td>{esc(a.get("price"))}</td><td>{esc(a.get("size"))}</td><td>{esc(a.get("nominal"))}</td><td>{link}</td></tr>'
        content+='</table></div>'
        if len(alerts)>50:content+=f'<p>50 groupes affichés sur {len(alerts)} ; détail complet ci-dessous.</p>'
    for key,label in [('score','Score d’anomalie exploratoire'),('quality','Qualité des données'),('signals','Règles et références'),('alerts','Opérations'),('contradictions','Explications concurrentes'),('limitations','Limites'),('evidence','Preuves')]:
        if key in case:
            content += '<h2>'+label+'</h2>'+detail(case[key])
    if investigation:
        content += '<h2>Enquête et preuves</h2><p>'+esc(investigation.get('status'))+' · '+esc(investigation.get('public_availability'))+'</p>'
        for key,label in [('histories','Couverture des historiques'),('receipts','Rapprochements blockchain'),('graph','Liens financiers sourcés'),('news','Information publique'),('positions','Positions observées'),('activity_sequences','Séquences de financement et retraits'),('errors','Limites des sources')]:
            content+='<details><summary>'+label+'</summary>'+detail(investigation.get(key))+'</details>'
        content+='<details><summary>Enquête complète</summary>'+detail(investigation)+'</details>'
    if case.get('scenarios'):content+='<details><summary>Scénarios liés — interprétation à vérifier</summary>'+detail(case['scenarios'])+'</details>'
    content += '<details><summary>Dossier complet</summary>'+detail(case)+'</details>'
    return page('Dossier '+str(case.get('id','')),content)

def atomic_write(path, text):
    path = Path(path)
    raw = text if isinstance(text,bytes) else text.encode('utf-8')
    if path.is_file() and not path.is_symlink() and path.read_bytes() == raw:
        return
    guard_export(path,len(raw))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp = path.with_name(path.name+'.tmp')
    tmp.write_bytes(raw)
    os.replace(tmp,path)

def export_dossier(root, case, investigation=None):
    # The derived filename is not evidence and must not change its own hash.
    case = {k:v for k,v in case.items() if k != 'report'}
    payload = dict(case=case,investigation=investigation)
    digest = hashlib.sha256(encode(payload).encode()).hexdigest()[:12]
    key = re.sub(r'[^A-Za-z0-9_.-]','_',str(case.get('id','dossier')))[:90]
    stem = f'{key}-{digest}-z1'
    dest = Path(root)/'reports'
    atomic_write(dest/(stem+'.json.gz'),gzip.compress(encode(payload).encode(),mtime=0))
    summary={k:case.get(k) for k in ('id','wallet','event_id','calculated_at','score','status','quality','contradictions')}
    content='<p>Version archivée complète et sans perte dans le JSON compressé ci-dessous.</p>'+detail(summary)
    content+=f'<p><a href="/reports/{esc(stem)}.json.gz">Télécharger les preuves de cette version</a> · <a href="/case/{esc(key)}">Consulter le dossier courant (peut avoir évolué)</a></p>'
    atomic_write(dest/(stem+'.html'),page('Dossier archivé '+key,content))
    return stem

def daily_report(store, snapshot):
    day = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
    cases = [r['payload'] for r in store.list('case',limit=100)]
    payload = dict(date_utc=day,**snapshot,cases=cases)
    stem = 'quotidien-'+day+'-z2'
    dest = store.root/'reports'
    atomic_write(dest/(stem+'.json.gz'),gzip.compress(encode(payload).encode(),mtime=0))
    content=detail({k:payload.get(k) for k in ('date_utc','generated_at','verdict','counts')})
    content+=f'<p><a href="/reports/{stem}.json.gz">Rapport complet compressé, avec les preuves</a></p>'
    atomic_write(dest/(stem+'.html'),page('Rapport local du '+day,content))
    return str(dest/(stem+'.html'))
