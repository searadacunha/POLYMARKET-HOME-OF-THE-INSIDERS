"""Builds data/*.csv and graphs/changenow_network.graphml from the archived answers. No network. Amounts stay exact: raw integers, decimals, Decimal division."""
import csv, gzip, hashlib, json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
import datetime
ROOT = Path(__file__).resolve().parent.parent
INV = Path.home() / 'Projects/PolySentinel-investigation'
SLUGS = 'thin vidente cookedrice wen 0x86544e4dfde brace227 walletwallet8424 zoomman17 kraben006 ouldlm3alem 0xdd97e6'.split()
HOT3, DEP, HW4, RELAY = '0xdd3d72c53ff982ff59853da71158bf1538b3ceee', '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1', '0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23'
KRAB, BRACE, FUND, HTXDEP, WATCH = '0x101b5f4dc0886c32e2b75972101aeaf9f338fb65', '0xc852b0938f5ad79b640d105ed11c14499454af26', '0x3eaef6d5e91ecf7b7623eb19978e145ebd417013', '0x66d582e5e0670bd99153199f179733c6ee5d19be', '0xcc0f311eb2c688f30bc9aadb42781e46899723f7'
BN = 'metadata.services.blockscout.com/api/v1/metadata, addresses[a].tags, lu le 2026-11-02'
p9, p10, p12, p13, p14, p15 = (json.load(open(ROOT / f'state/p{n}.json')) for n in (9, 10, 12, 13, 14, 15))
fig = json.load(open(ROOT / 'state/figures.json'))
manifest = {r['file']: r for r in csv.DictReader(open(ROOT / 'evidence/api/MANIFEST.csv'))}


def exact(raw, dec):
    return format((Decimal(int(raw)) / (Decimal(10) ** int(dec))).normalize(), 'f')


# --- verified transfers
HTXHOT, BRIDGERS, B6B, EBAB, CN22, BINANCE34, CAD, C52 = '0xa03400e098f4421b34a3a44a1b4e571419517687', '0xb685760ebd368a891f27ae547391f4e2a289895b', '0x6b33c41cac7db6726dd1240bc8bbce5e6dbb2180', '0xebaba1d649be1e293a8a9e37b0f59f166b025d1f', '0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a', '0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055', '0xcad97616f91872c02ba3553db315db4015cbe850', '0x52c21f32f2cc1d49d1ee0f17515fb92963b0a606'
LAB = {HOT3: 'ChangeNOW: Hot Wallet 3', HW4: 'ChangeNOW: Hot Wallet 4', DEP: 'ChangeNOW Dep: 0x3f3...07B', CN22: 'ChangeNOW 22'}
SOURCE = {HOT3: 'Blockscout metadata (pas de tag public Etherscan au 2026-11-02) ; copies Arkham et AMLBot de seconde main', HW4: 'Etherscan Public Name Tag et Blockscout (meme nom) ; ChangeNOW 16 par OLI, compilation hildobby', DEP: 'Etherscan Public Name Tag et Blockscout (meme nom, une seule source)', CN22: 'dawsbot et PolygonScan de seconde main, hildobby selon cette source ; source unique de famille, non recoupee'}
PROOF = {HOT3: 'Liens on-chain avec HW4, ChangeNOW 2, 17, HTX Deposit : data/attribution_links.csv', HW4: 'Deux origines d etiquette (Etherscan, hildobby) ; liens on-chain avec HOT3, 0x3f3ee0a9, ChangeNOW 10', DEP: 'Liens on-chain avec HW4, ChangeNOW 10, 21, (0x4778). Niveau conditionne a l independance de hildobby et Etherscan', CN22: 'Etiquette seule, aucune corroboration'}
NO_LABEL = 'aucune etiquette sur les deux adresses'
NO_PROOF = 'sans objet : ce transfert ne touche pas une adresse etiquetee ChangeNOW'
REL = {
    (HOT3, KRAB): ('kraben006', 'Paiement du service vers la cle proprietaire', 2, 'Autre payeur que le client (commande creee par un tiers), remboursement vers une refundAddress, partenaire en marque blanche', 'Ordre, actif source et chaine source non publics'),
    (KRAB, RELAY): ('kraben006', 'Cle vers adresse a usage unique sans etiquette : chemin indirect, depot deduit de l empreinte', 0, 'Facture payee pour un tiers, private transfer ChangeNOW, autre service partageant le meme logiciel', 'Actif de sortie et destination non publics ; relais sans etiquette, statut deduit de son empreinte'),
    (RELAY, DEP): ('kraben006', 'Balayage automatique 492 s plus tard vers le service', 2, 'Autre service partageant le meme logiciel', 'Ce balayage est interne au service et ne dit rien de la sortie'),
    (KRAB, HTXDEP): ('kraben006', 'Sortie de la cle apres les deux paiements', 0, 'Adresse de depot HTX d un tiers, ou compte OTC', 'Compte HTX non public ; aucune etiquette sur 0x66d582e5, statut deduit de ses sorties'),
    (HOT3, HTXDEP): ('kraben006', 'Inverse : le service paie aussi la destination de la cle', 2, 'Autre client du service, adresse de depot HTX ouverte a tous les payeurs', 'Rien ne relie cet ordre au compte kraben006'),
    (HOT3, FUND): ('brace227', 'Service vers un financeur ancien de la cle, 21 mois avant les paris', 2, 'Adresse de paiement d un tiers ou OTC : ses 9 sorties vont a 9 destinataires', 'Proprietaire de 0x3eaef6d5 inconnu'),
    (HW4, FUND): ('brace227', 'Service vers le meme financeur, ETH de gaz possible', 2, 'Idem', 'Proprietaire de 0x3eaef6d5 inconnu'),
    (FUND, BRACE): ('brace227', 'Financeur vers la cle, 84 s apres le paiement du service', 0, 'Paiement de 0x3eaef6d5 a un tiers, comme ses 8 autres sorties', 'Le lien entre la cle et le service reste indirect'),
    (BRACE, KRAB): ('brace227 et kraben006', 'Transfert direct deja etabli, hors service', 0, 'Don de gaz, cle commune, service rendu', 'Aucune etiquette, ne prouve pas la coordination'),
    (HW4, WATCH): ('walletwallet8424', 'Service vers un financeur a fort trafic', 2, 'Adresse mutualisee de 672 contreparties : ne dit rien du compte', 'Aucun lien avec le compte au-dela de ce financeur mutualise'),
    (HOT3, '0x1086c953cea1280c1afc87713a614dc464f7d7f7'): ('kraben006', 'Inverse : un destinataire de la cle recoit aussi du service', 2, 'Adresse Cryptomus probable, service de paiement', 'Rien ne relie cet ordre au compte'),
    (HW4, '0x50e3a360ba9bc0accfbc216e0544bfe53d49ba12'): ('kraben006', 'Inverse : un destinataire de la cle recoit aussi du service', 2, 'Contrat ou portefeuille de tiers', 'Rien ne relie cet ordre au compte'),
    (HW4, '0xe52b6693fa225adf73fd2a36b1799bc66f3327bb'): ('kraben006', 'Inverse : un destinataire de la cle recoit aussi du service', 2, 'Contrat ou portefeuille de tiers', 'Rien ne relie cet ordre au compte'),
    (HOT3, '0xe52b6693fa225adf73fd2a36b1799bc66f3327bb'): ('kraben006', 'Inverse : un destinataire de la cle recoit aussi du service', 2, 'Contrat ou portefeuille de tiers', 'Rien ne relie cet ordre au compte'),
    (KRAB, C52): ('kraben006', 'Sortie mineure de la cle, comptee dans le solde', 0, 'Paiement ordinaire', 'Hors chemin ChangeNOW'),
    (CAD, KRAB): ('kraben006', 'Entree mineure de la cle, comptee dans le solde', 0, 'Paiement ordinaire', 'Hors chemin ChangeNOW'),
    (HTXDEP, HTXHOT): ('kraben006', 'Ramassage du depot 72 s plus tard par le portefeuille HTX', 0, 'Automatique cote plateforme', 'Compte HTX non public'),
    (BRACE, B6B): ('brace227', 'Sortie de 285 USDT 3 min apres la reception', 0, 'Paiement ordinaire', 'Aval suivi sur un saut'),
    (B6B, EBAB): ('brace227', 'Sortie suivante, 18 min 36 s plus tard', 0, 'Paiement ordinaire', 'Non suivie au-dela'),
    (BRACE, BRIDGERS): ('brace227', 'Reste du solde USDT, qui passe a 0', 0, 'Echange ordinaire', 'Sortie de Bridgers non attribuee ici'),
    (BINANCE34, CN22): ('ouldlm3alem et wen : aucun lien', 'Flux entre deux services : Binance: Hot Wallet 34 vers ChangeNOW 22, faux positif', 1, 'Compte de service a service', 'Aucune relation avec les comptes'),
}
rows = []
for r in p12['ok']:
    rows.append(dict(r, amount=exact(r['raw'], r['decimals'])))
for x in p14['proofs']:
    if x['kind'] == 'second_hop_reverse' and x['node_ok']:
        body = (ROOT / 'evidence/onchain' / f"{x['tx']}.json").read_bytes()
        native = not x['sym']
        dec = 18 if native else 6
        rows.append(dict(chain_id=1, tx=x['tx'], block=x['block'], utc=x['utc'], event='native_transaction' if native else 'erc20_transfer_log', log_index='', token='ETH' if native else x['sym'], contract=x['contract'], decimals=dec, raw=x['raw'], amount=exact(x['raw'], dec), src=x['src'], dst=x['dst'], node_proof_sha256=hashlib.sha256(body).hexdigest(), node_ok=True))
SYMBOL = {'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 'USDC', '0xdac17f958d2ee523a2206206994597c13d831ec7': 'USDT', '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359': 'USDC', '0x2791bca1f2de4661ed88a30c99a7a9449aa84174': 'USDC.e'}
for x in fig['supporting_proofs']:
    for l in x['logs']:
        if (l['src'], l['dst']) in REL and l['contract'] in SYMBOL:
            body = (ROOT / 'evidence/onchain' / f"{x['tx']}.json").read_bytes()
            rows.append(dict(chain_id=x['chain_id'], tx=x['tx'], block=x['block'], utc=x['utc'], event='erc20_transfer_log', log_index=l['log_index'], token=SYMBOL[l['contract']], contract=l['contract'], decimals=6, raw=l['raw'], amount=exact(l['raw'], 6), src=l['src'], dst=l['dst'], node_proof_sha256=hashlib.sha256(body).hexdigest(), node_ok=x['status'] == 1))
rows.sort(key=lambda r: r['utc'])
cols = ['case', 'chain_id', 'tx', 'block', 'utc', 'event', 'log_index', 'token', 'contract', 'decimals', 'raw', 'amount', 'src', 'dst', 'service_label', 'label_source', 'attribution_proof', 'relation_to_account', 'proof_level', 'alternatives', 'visibility_limit', 'node_proof_file', 'node_proof_sha256', 'node_ok']
with (ROOT / 'data/verified_transfers.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        case, rel, lvl, alt, lim = REL[(r['src'], r['dst'])]
        svc = r['src'] if r['src'] in LAB else (r['dst'] if r['dst'] in LAB else None)
        w.writerow({**{k: r.get(k, '') for k in cols}, 'case': case, 'service_label': LAB.get(svc, 'aucune'), 'label_source': SOURCE.get(svc, NO_LABEL), 'attribution_proof': PROOF.get(svc, 'empreinte de balayage, sans etiquette : reports/ATTRIBUTION_EVIDENCE.md section F' if RELAY in (r['src'], r['dst']) else NO_PROOF), 'relation_to_account': rel, 'proof_level': lvl, 'alternatives': alt, 'visibility_limit': lim, 'node_proof_file': f"evidence/onchain/{r['tx']}.json"})
print('verified_transfers', len(rows))
# --- attribution links
agg = defaultdict(lambda: dict(n=0, raw=0, first=None, last=None, tx=None, dec=18, read=0))
for l in p9['links']:
    for h in l['hits']:
        me = DEP if DEP in (h['f'], h['to']) else HOT3
        d = 'labeled_to_studied' if h['to'] == me else 'studied_to_labeled'
        a = agg[(l['address'], l['names'][0], me, d, h['sym'] or 'ETH')]
        a['n'] += 1
        a['raw'] += int(h['v'])
        a['dec'] = int(h['dec'] or 18)
        a['first'] = min(a['first'] or h['t'], h['t'])
        a['last'] = max(a['last'] or h['t'], h['t'])
        a['tx'] = a['tx'] or h['h']
        a['read'] = l['read']
T = lambda x: datetime.datetime.fromtimestamp(int(x), datetime.UTC).strftime('%Y-%m-%d %H:%M:%S') if x else ''
proofs = {x['tx']: x for x in p14['proofs']}
with (ROOT / 'data/attribution_links.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['group', 'labeled_address', 'label', 'studied_address', 'direction', 'token', 'n_rows', 'sum_exact', 'first_utc', 'last_utc', 'rows_read_from_labeled_side', 'example_tx', 'node_verified'])
    for (addr, name, me, d, sym), a in sorted(agg.items(), key=lambda kv: -kv[1]['n']):
        w.writerow(['changenow_labeled', addr, name, me, d, sym, a['n'], exact(a['raw'], a['dec']), T(a['first']), T(a['last']), a['read'], a['tx'], bool(proofs.get(a['tx'], {}).get('node_ok'))])
    known_lineage = set()
    for x in p15['lineage']:
        known_lineage.add(x['tx'])
        w.writerow(['funder_lineage', x['src'], '', x['dst'], 'src_to_dst', 'ETH', 1, exact(x['raw'], 18), x['utc'], x['utc'], '', x['tx'], x['node_ok']])
    for x in fig['supporting_proofs']:
        if x['tx'] not in known_lineage and not x['logs'] and int(x['value']) > 0:
            w.writerow(['funder_lineage', x['src'], '', x['dst'], 'src_to_dst', 'ETH', 1, exact(x['value'], 18), x['utc'], x['utc'], '', x['tx'], x['status'] == 1])
    for c in p10['controls']:
        w.writerow(['control_other_service', c['address'], c['name'], 'hot3 and dep', 'any', c['action'], c['hits'], '0', T(c['first']), T(c['last']), c['read'], '', False])
print('attribution links', len(agg))
# --- candidates
uni = defaultdict(lambda: defaultdict(set))
for r in csv.DictReader(open(ROOT / 'state/universe_raw.csv')):
    a = r['address']
    uni[a][r['chain_id']].add((r['name'], r['source'], r['source_kind']))
for src, tag in ((p9['dep_cp_tags'], 'depcp'), (p9['hot3_cp_tags'], 'hotcp')):
    for a, names in src.items():
        if 'changenow' in ' '.join(names).lower():
            uni[a]['1'].add((' / '.join(names), BN, 'blockscout'))
for x in p14['sib']:
    uni[x['address']]['1'].add(('tag protocole changenow-dep', 'metadata.services.blockscout.com/api/v1/addresses?slug=changenow-dep&tagType=protocol&chainId=1', 'blockscout'))
ROLE = {
    HOT3: ('kraben006 direct ; brace227 indirect', 2, 'Marque blanche ou partenaire ; attribution non confirmee par ChangeNOW ; pas de tag public Etherscan', 'Ordres invisibles'),
    DEP: ('kraben006 via 0x7e67df45', 2, 'Autre service au meme logiciel ; le tag DEPOSIT ADDRESS est trompeur ; niveau conditionne a l independance de hildobby et Etherscan', 'Ordres invisibles'),
    HW4: ('brace227 indirect ; walletwallet8424 tres indirect', 2, 'Marque blanche ou partenaire', 'Ordres invisibles'),
    RELAY: ('kraben006, chemin indirect, depot deduit de l empreinte', 0, 'Aucune etiquette : ni le niveau 1 ni un ordre', 'Ordre non public'),
    CN22: ('Aucune pour les comptes : Binance paie ChangeNOW 22', 1, 'Flux de service a service', 'Etiquette seule'),
}
uni[RELAY]['1'].add(('aucune etiquette, empreinte de balayage', 'mesure de cette etude, state/p10.json et state/p14.json', 'behaviour'))
EV = {'etherscan_page': 'evidence/api/etherscan_page_dep_0x3f3ee0a9.html', 'blockscout': 'evidence/api/bs_labels_direct.json', 'dawsbot': 'evidence/labels/changenow_rows.json', 'brianleect': 'evidence/labels/changenow_rows.json', 'arkham_copy': 'evidence/repos/thirdparty/Xaxrich__okx-ai-quant-lab__arkham_entity_labeled_transfers.csv.txt', 'amlbot_copy': 'evidence/repos/thirdparty/opun__amlbot-agent__example-6.json.txt', 'github_list': 'evidence/repos/thirdparty/PeLegend__BlockchainAnalysis__wallets_exchange.csv.txt', 'services_json': 'evidence/labels/services_changenow_rows.json', 'behaviour': 'state/p14.json'}
OWN = {HOT3: 'evidence/api/blockscout_metadata_hot3_0xdd3d72c5.json', DEP: 'evidence/api/blockscout_metadata_dep_0x3f3ee0a9.json', HW4: 'evidence/api/blockscout_metadata_hot4_0xeba88149.json', RELAY: 'evidence/api/blockscout_metadata_relay_0x7e67df45.json'}
first_contact = {}
for r in rows:
    for a in (r['src'], r['dst']):
        first_contact.setdefault(a, (r['tx'], r['utc'], f"{r['amount']} {r['token']}", 'verified_transfers'))
for (addr, name, me, d, sym), a_ in agg.items():
    first_contact.setdefault(addr, (a_['tx'], T(a_['first']), f"{exact(a_['raw'], a_['dec'])} {sym} sur {a_['n']} lignes", 'attribution_links'))
cols = ['address', 'chain_id', 'labels', 'label_sources', 'source_families', 'contact_tx', 'contact_utc', 'contact_amount', 'contact_table', 'attribution_proof', 'relation_to_accounts', 'proof_level', 'alternatives', 'visibility_limit', 'evidence_file', 'evidence_sha256']
n = 0
with (ROOT / 'data/changenow_candidates.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(cols)
    for a in sorted(uni):
        for chain in sorted(uni[a]):
            v = uni[a][chain]
            linked = a in first_contact and first_contact[a][3] == 'attribution_links'
            rel, lvl, alt, lim = ROLE.get(a, ('Aucun contact lu avec les 11 comptes', 1, 'Etiquette seule', 'Source unique ou copie'))
            ev = OWN.get(a) or EV[sorted(x[2] for x in v)[0]]
            sha = hashlib.sha256((ROOT / ev).read_bytes()).hexdigest() if (ROOT / ev).exists() else ''
            c = first_contact.get(a, ('', '', '', ''))
            proof = PROOF.get(a, 'Empreinte de balayage' if a == RELAY else ('Liens on-chain lus avec 0xdd3d72c5 ou 0x3f3ee0a9 : data/attribution_links.csv' if linked else 'Etiquette seule, non testee'))
            w.writerow([a, chain, ' | '.join(sorted({x[0] for x in v})), ' | '.join(sorted({x[1][:130] for x in v})), ' | '.join(sorted({x[2] for x in v})), c[0], c[1], c[2], c[3], proof, rel, lvl, alt, lim, ev, sha])
            n += 1
print('candidates', n, len(uni))
# --- graph: one edge per verified transfer, one per attribution link
nodes, edges = {}, []


def node(a, kind, label=''):
    if a not in nodes or (label and not nodes[a][1]):
        nodes[a] = (kind, label)


for s_ in SLUGS:
    d = json.load(open(INV / f'cases/{s_}.json'))
    w_ = d['wallet']['address'].lower()
    k = next(iter(d['owner_nonces'])).lower()
    node(w_, 'polymarket_wallet', d['label'])
    node(k, 'owner_key', d['label'])
    edges.append(dict(s=k, t=w_, kind='owner_of', chain='137', tx='', utc='', token='', amount='', level='', source='owner() on chain, investigation cases', limit='Ne prouve pas une personne'))
for a, l in ((HOT3, 'ChangeNOW: Hot Wallet 3'), (DEP, 'ChangeNOW Dep: 0x3f3...07B'), (HW4, 'ChangeNOW: Hot Wallet 4'), (CN22, 'ChangeNOW 22'), (HTXHOT, 'HTX: Hot Wallet'), (BINANCE34, 'Binance: Hot Wallet 34')):
    node(a, 'labeled_service', l)
node(RELAY, 'candidate_payin_no_label')
node(FUND, 'unattributed_payment_wallet')
node(HTXDEP, 'htx_deposit_by_behaviour')
node(WATCH, 'high_volume_unattributed')
node('0xa2768df0b1fb437d5d238d5d0e9b7ca584e84628', 'upstream_no_label')
node('0xb2c257557fd1c7a0738d7e9e2c953441f333b8fd', 'upstream_no_label')
for r in rows:
    node(r['src'], 'other')
    node(r['dst'], 'other')
    svc = r['src'] if r['src'] in LAB else (r['dst'] if r['dst'] in LAB else None)
    edges.append(dict(s=r['src'], t=r['dst'], kind='verified_transfer', chain=str(r['chain_id']), tx=r['tx'], utc=r['utc'], token=r['token'], amount=r['amount'], level=str(REL[(r['src'], r['dst'])][2]), source=SOURCE.get(svc, NO_LABEL), limit=REL[(r['src'], r['dst'])][4]))
for (addr, name, me, d, sym), a_ in agg.items():
    node(addr, 'changenow_labeled', name)
    s_, t_ = (addr, me) if d == 'labeled_to_studied' else (me, addr)
    edges.append(dict(s=s_, t=t_, kind='attribution_link', chain='1', tx=a_['tx'], utc=f"{T(a_['first'])} a {T(a_['last'])}", token=sym, amount=exact(a_['raw'], a_['dec']), level='', source=f"{a_['n']} lignes lues du cote de {name}", limit='Dernieres 1000 lignes seulement'))
for x in list(p15['lineage']) + [dict(src=y['src'], dst=y['dst'], raw=y['value'], utc=y['utc'], tx=y['tx']) for y in fig['supporting_proofs'] if not y['logs'] and int(y['value']) > 0]:
    node(x['src'], 'other')
    node(x['dst'], 'other')
    edges.append(dict(s=x['src'], t=x['dst'], kind='upstream_lineage', chain='1', tx=x['tx'], utc=x['utc'], token='ETH', amount=exact(x['raw'], 18), level='', source='Lecture de nœud', limit='Lien d adresses, pas d operateur prouve'))
FIELDS = ('kind', 'chain', 'tx', 'utc', 'token', 'amount', 'level', 'source', 'limit')
out = ['<?xml version="1.0" encoding="UTF-8"?>', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">', '<key id="node_kind" for="node" attr.name="kind" attr.type="string"/>', '<key id="node_label" for="node" attr.name="label" attr.type="string"/>']
for k in FIELDS:
    out.append(f'<key id="e_{k}" for="edge" attr.name="{k}" attr.type="string"/>')
out.append('<graph id="changenow" edgedefault="directed">')
for a, (k, l) in sorted(nodes.items()):
    out.append(f'<node id={quoteattr(a)}><data key="node_kind">{escape(k)}</data><data key="node_label">{escape(l)}</data></node>')
for e in edges:
    out.append(f'<edge source={quoteattr(e["s"])} target={quoteattr(e["t"])}>' + ''.join(f'<data key="e_{k}">{escape(e[k])}</data>' for k in FIELDS) + '</edge>')
out += ['</graph>', '</graphml>']
(ROOT / 'graphs/changenow_network.graphml').write_text('\n'.join(out) + '\n')
print('graph', len(nodes), len(edges))
