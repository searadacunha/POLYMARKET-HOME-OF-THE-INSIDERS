import json,sys,time,glob
sys.path.insert(0,'tools')
import net,sol
net.RPC[56]=('https://bsc-mainnet.gateway.tatum.io','https://56.rpc.thirdweb.com')
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t)) if t else None
R={}
for f in glob.glob('cases/*.json'):
    for r in json.load(open(f)).get('chain_relations',[]): R[r['id']]=r
def show(i):
    r=R[i]; print(' ',r['case'],r['category'],r['utc'],r['source'],'->',r['target'],'chain',r['chain'],r['token'],r['amount'],'tx',r['tx'],'|',(r['basis'] or '')[:90])
print('--- Gxjc');show('Rf8fe34daeceb2c');show('Ra87d2b7f582188')
G='GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW'
s=sol.rpc('getSignaturesForAddress',[G,dict(limit=1000)])
a=sol.rpc('getAccountInfo',[G,dict(encoding='base64')])['value']
print('Gxjc sigs',len(s),U(s[-1]['blockTime']),U(s[0]['blockTime']),'per min',round(len(s)/max((s[0]['blockTime']-s[-1]['blockTime'])/60,.01),2),'owner',a and a['owner'],'lamports',a and a['lamports'],'exec',a and a['executable'])
print('--- 0xee7a');show('Rbe9e6b059d3dd2');show('R14e98f8ca81780')
E='0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055'
for ch in (137,42161,1,8453,56):
    try: print(' ',ch,'code',net.rpc('eth_getCode',[E,'latest'],ch)[:60],'nonce',net.nonce(E,ch))
    except Exception as e: print(' ',ch,'ERR',str(e)[:90])
print('--- 0xc8a6');show('R8f007c61a50bd7');show('Rf045de8decc17c');show('Ra9c27c406ad547');show('R7805ea41621b7b')
C='0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64'
for ch in (137,1):
    print(' ',ch,'code',net.rpc('eth_getCode',[C,'latest'],ch)[:60],'nonce',net.nonce(C,ch))
print('calls',net.Stats.calls)
