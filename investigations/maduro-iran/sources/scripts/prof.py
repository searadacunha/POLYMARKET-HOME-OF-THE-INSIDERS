import sys, re, html, subprocess, json
sys.path.insert(0,'.')
from common import *
SCAN={1:'etherscan.io',137:'polygonscan.com',8453:'basescan.org',42161:'arbiscan.io',10:'optimistic.etherscan.io'}
def label(chain,a):
    try:
        out=subprocess.run(['curl','-s','-m','25','-A','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',f'https://{SCAN[chain]}/address/{a}'],capture_output=True,text=True,errors='ignore').stdout
        t=re.search(r'<title>\s*(.*?)\s*</title>',out,re.S); d=re.search(r'<meta name="Description" content="([^"]+)"',out,re.I)
        tt=html.unescape(t.group(1)).strip() if t else ''
        lab=tt.split('|')[0].strip() if '|' in tt and not tt.startswith('Address') and not tt.startswith('Contract Address') else ''
        return lab, (html.unescape(d.group(1))[:160] if d else '')
    except Exception as e: return '',str(e)
def prof(chain,a):
    a=a.lower()
    n=es(chain,module='proxy',action='eth_getTransactionCount',address=a,tag='latest')
    n=int(n['result'],16) if isinstance(n,dict) and n.get('result') else None
    code=es(chain,module='proxy',action='eth_getCode',address=a,tag='latest'); code=code.get('result') if isinstance(code,dict) else code
    lab,desc=label(chain,a)
    return dict(addr=a,chain=chain,nonce=n,code=len(code or '')//2-1,label=lab,desc=desc)
if __name__=='__main__':
    chain=int(sys.argv[1])
    for a in sys.argv[2:]:
        print(json.dumps(prof(chain,a)))
