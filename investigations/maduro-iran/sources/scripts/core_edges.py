import sys,json,os,datetime as dt; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bfs2 import relay_edges
def T(t): return dt.datetime.fromtimestamp(int(t),dt.UTC).strftime('%Y-%m-%d %H:%M:%S')
ACC={'0x168b100d7a6620a2f49a455344c2c006eaf1714b':'Chiwawas','0x834079f62fa9b4b0bdfad5b8b7a841e8267da024':'chileno777','0x5621116629c5d640c8186f577362478cc6605245':'TacticalInsiderNews','0xbf32f7a77ccea8bba647fea63d438ce1778b1762':'154x838hjd6','0x56efadc9defe5b7a21af751e0d026f2cf54136db':'Neodbs','0x38745db27f7360a287f6ca3c9b6a6a9c76149801':'Planktonbets','0xe9b80c387ba77a585423b13c850c2e126c3befd8':'Mrs.Joker','0x60280beffdfeaf962de4e6397ab49ed05a1b99e1':'X34',
     '0x6baf05d193692bb208d616709e27442c910a94c5':'SBet365','0x31a56e9e690c621ed21de08cb559e9524cdb8ed9':'0x31a56e9e','0xa72db1749e9ac2379d49a3c12708325ed17febd4':'0xa72db1749e','0x0e9310b9a1bf61ff13d5a31e8ca6188abc8ddb0c':'LINKCS','0x7e9beb7d85ef7eafcdee00f20387217c2b0803ed':'Dhaman','0x73e237f9363d5397f47f3d5c6719bec5602613c3':'night7ucker'}
rows=[]
for a,nm in ACC.items():
    rr,n=relay_edges(a,maxpages=10)
    for e in rr:
        if a not in (e['src'],e['dst']): continue
        rows.append(dict(src=e['src'],dst=e['dst'],chain=e['chain'],asset=e['asset'],amount=round(e['amt'],2),utc=T(e['ts']),tx=e['tx'],relation=('DEPOSIT' if e['dst']==a else 'WITHDRAWAL')+f' ({nm}) via Relay',status='PROVEN (Relay record + on-chain tx)',account=nm))
json.dump(rows,open('core_relay_edges.json','w'),indent=0)
print(len(rows))
for r in rows[:5]: print(r)
