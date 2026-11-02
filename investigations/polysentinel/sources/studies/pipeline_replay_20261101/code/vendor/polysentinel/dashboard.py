import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote

from .db import Store
from .reports import esc, times, page, detail, dossier_html
from .quality import measure_quality, case_quality, targeted_context


def review_files(root):
    files = {'restoration': root/'evidence/restoration_20261029/REPORT.md',
             'targeted': root/'evidence/targeted_20261027/inquiries/REPORT.md'}
    study = root/'studies/chronological_20261027'
    for name in ('results.md', 'RAPPORT.md', 'REPORT.md', 'results/REPORT.md', 'results/RAPPORT.md'):
        if (study/name).is_file():
            files['historical'] = study/name
            break
    return {key: path for key, path in files.items() if path.is_file() and not path.is_symlink()}

def snapshot(store):
    from .prospective_bridge import dashboard_status
    now = time.time()
    heartbeat = store.get('service','heartbeat')
    hb = heartbeat['payload'] if heartbeat else {}
    from .monitoring import runtime_status
    latest=runtime_status(store.root)
    if latest.get('at',0)>hb.get('at',0):hb=latest
    live = hb.get('running',False) and now-hb.get('at',0)<45
    health = store.list('health',limit=100)
    trade_health = [r for r in health if 'trade' in r['key'].lower()]
    success = [r for r in trade_health if r['payload'].get('status') in ('ok','empty','capped')]
    recent = [r for r in success if now-r['observed_at']<600]
    quality_metrics = measure_quality(store, now=now)
    ncase = quality_metrics['counts']['current_priority']
    if not recent:
        verdict = 'surveillance indisponible — aucune collecte de trades réussie depuis dix minutes'
    elif ncase:
        verdict = 'Dossiers exploratoires à examiner ; aucune information privilégiée établie'
    else:
        verdict = 'aucun dossier prioritaire détecté dans le périmètre couvert'
    engine=store.get('health','engine')
    if engine and engine['payload'].get('status')=='error':
        verdict='Collecte partielle ; analyse indisponible — '+engine['payload'].get('detail','erreur interne')
    if hb.get('resource_mode')=='paused':
        verdict='Collecte suspendue : '+('; '.join(
            ('espace libre %.3f Go, requis %.3f Go' % (b['free_bytes']/1e9,b['required_bytes']/1e9))
            if b['code']=='volume_free_space' else 'quota projet atteint'
            for b in hb.get('resource_blockers',[])) or 'ressources à recontrôler')+' ; reprise automatique'
    counts = {kind:store.count(kind) for kind in ('event','market','trade','case','investigation','alert','gap','rejected_trade','market_coverage')}
    counts['priority']=ncase
    from .coverage import measure_coverage
    coverage_metrics=measure_coverage(store,now=now)
    market_streams=coverage_metrics['counts']['individually_interrogated']
    from .monitoring import storage_trends
    return dict(generated_at=now,live=live,heartbeat=hb,counts=counts,verdict=verdict,
                prospective=dashboard_status(store.root),
                health=health,market_streams=market_streams,coverage_metrics=coverage_metrics,quality_metrics=quality_metrics,
                storage_trends=storage_trends(store.root),collection_queue=store.checkpoint('collect:queue'),
                coverage='Catalogue découvert, pages de trades bornées et marchés tournants. Historique et univers incomplets ; voir chaque flux.',
                latest_success=max((r['observed_at'] for r in success),default=None))

def home_html(store):
    data = snapshot(store)
    content = f'<p class="{ "ok" if data["live"] else "warn"}">Service : {"actif" if data["live"] else "arrêté ou heartbeat périmé"} · {times(data["generated_at"])}</p>'
    content += '<article>'+esc(data['verdict'])+'<p class="muted">'+esc(data['coverage'])+'</p></article><div class="cards">'
    for kind,label in [('event','événements découverts'),('market','marchés catalogués'),('trade','lignes de trades conservées'),('case','identités de dossiers archivées, toutes versions')]:
        content += f'<div class="card"><strong>{data["counts"][kind]:,}</strong>{label}</div>'
    content += '</div><p>Dernière collecte de trades réussie : '+times(data['latest_success'])+'</p>'
    p=data['prospective']
    content += '<h2>Conservation prospective</h2><p>'+esc(p.get('state','unknown'))+' : '+esc(p.get('detail',''))+'</p><div class="cards">'
    for label,key in [('Dernière alerte observée','last_observed_at'),('Dernière alerte scellée','last_alert_sealed_at')]:
        content += '<div class="card"><strong>'+times(p.get(key))+'</strong>'+label+'</div>'
    for label,key in [('Observations en attente','pending_observations'),('Retard de scellement (s)','seal_lag_seconds')]:
        content += '<div class="card"><strong>'+esc(p.get(key) if p.get(key) is not None else 'inconnu')+'</strong>'+label+'</div>'
    content += '</div><p>Plafond : '+esc(p.get('cap_bytes','inconnu'))+' octets ; capacité restante : '+esc(p.get('remaining_bytes','inconnue'))+' octets.</p>'
    content += '<p>Continuité : '+esc(p.get('continuity','inconnue'))+'</p><details><summary>État et limites de conservation</summary>'+detail(p)+'</details>'
    content += f'<p>{data["counts"]["priority"]} dossiers prioritaires · {data["counts"]["market_coverage"]} marchés interrogés · {data["counts"]["gap"]} lacunes enregistrées · {data["counts"]["rejected_trade"]} lignes en quarantaine.</p>'
    c=data['coverage_metrics']['counts']
    content += f'<p>{c["eligible"]} marchés éligibles · {c["with_ingested_trades"]} avec des trades conservés (tous flux) · {c["collection_recent_complete"]} fenêtres individuelles terminées depuis moins de 10 minutes · {c["stale"]} anciennes · {c["never_attempted"]} jamais interrogés individuellement · {c["error"]} en erreur · {c["backlogged"]} en rattrapage · {c["excluded"]} exclus.</p>'
    content += '<details><summary>Définitions et dénominateurs de couverture</summary>'+detail(data['coverage_metrics'])+'</details>'
    presence=data['coverage_metrics'].get('source_presence',{})
    feeds=presence.get('all_catalogued_with_trades',{})
    content+='<h2>Provenance des marchés avec trades conservés</h2><p>Dénominateur : '+str(c['with_ingested_trades'])+' marchés catalogués avec trades. Présence observée, borne inférieure historique ; aucun historique global exhaustif certifié.</p><ul>'
    for key,label in [('global_only','flux global seul'),('individual_only','flux individuel seul'),('both','les deux flux'),('other_feed','autre flux'),('unattributed','provenance non attribuée')]:
        content+=f'<li>{esc(label)} : {feeds.get(key,0)}</li>'
    content+='</ul>'
    q=data['quality_metrics'];qc=q['counts']
    content+=f'<h2>Qualité et preuves manquantes</h2><p>{qc["all_cases"]} dossiers conservés : {qc["current_cases"]} courants, dont {qc["current_priority"]} prioritaires et {qc["current_nonpriority"]} non prioritaires ; {qc["historical_cases"]} historiques.</p>'
    content+=f'<p><strong>{qc["documentary_complete"]}/{qc["assessed_priority"]} dossiers évalués documentés pour examen</strong> ; {qc["unassessed_priority"]} priorités non évaluées dans cette mesure. Les quatre preuves sont exigées ; ce compte ne mesure pas des initiés. L’éligibilité à une enquête automatique courante est distincte. Mesure : {times(q["generated_at"])}.</p><ul>'
    for key,reason in q['missing_explanations'].items():
        content+=f'<li>{q["missing_counts"].get(key,0)}/{qc["assessed_priority"]} : {esc(reason)}</li>'
    content+='</ul><p>Les catégories de manque se recouvrent ; aucune précision/rappel sans vérité terrain.</p><details><summary>Dernier calcul : candidats examinés et dénominateurs</summary>'+detail(q['latest_analysis'])+'</details><details><summary>Rejets conservés et raisons</summary>'+detail(q['rejected_reasons'])+'</details><details><summary>Qualité : définitions, temps publics et coûts</summary>'+detail({k:v for k,v in q.items() if k!='focused_cases'})+'</details>'
    content += '<h2>File de collecte et budgets</h2><p>La file répartit un budget borné entre exploration générale et marchés d’annonce documentés. Une interrogation terminée ne signifie pas un historique complet.</p>'
    queue=data['collection_queue'] or {}
    if queue:
        content+=f'<p>Dernière sélection : {queue["selected_count"]}/{queue["limit"]} places, dont {queue["exploration_selected"]} en exploration et {queue.get("targeting_selected",queue.get("announcement_selected",0))} en ciblage opérationnel. {queue["never_queried"]} marchés encore jamais interrogés ; {queue["revisits"]} déjà parcourus.</p>'
        strata=(queue.get('sampling') or {}).get('strata',[])
        positive=sum(s.get('population',0) for s in strata if isinstance(s.get('inclusion_probability'),(int,float)) and s['inclusion_probability']>0)
        population=sum(s.get('population',0) for s in strata)
        content+=f'<p>Tirage : probabilité d’inclusion positive documentée pour {positive}/{population} marchés du cadre stratifié décrit. Les probabilités sont conditionnelles au cadre découvert et au cycle ; les valeurs absentes restent inconnues.</p>'
        content+='<details><summary>Plan de tirage, probabilités et composantes inconnues</summary>'+detail(dict(sampling=queue.get('sampling'),unknown_components=(queue.get('targeting') or {}).get('unknown_components')))+'</details>'
        content+='<details><summary>Marchés sélectionnés et raisons</summary><div class="scroll"><table><tr><th>Marché</th><th>Motif</th><th>Probabilité d’inclusion</th><th>Dernière tentative</th></tr>'
        for item in queue['selected']:
            row=store.get('market',item['market_id']);market=row['payload'] if row else {}
            content+=f'<tr><td>{esc(market.get("question",item["market_id"]))}</td><td>{esc(item["selection_reason"])}</td><td>{esc(item.get("inclusion_probability","inconnue"))}</td><td>{times(item["last_attempt"])}</td></tr>'
        content+='</table></div></details><details><summary>Quotas, exclusions et mesure complète</summary>'+detail(queue)+'</details>'
    else:content+='<p>Première sélection en attente.</p>'
    content += '<h2>Évolution du stockage</h2><p>'+esc(data['storage_trends'].get('note','Mesures en attente'))+'</p><div class="scroll"><table><tr><th>Fenêtre UTC</th><th>Base</th><th>WAL</th><th>Rapports</th><th>Logs</th><th>Nouveaux trades</th><th>Mo/min logiques</th></tr>'
    for w in data['storage_trends']['windows'][-6:]:
        values=''.join(f'<td>{w["files"].get(k,{}).get("logical_bytes",0)/1e6:.3f} Mo</td>' for k in ('sqlite_main','wal','reports','logs'))
        content+=f'<tr><td>{times(w["start"])} → {times(w["end"])}</td>{values}<td>{w["unique_keys"].get("trade",0)}</td><td>{w["runtime_logical_mb_per_min"]:.3f}</td></tr>'
    content+='</table></div><details><summary>Mesures complètes et limites</summary>'+detail(data['storage_trends'])+'</details>'
    focused=q['focused_cases']
    content+='<h2>Dossiers de marchés d’annonce</h2><p>Sélection opérationnelle courante, parmi au plus 250 priorités examinées. Aucun score ne constitue une anomalie validée.</p>'
    if (store.root/'reports/revue-annonces-20261027.html').exists():
        content+='<p><a href="/reports/revue-annonces-20261027.html">Audit daté du 27 octobre : transactions, témoins et explications concurrentes</a></p>'
    for key,path in review_files(store.root).items():
        label='Revue du 29 octobre : collecte, preuves et blocages' if key=='restoration' else 'Complément ciblé : cinq reçus et soldes datés' if key=='targeted' else 'Étude chronologique : '+('NON_ESTIMABLE' if 'NON_ESTIMABLE' in path.read_text() else 'résultats et limites')
        content+=f'<p><a href="/review/{key}">{esc(label)}</a></p>'
    for case in focused:
        content+=f'<article><a href="/case/{esc(case["id"])}">{esc(case.get("event_title") or case["event_id"])}</a><p>{esc(case.get("wallet"))} · score exploratoire {esc(case.get("score"))} · {esc(case.get("status"))}</p><p>Transactions, références, explications concurrentes et complétude dans le dossier.</p></article>'
    if not focused:content+='<p>Aucun des candidats examinés (au plus 250) ne remplit les critères d’enquête automatique sur une annonce documentée.</p>'
    content += '<h2>Dossiers — priorité et apprentissage</h2><div class="scroll"><table><tr><th>Dossier</th><th>Adresse</th><th>Événement</th><th>Score exploratoire</th><th>État</th></tr>'
    cases = [store._object(r) for r in store.conn.execute("SELECT * FROM objects WHERE kind='case' ORDER BY json_extract(payload,'$.priority') DESC,COALESCE(json_extract(payload,'$.current'),1) DESC,json_extract(payload,'$.score') DESC,observed_at DESC LIMIT 30")]
    for r in cases:
        c = r['payload']
        content += f'<tr><td><a href="/case/{esc(r["key"])}">{esc(r["key"][:16])}</a></td><td><code>{esc(c.get("wallet"))}</code></td><td>{esc(c.get("event_id"))}</td><td>{esc(c.get("score"))}</td><td>{"priorité exploratoire" if c.get("priority") else "apprentissage / rétrospectif"} · {esc(c.get("status"))}</td></tr>'
    content += '</table></div><p class="muted">30 dossiers affichés au maximum ; dossiers et émissions antérieures conservés dans SQLite.</p><h2>Couverture et état des sources</h2><div class="scroll"><table><tr><th>Flux</th><th>État</th><th>Dernier contrôle</th><th>Détail</th></tr>'
    for r in data['health']:
        p = r['payload']
        status = p.get('status','inconnu')
        content += f'<tr><td>{esc(r["key"])}</td><td class="{"ok" if status in ("ok","empty") else "warn"}">{esc(status)}</td><td>{times(r["observed_at"])}</td><td>{esc(p.get("detail"))}<details><summary>Mesures</summary>{detail(p)}</details></td></tr>'
    content += '</table></div><details><summary>Lacunes et interruptions conservées</summary>'+detail(store.list('gap',50))+'</details><h2>Événements en cours</h2><div class="scroll"><table><tr><th>Événement</th><th>Priorité</th><th>Statut</th><th>Observé</th></tr>'
    for r in store.list('event',limit=100):
        p = r['payload']
        content += f'<tr><td><a href="/event/{esc(r["key"])}">{esc(p.get("title"))}</a></td><td>{esc(p.get("priority"))}</td><td>{"terminé" if p.get("closed") else "ouvert selon Gamma"}</td><td>{times(r["observed_at"])}</td></tr>'
    content += '</table></div><h2>Ressources et budgets</h2>'+detail(data['heartbeat'])
    content += '<h2>Rapports locaux</h2><ul>'
    for p in sorted((store.root/'reports').glob('*.html'),key=lambda p:p.stat().st_mtime,reverse=True)[:30]:
        content += f'<li><a href="/reports/{esc(p.name)}">{esc(p.name)}</a></li>'
    content += '</ul>'
    return page('Surveillance Polymarket',content,refresh=True)

def server(root,port):
    root = Path(root)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def do_GET(self):
            host = self.headers.get('Host','')
            if host not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):
                self.send_error(403)
                return
            path = unquote(urlsplit(self.path).path)
            store = Store(root)
            try:
                kind = 'text/html; charset=utf-8'
                if path == '/':
                    body = home_html(store)
                elif path == '/api/status':
                    body = json.dumps(snapshot(store),ensure_ascii=False)
                    kind = 'application/json; charset=utf-8'
                elif path.startswith('/case/'):
                    row = store.get('case',path[6:])
                    if not row:
                        self.send_error(404); return
                    inv = store.get('investigation',row['payload'].get('investigation_id',row['key']))
                    from .review import case_scope
                    context=case_scope(store,row['payload'])
                    context['quality']=case_quality(store,row['payload'],scope=context)
                    evidence=targeted_context(root,row['payload'])
                    if evidence:context['targeted_evidence']=evidence
                    presented=dict(row['payload'],review_context=context)
                    body = dossier_html(presented,inv['payload'] if inv else None)
                elif path.startswith('/event/'):
                    row = store.get('event',path[7:])
                    if not row:
                        self.send_error(404); return
                    body = page(row['payload'].get('title','Événement'),detail(row))
                elif path.startswith('/reports/'):
                    name = path[9:]
                    if Path(name).name != name or not name.endswith(('.html','.json','.json.gz')):
                        self.send_error(404); return
                    f = root/'reports'/name
                    archived=f.with_name(f.name+'.gz')
                    if not f.exists() and name.endswith(('.html','.json')) and archived.is_file() and not archived.is_symlink():
                        import gzip
                        body=gzip.decompress(archived.read_bytes())
                        if name.endswith('.json'):kind='application/json; charset=utf-8'
                    elif not f.is_file() or f.is_symlink():
                        self.send_error(404); return
                    elif name.endswith('.json.gz'):
                        body=f.read_bytes();kind='application/gzip'
                    else:
                        body = f.read_text()
                        if name.endswith('.json'):kind='application/json; charset=utf-8'
                elif path.startswith('/review/'):
                    f=review_files(root).get(path[8:])
                    if not f:
                        self.send_error(404);return
                    body=page('Revue datée — résultats et limites','<pre>'+esc(f.read_text())+'</pre>')
                else:
                    self.send_error(404); return
                raw = body if isinstance(body,bytes) else body.encode()
                self.send_response(200)
                self.send_header('Content-Type',kind)
                self.send_header('Content-Length',str(len(raw)))
                self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")
                self.send_header('X-Content-Type-Options','nosniff')
                self.send_header('Cache-Control','no-store')
                self.end_headers()
                self.wfile.write(raw)
            finally:
                store.close()
    httpd = ThreadingHTTPServer(('127.0.0.1',port),Handler)
    httpd.daemon_threads = True
    return httpd
