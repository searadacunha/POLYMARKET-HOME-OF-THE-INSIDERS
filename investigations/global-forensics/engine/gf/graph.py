"""Five layers that never merge into one notion of "same person". Every edge keeps the transaction and the level that prove it.

financial: money between addresses. control: an owner read on-chain. infrastructure: a service a flow touched, which is shared and proves no link.
behaviour: similar acts, kept apart from identity. market: a position in an outcome. A cluster here is a reading aid over money edges between
personal-sized addresses; hubs, services and contracts cannot join two accounts, and each association lists its reasons.
"""
import csv
import html
import json
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

from . import labels

FINANCIAL, CONTROL, INFRA, BEHAVIOUR, MARKET = 'financial', 'control', 'infrastructure', 'behaviour', 'market'
LAYERS = (FINANCIAL, CONTROL, INFRA, BEHAVIOUR, MARKET)
FIELDS = ('layer', 'source', 'target', 'kind', 'chain_id', 'block_number', 'block_hash', 'transaction_hash', 'log_index', 'contract', 'token', 'decimals', 'raw_amount', 'timestamp', 'data_source', 'decoding', 'level', 'data_class', 'role', 'direction', 'case', 'service', 'label_source', 'label_lineages', 'note')
JOINING_ROLES = ('transfer', 'deposit_path', 'withdrawal_path', 'internal_to_dossier', 'bridge_hop')


class Graph:
    def __init__(self):
        self.nodes, self.edges, self.seen = {}, [], set()

    def node(self, address, **attrs):
        node = self.nodes.setdefault(address, dict(id=address, cases=set(), kinds=set(), service=None, cls=None))
        for key, value in attrs.items():
            if key == 'case' and value:
                node['cases'].add(value)
            elif key == 'kind' and value:
                node['kinds'].add(value)
            elif value is not None:
                node[key] = value
        return node

    def add(self, layer, source, target, key, **fields):
        token = (layer, key)
        if token in self.seen:
            return
        self.seen.add(token)
        self.edges.append(dict(layer=layer, source=source, target=target, **fields))

    def add_trace(self, result):
        case, wallet = result['case'], result['wallet']
        self.node(wallet, case=case, kind='polymarket_wallet', cls='POLYMARKET_WALLET')
        for c in result.get('classes') or []:
            self.node(c['address'], cls=c.get('cls'), service=(c.get('label') or {}).get('name'))
        account = result.get('account') or {}
        for tag, read in (('latest', account.get('control_latest')), ('at_first_money', account.get('control_at_first_money'))):
            for owner in (read or {}).get('owners') or []:
                if owner != wallet:
                    self.node(owner, case=case, kind='owner_key')
                    self.add(CONTROL, owner, wallet, (owner, wallet, tag), kind='owner_read_onchain', level='ONCHAIN_READ', block_number=read.get('block'), note=f"{read.get('form')} {tag}", case=case, data_class='fresh', data_source='eth_call')
        for e in result['edges']:
            source, target = e['from'], e['to']
            for address in (source, target):
                self.node(address, case=case)
            fields = dict(kind=e['kind'], chain_id=e['chain_id'], block_number=e['block_number'], block_hash=e.get('block_hash'), transaction_hash=e['transaction_hash'], log_index=e.get('log_index'), contract=e.get('contract'), token=e.get('token'), decimals=e.get('decimals'), raw_amount=e['raw_amount'], timestamp=e['timestamp'], data_source=e.get('source'), decoding=e.get('decoding'), level=e.get('level'), data_class=e.get('data_class'), role=e.get('role'), direction=e.get('direction'), case=case, service=e.get('service'), label_source=e.get('label_source'), label_lineages=e.get('label_lineages'), note=e.get('note'))
            key = (e['chain_id'], e['transaction_hash'], e.get('log_index'), source, target, e['raw_amount'])
            if e.get('other_cls') in (labels.SERVICE, labels.HUB, labels.CONTRACT, 'ZERO_ADDRESS') or e.get('role') in ('bridge_payout', 'bridge_deposit', 'mint', 'burn'):
                self.add(INFRA, source, target, key, **fields)
            else:
                self.add(FINANCIAL, source, target, key, **fields)
            self._bridge_hop(e, fields, case)

    def _bridge_hop(self, e, fields, case):
        """A proved hop is money from the sender on one chain to the recipient on the other, so it can join files. The solver and the depository are infrastructure and never join anything. An unproved hop stays out."""
        if e.get('role') not in ('bridge_payout', 'bridge_deposit') or not e.get('note'):
            return
        try:
            hop = json.loads(e['note'])
        except ValueError:
            return
        if hop.get('proof') is not True:
            return
        low = lambda a: a.lower() if a and a.startswith('0x') else a
        sender = low(hop.get('sender')) or (e['from'] if e['role'] == 'bridge_deposit' else None)
        recipient = low(hop.get('recipient')) or (e['to'] if e['role'] == 'bridge_payout' else None)
        if not sender or not recipient or sender == recipient:
            return
        for address in (sender, recipient):
            self.node(address, case=case)
        self.add(FINANCIAL, sender, recipient, ('hop', hop.get('id') or e['transaction_hash'], sender, recipient), **dict(fields, kind='bridge_hop', role='bridge_hop', decoding='same id read on both chains' if hop.get('basis') else fields.get('decoding'), note=e['note']))

    def add_positions(self, wallet, lines, case=None):
        for line in lines:
            market = 'market:' + str(line['condition'])
            self.node(market, kind='market', title=line.get('title'))
            self.add(MARKET, wallet, market, (wallet, line['condition']), kind='position', note=json.dumps({k: line.get(k) for k in ('title', 'outcomes', 'capital_engaged', 'cash_result', 'trades', 'first', 'last')}), case=case, level='API_ROW', data_class='fresh', data_source='data-api /v2/activity')

    def links_between_cases(self):
        """Which dossiers share a personal-sized address on the financial layer, with the transactions that say so. Shared services never appear here."""
        by_address = defaultdict(lambda: defaultdict(list))
        for e in self.edges:
            if e['layer'] != FINANCIAL or e.get('role') not in JOINING_ROLES:
                continue
            for address in (e['source'], e['target']):
                node = self.nodes.get(address) or {}
                if node.get('cls') in (labels.SERVICE, labels.HUB, labels.CONTRACT, labels.UNREAD):
                    continue
                by_address[address][e['case']].append(e)
        out = []
        for address, cases in by_address.items():
            if len(cases) >= 2:
                sides = {c: sorted({x.get('direction') for x in rows}) for c, rows in cases.items()}
                on_funding = sum('funding' in v for v in sides.values())
                on_exit = sum('cashout' in v for v in sides.values())
                relation = 'COMMON_FUNDER_CANDIDATE' if on_funding >= 2 else 'COMMON_DESTINATION_CANDIDATE' if on_exit >= 2 and not on_funding else 'FUNDING_OF_ONE_EXIT_OF_ANOTHER'
                out.append(dict(address=address, cases=sorted(cases), cls=(self.nodes.get(address) or {}).get('cls'), relation=relation, sides=sides, evidence={c: [dict(tx=x['transaction_hash'], chain=x['chain_id'], token=x.get('token'), raw=x['raw_amount'], level=x.get('level'), direction=x.get('direction'), role=x.get('role')) for x in rows[:6]] for c, rows in cases.items()}, ownership='OWNERSHIP_NOT_ESTABLISHED', reading='Money touched this address in both files. A candidate relation by direction, read from the walks. Common ownership is not established.'))
        return sorted(out, key=lambda x: (-len(x['cases']), x['address']))

    def flows(self):
        """For each file: who paid in, the account, its markets, what left and where to, every line with its proof, ordered from the farthest funder to the last destination."""
        out = defaultdict(lambda: dict(funding=[], account_markets=[], cashout=[], control=[]))
        for e in self.edges:
            slot = out[e.get('case')]
            line = {k: e.get(k) for k in ('source', 'target', 'role', 'kind', 'chain_id', 'block_number', 'block_hash', 'transaction_hash', 'log_index', 'token', 'decimals', 'raw_amount', 'timestamp', 'level', 'data_class', 'service', 'layer')}
            if e['layer'] == MARKET:
                slot['account_markets'].append(dict(market=e['target'], note=e.get('note')))
            elif e['layer'] == CONTROL:
                slot['control'].append(line)
            else:
                slot['funding' if e.get('direction') == 'funding' else 'cashout'].append(line)
        for slot in out.values():
            slot['funding'].sort(key=lambda x: x['timestamp'] or 0)
            slot['cashout'].sort(key=lambda x: x['timestamp'] or 0)
        return dict(out)

    def export(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        nodes = [dict(n, cases=sorted(n['cases']), kinds=sorted(n['kinds'])) for n in self.nodes.values()]
        (directory / 'nodes.json').write_text(json.dumps(nodes, indent=0, sort_keys=True))
        (directory / 'edges.json').write_text(json.dumps(self.edges, indent=0, sort_keys=True))
        with (directory / 'edges.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.edges)
        root = ET.Element('graphml', xmlns='http://graphml.graphdrawing.org/xmlns')
        for field in FIELDS:
            ET.SubElement(root, 'key', id=field, **{'for': 'edge', 'attr.name': field, 'attr.type': 'string'})
        for attr in ('cls', 'service'):
            ET.SubElement(root, 'key', id='n_' + attr, **{'for': 'node', 'attr.name': attr, 'attr.type': 'string'})
        graph = ET.SubElement(root, 'graph', edgedefault='directed', id='global-forensics')
        for n in nodes:
            item = ET.SubElement(graph, 'node', id=n['id'])
            for attr in ('cls', 'service'):
                if n.get(attr):
                    ET.SubElement(item, 'data', key='n_' + attr).text = str(n[attr])
        for i, e in enumerate(self.edges):
            item = ET.SubElement(graph, 'edge', id=f'e{i}', source=e['source'], target=e['target'])
            for field in FIELDS:
                if e.get(field) is not None:
                    ET.SubElement(item, 'data', key=field).text = str(e[field])
        ET.ElementTree(root).write(directory / 'graph.graphml', encoding='utf-8', xml_declaration=True)
        (directory / 'viewer.html').write_text(viewer(nodes, self.edges))
        (directory / 'flows.json').write_text(json.dumps(self.flows(), indent=0, sort_keys=True))
        return dict(nodes=len(nodes), edges=len(self.edges), by_layer={l: sum(1 for e in self.edges if e['layer'] == l) for l in LAYERS})


EXPLORER = {1: 'https://etherscan.io/tx/', 137: 'https://polygonscan.com/tx/', 42161: 'https://arbiscan.io/tx/', 10: 'https://optimistic.etherscan.io/tx/', 8453: 'https://basescan.org/tx/', 56: 'https://bscscan.com/tx/'}


def viewer(nodes, edges):
    """A self-contained page: filter by layer and case, click a relation to read its transaction and proof. No external script."""
    keep = ('layer', 'source', 'target', 'kind', 'chain_id', 'block_number', 'block_hash', 'transaction_hash', 'log_index', 'token', 'raw_amount', 'decimals', 'timestamp', 'decoding', 'level', 'data_class', 'role', 'direction', 'case', 'service', 'label_source', 'note')
    data = json.dumps(dict(nodes=[{k: n.get(k) for k in ('id', 'cls', 'service', 'cases', 'kinds', 'title')} for n in nodes], edges=[{k: e.get(k) for k in keep} for e in edges], explorers=EXPLORER)).replace('</', '<\\/')
    return VIEWER.replace('/*DATA*/', data)


VIEWER = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Multilayer graph, global forensics</title><style>
:root{--bg:#fff;--fg:#1a1a1a;--mute:#666;--line:#ddd;--panel:#f6f6f4}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--mute:#aaa;--line:#333;--panel:#202020}}
body{margin:0;font:14px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--fg);display:grid;grid-template-columns:1fr 380px;grid-template-rows:auto 1fr;height:100vh}
header{grid-column:1/3;padding:8px 12px;border-bottom:1px solid var(--line);display:flex;gap:14px;flex-wrap:wrap;align-items:center}
canvas{width:100%;height:100%;display:block;cursor:grab}#side{overflow:auto;padding:12px;border-left:1px solid var(--line);background:var(--panel)}
code{font-size:12px;word-break:break-all}.m{color:var(--mute)}a{color:inherit}label{white-space:nowrap}
</style></head><body><header><b>Money is not identity.</b><span class="m">An edge shows a transfer or a read, never a common owner.</span><span id="layers"></span><select id="case" aria-label="Filter by file"><option value="">All files</option></select><span class="m" id="count"></span></header>
<canvas id="c" aria-label="Graph of addresses and relations" tabindex="0"></canvas><div id="side"><p class="m">Click an address or a relation. Scroll to zoom, drag to pan.</p></div>
<script>const D=/*DATA*/;
const COLOR={financial:'#2a78b5',control:'#a23b72',infrastructure:'#999',behaviour:'#d9822b',market:'#3a9d5d'};
const cv=document.getElementById('c'),ctx=cv.getContext('2d');let view={x:0,y:0,k:1},on=new Set(['financial','control','market']),only='';
const N=new Map(D.nodes.map((n,i)=>[n.id,Object.assign(n,{x:Math.cos(i)*(50+i*2),y:Math.sin(i)*(50+i*2),vx:0,vy:0})]));
const L=D.edges.filter(e=>N.has(e.source)&&N.has(e.target));
function vis(){return L.filter(e=>on.has(e.layer)&&(!only||e.case===only))}
const lay=document.getElementById('layers');Object.keys(COLOR).forEach(l=>{const c=document.createElement('label');c.innerHTML=`<input type=checkbox ${on.has(l)?'checked':''}> <span style="color:${COLOR[l]}">${l}</span> `;c.firstChild.onchange=e=>{e.target.checked?on.add(l):on.delete(l);tick=0};lay.append(c)});
const sel=document.getElementById('case');[...new Set(L.map(e=>e.case).filter(Boolean))].sort().forEach(c=>{const o=document.createElement('option');o.textContent=c;sel.append(o)});sel.onchange=()=>{only=sel.value;tick=0};
let tick=0;function step(){const E=vis(),A=[...new Set(E.flatMap(e=>[N.get(e.source),N.get(e.target)]))];document.getElementById('count').textContent=`${A.length} addresses, ${E.length} relations`;
if(tick<500){tick++;for(const a of A){for(const b of A){if(a===b)continue;const dx=a.x-b.x,dy=a.y-b.y,d=dx*dx+dy*dy+.01;if(d<90000){a.vx+=dx/d*40;a.vy+=dy/d*40}}a.vx-=a.x*.002;a.vy-=a.y*.002}for(const e of E){const a=N.get(e.source),b=N.get(e.target),dx=b.x-a.x,dy=b.y-a.y;a.vx+=dx*.004;a.vy+=dy*.004;b.vx-=dx*.004;b.vy-=dy*.004}for(const a of A){a.x+=a.vx*=.8;a.y+=a.vy*=.8}}
const r=cv.getBoundingClientRect();if(cv.width!==r.width){cv.width=r.width;cv.height=r.height}ctx.clearRect(0,0,cv.width,cv.height);ctx.save();ctx.translate(cv.width/2+view.x,cv.height/2+view.y);ctx.scale(view.k,view.k);
for(const e of E){const a=N.get(e.source),b=N.get(e.target);ctx.strokeStyle=COLOR[e.layer];ctx.lineWidth=1/view.k;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}
for(const a of A){ctx.fillStyle=(a.kinds||[]).includes('polymarket_wallet')?'#c2410c':a.cls==='SERVICE'||a.cls==='HUB_MEASURED'?'#999':'#2a78b5';ctx.beginPath();ctx.arc(a.x,a.y,((a.kinds||[]).includes('polymarket_wallet')?6:3.5)/view.k,0,7);ctx.fill()}ctx.restore();requestAnimationFrame(step)}step();
function world(ev){const r=cv.getBoundingClientRect();return[(ev.clientX-r.left-cv.width/2-view.x)/view.k,(ev.clientY-r.top-cv.height/2-view.y)/view.k]}
let drag=null;cv.onmousedown=ev=>drag=[ev.clientX,ev.clientY];window.onmouseup=()=>drag=null;window.onmousemove=ev=>{if(drag){view.x+=ev.clientX-drag[0];view.y+=ev.clientY-drag[1];drag=[ev.clientX,ev.clientY]}};cv.onwheel=ev=>{ev.preventDefault();view.k*=ev.deltaY<0?1.15:.87};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function show(e){const u=D.explorers[e.chain_id];const amt=e.raw_amount&&e.decimals!=null?(Number(e.raw_amount)/10**e.decimals).toLocaleString():'';document.getElementById('side').innerHTML=`<h3>${esc(e.layer)} relation</h3><p><b>${esc(e.role||e.kind)}</b> ${esc(amt)} ${esc(e.token)}</p><p class=m>Level: ${esc(e.level)}, data: ${esc(e.data_class)}</p><p>From <code>${esc(e.source)}</code><br>To <code>${esc(e.target)}</code></p>${e.transaction_hash?`<p>Tx <code>${esc(e.transaction_hash)}</code>${u?` <a href="${u+esc(e.transaction_hash)}" rel="noreferrer">explorer</a>`:''}</p>`:''}<p class=m>Chain ${esc(e.chain_id)}, block ${esc(e.block_number)}, log ${esc(e.log_index)}<br>Block hash <code>${esc(e.block_hash)}</code><br>Time ${e.timestamp?new Date(e.timestamp*1000).toISOString():''}</p><p class=m>Decoding: ${esc(e.decoding)}</p>${e.service?`<p>Service: ${esc(e.service)}<br><span class=m>Label source: ${esc(e.label_source)}</span></p>`:''}${e.note?`<p class=m><code>${esc(e.note)}</code></p>`:''}<p class=m>File: ${esc(e.case)}. Ownership not established.</p>`}
function showNode(a){const E=vis().filter(e=>e.source===a.id||e.target===a.id);document.getElementById('side').innerHTML=`<h3>Address</h3><p><code>${esc(a.id)}</code></p><p>${esc(a.cls)} ${esc(a.service)}</p><p class=m>Files: ${esc((a.cases||[]).join(', '))}</p><p>${E.length} relation(s):</p>`+E.slice(0,60).map((e,i)=>`<p><a href="#" data-i="${L.indexOf(e)}">${esc(e.role||e.kind)} ${esc(e.token)} ${e.timestamp?new Date(e.timestamp*1000).toISOString().slice(0,16):''}</a></p>`).join('');document.querySelectorAll('#side a[data-i]').forEach(x=>x.onclick=ev=>{ev.preventDefault();show(L[+x.dataset.i])})}
cv.onclick=ev=>{const[x,y]=world(ev);let best=null,bd=64/view.k/view.k;for(const e of vis())for(const id of[e.source,e.target]){const a=N.get(id),d=(a.x-x)**2+(a.y-y)**2;if(d<bd){bd=d;best=a}}if(best)return showNode(best);let be=null,bl=25/view.k/view.k;for(const e of vis()){const a=N.get(e.source),b=N.get(e.target),dx=b.x-a.x,dy=b.y-a.y,t=Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy||1))),d=(a.x+t*dx-x)**2+(a.y+t*dy-y)**2;if(d<bl){bl=d;be=e}}if(be)show(be)};
</script></body></html>'''
