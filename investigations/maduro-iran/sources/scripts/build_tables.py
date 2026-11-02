import json,csv,os,glob,datetime as dt
from collections import defaultdict
OUT=os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase2'); os.makedirs(OUT,exist_ok=True)
def T(t): return dt.datetime.fromtimestamp(int(t),dt.UTC).strftime('%Y-%m-%d %H:%M:%S')
LBL={'0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43':'Coinbase 10','0x05ff6964d21e5dae3b1010d5ae0465b3c450f381':'Kraken Hot Wallet 4','0xc9aaa6ca0e05b87d53a3e51edbc44b406eeaf299':'Coinbase 30',
 '0x1bac08001d761c303901d5e32273a24c07d3f3da':'n.exchange Hot Wallet','0xd0e83490a55e671b3cf39cd027f0f9035ec5a1ef':'Binance Deposit (n.exchange)','0xb685760ebd368a891f27ae547391f4e2a289895b':'Bridgers',
 '0x9642b23ed1e01df1092b92641051881a322f5d4e':'MEXC 16','0x3cc936b795a188f0e246cbb2d74c5bd190aecf18':'MEXC 3','0x89e51fa8ca5d66cd220baed62ed01e8951aa7c40':'Kraken 7','0xfb19ffd1ff9316b7f5bba076ef4b78e4bbedf4e1':'Aeroswap 2',
 '0x6081258689a75d253d87ce902a8de3887239fe80':'Robinhood 3','0xcb39c5b0db9c5b6bd1d9273dccc2f98f532a8bc6':'Coinbase 6','0x20fe51a9229eef2cf8ad9e89d91cab9312cf3b7a':'Coinbase 14 (Base)',
 '0xa3222357a0eccf60c73606170be6c99adecb59b3':'batch-withdrawal contract (INFERÉ HitBTC)','0x4a9a16755a6bf64291cd2c9eb027b39c129ff58d':'UNKNOWN SERVICE payout (41k payees)','0xb7152d5900da932b7fc3cac97aebfc815f88d5ca':'UNKNOWN SERVICE payout (same refiller)',
 '0xed9c6843bf3a69eca32578c253b742e5fbab7738':'UNKNOWN SERVICE hot wallet (71k tx)','0xba4e328c6f9a5356db1cf17a04062f4d6d6e5153':'UNKNOWN SERVICE (successor of 0xed9c6843)',
 'TPwezUWpEGmFBENNWJHwXHRG1D2NCEEt5s':'Bridgers TRON','TXtEs6t2oUWQsNos7m68gbHdE9Q5n6x2oN':'Relay TRON receiver','TYVWGh8XkmUz6Vug7NAPRCmNYdHcf7KxeW':'Relay TRON receiver (INFERÉ)','TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf':'UNKNOWN SERVICE TRON (733 senders/6h)',
 '0xf70da97812cb96acdf810712aa562db8dfa3dbef':'Relay solver','0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222':'RelayRouter','0x4cd00e387622c35bddb9b4c962c136462338bc31':'Relay depository','0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae':'LI.FI'}
NETW={'0x44b6f8de91e20953eb2c632062860338154ebe4e','0xe9a7230f874930827b87970a4fbb33a262f02442','0x2e473c0af74b294031c1ef44b5a3870b47d4d26f','0x2225a4fd2cdf91307ab9da9f6fc30312eff627ca','0x4e062726688d02cffff7c39918bfb3d4470614eb',
 'TSahUmP5mWriKP7ftbkLvz6AJ8zvc5qTPT','TJs1u6k8RWaqgLRZTxF9eKXojWv8HsbJwx','TTt3h6D2sB3KMNZAH8w8z9xEqsfCTRo8nf','TA4chMztaY6TW8dv7qnuqmJKvb4edZqwj5','TLREUZVRJ9jifQfKvnDMRyXxEhasiGYhP4','TEfE77WkNAzm6DrKhkqd6S9kw53HnqHPS6','TFMhN2unzoVHvyxQZ7FAt3UuKXCbegpekp','TChkscPd95MexmFGZLWpSLkrNnyfg8V2rE'}
DEP={'0x572441fa356183130b0386de377222d17a7d66a5':'dépôt PM Chiwawas','0x5b85645c81b2a768c9919ea54c736ba025b21ece':'dépôt PM TacticalInsiderNews','0xd4f7d8ac96ed3f467db31fd195faa10676775dab':'dépôt PM 154x838hjd6','0xc2be6a8c0ceae73a8ecdccd22aa0334f0a5c34ff':'dépôt PM chileno777',
 '0xa460a58881631e92d26aeab572b95b003f132f3c':'dépôt PM Mrs.Joker','0xefaa882c1eb8253a65a3a194f08063693a13f565':'dépôt PM X34','0x75db067e953f776d24ba54b64217a168a13ab397':'dépôt PM Planktonbets (profil non confirmé)','0x72bf08860e18a46ee020e3a475f8491461903f48':'dépôt PM SBet365','0x8db6758f477290b2530bfb6a5d5f11d3b39b822d':'dépôt PM LINKCS','0x1a714134658f4a735700c4e86842664f8ca9e0ba':'dépôt PM 0xa72db1749e'}
def lab(a): return LBL.get(a) or DEP.get(a) or ('réseau' if a in NETW else '')
rows=[]
# relay edges
for e in json.load(open('core_relay_edges.json')):
    rows.append(dict(source=e['src'],src_label=lab(e['src']) or e['account'] if e['src'].startswith('0x') and e['relation'].startswith('WITHDRAWAL') else lab(e['src']),destination=e['dst'],dst_label=lab(e['dst']) or (e['account'] if e['relation'].startswith('DEPOSIT') else ''),
        chain=e['chain'],asset=e['asset'],amount=e['amount'],utc=e['utc'],tx=e['tx'],relation=e['relation'],status='PROVEN'))
# erc20 / native from BFS edges + deep + extra, restricted to edges touching network EOAs, deposit addrs, or labelled services
seen=set()
def add(src,dst,chain,asset,amt,ts,tx,rel,status):
    k=(tx,src,dst,round(amt,4))
    if k in seen: return
    seen.add(k); rows.append(dict(source=src,src_label=lab(src),destination=dst,dst_label=lab(dst),chain=chain,asset=asset,amount=round(amt,4),utc=T(ts),tx=tx,relation=rel,status=status))
E=[json.loads(l) for l in open('bfs2/edges.jsonl')]
FOCUS=NETW|set(DEP)
for e in E:
    if e['kind'] in ('erc20','native','trc20') and (e['src'] in FOCUS or e['dst'] in FOCUS):
        rel='gas' if e['kind']=='native' and e['amt']<0.05 and e['asset'] in ('NATIVE','ETH') else ('transfer' if e['kind']!='native' else 'native transfer')
        add(e['src'],e['dst'],{'1':'ethereum','137':'polygon','tron':'tron'}.get(e['chain'],e['chain']),e['asset'],e['amt'],e['ts'],e['tx'],rel,'PROVEN')
A='0x44b6f8de91e20953eb2c632062860338154ebe4e'
OFF={'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':'USDC','0xdac17f958d2ee523a2206206994597c13d831ec7':'USDT'}
for x in json.load(open('deep_0x44b6f8de_1_tokentx.json')):
    c=x['contractAddress'].lower()
    if c in OFF and int(x['value'])/1e6>=1: add(x['from'].lower(),x['to'].lower(),'ethereum',OFF[c],int(x['value'])/1e6,x['timeStamp'],x['hash'],'transfer','PROVEN')
for x in json.load(open('deep_0x44b6f8de_1_txlist.json')):
    if int(x['value'])>0: add(x['from'].lower(),x['to'].lower(),'ethereum','ETH',int(x['value'])/1e18,x['timeStamp'],x['hash'],'gas' if int(x['value'])/1e18<0.05 else 'native transfer','PROVEN')
for x in json.load(open('extra_edges.json')):
    ts=int(dt.datetime.strptime(x['ts'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=dt.UTC).timestamp())
    rel='sweep to service' if lab(x['dst']) and not x['dst'].startswith('0x44b6') else 'transfer'
    add(x['src'],x['dst'],'ethereum' if x['chain']==1 else 'polygon',x['asset'],x['amt'],ts,x['tx'],rel,'PROVEN')
# Bridgers cross-chain (calldata minReturn == received amount)
BR=[('0x2e473c0af74b294031c1ef44b5a3870b47d4d26f','TSahUmP5mWriKP7ftbkLvz6AJ8zvc5qTPT',34118.2235,33840.607570,1767465000,'0xb6abc243b39b4d6db3829ce5ca33e1107752df23a7e6e5b3002c9a3e5e0b10a5|8581f84980fbc41a7d85d2c85add4de8514c67de09d2a1e1bfb29dda574e4f9d'),
    ('0x2e473c0af74b294031c1ef44b5a3870b47d4d26f','TSahUmP5mWriKP7ftbkLvz6AJ8zvc5qTPT',38696.4503,38424.075149,1772274203,'0xe1c4e2b09768af49310cd4d6a722fffaa7b4371d5b588390e545ef519eb45d56|4d9673c6798aba9c7e5ee7aa8824a7bcd964263cc05ca91b56a170ba0e5b44c7'),
    ('0x4e062726688d02cffff7c39918bfb3d4470614eb','TJs1u6k8RWaqgLRZTxF9eKXojWv8HsbJwx',98679.3359,97987.080535,1772274119,'0xf6f4ae986acd03e0f6a41dc0d4e064d228fc5c04f88241d9d2f2ce985d9a2172|b1c3b47499ed5bcc2355b093e2ad0991e6c6f9c557007e59baf2aa5b44b1028a'),
    ('0xe9a7230f874930827b87970a4fbb33a262f02442','TTt3h6D2sB3KMNZAH8w8z9xEqsfCTRo8nf',38696.45,38424.074850,1772272835,'0x2ba1113c956d752a59070faf6ad1f678693b87fc8d5679575bfc889ec22ba100'),
    ('0xe9a7230f874930827b87970a4fbb33a262f02442','TTt3h6D2sB3KMNZAH8w8z9xEqsfCTRo8nf',159373.4654,158256.351097,1772273627,'0x28dbb955703158c438128bf310ffed87aa0ef9edabcae33e927c62c06cb1efdb'),
    ('0xe9a7230f874930827b87970a4fbb33a262f02442','TTt3h6D2sB3KMNZAH8w8z9xEqsfCTRo8nf',159373.4654,158256.351097,1772274095,'0xac894e838b78c631f0485b895a529fde2275e6e0666a8a1d123826f6de106a9e'),
    ('0xe9a7230f874930827b87970a4fbb33a262f02442','TTt3h6D2sB3KMNZAH8w8z9xEqsfCTRo8nf',40461.725823,40172.894745,1769730923,'0xd7bcb53eadeefb2098527b91010e6e50b5e4376c038c0c2d6a1eb5bad6f1bebc|e2474f1f5a2cbc6903b0d923e77c0a6d89f049e3459e0595e321281f2055550a'),
    ('TTt3h6D2sB3KMNZAH8w8z9xEqsfCTRo8nf','0xe9a7230f874930827b87970a4fbb33a262f02442',39899.20,39619.803654,1768420317,'b7521eee111b54f00884041a8e8664458741a195ad6c2178861977a93806d4b2|0xbc2a2f52e49e3b29a28f5001ebad474b335f19713f6cd810e154bfc786048078')]
for s,d,ai,ao,ts,tx in BR:
    add(s,d,'ethereum->tron' if s.startswith('0x') else 'tron->ethereum','USDT/USDC->USDT',ai,ts,tx,f'bridge Bridgers (reçu {ao:,.6f} = minReturn calldata)','PROVEN')
rows.sort(key=lambda r:r['utc'])
with open(f'{OUT}/TABLE1_graph.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=['source','src_label','destination','dst_label','chain','asset','amount','utc','tx','relation','status']); w.writeheader(); w.writerows(rows)
print('TABLE1 rows',len(rows))
json.dump(rows,open('table1.json','w'))
