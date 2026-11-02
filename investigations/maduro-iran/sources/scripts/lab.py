import sys,re,html,subprocess,os
SCAN={1:'etherscan.io',137:'polygonscan.com',8453:'basescan.org',42161:'arbiscan.io',10:'optimistic.etherscan.io',56:'bscscan.com'}
def page(chain,a):
    fp=f'cache/page_{chain}_{a.lower()}.html'
    if os.path.exists(fp) and os.path.getsize(fp)>50000: return open(fp,errors='ignore').read()
    out=subprocess.run(['curl','-s','-m','30','-A','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',f'https://{SCAN[chain]}/address/{a}'],capture_output=True,text=True,errors='ignore').stdout
    open(fp,'w').write(out); return out
def label(chain,a):
    s=page(chain,a); a=a.lower()
    t=re.search(r'<title>\s*(.*?)\s*</title>',s,re.S); tt=html.unescape(t.group(1)).strip() if t else ''
    title_lab=tt.split('|')[0].strip() if '|' in tt and not re.match(r'(Address|Contract Address|Contract)\b',tt) else ''
    found=set()
    for m in re.finditer(r'([^>"\'\n]{2,60})&#10;\((0x[0-9a-fA-F]{40})\)',s):
        if m.group(2).lower()==a: found.add(m.group(1).strip())
    d=re.search(r'<meta name="Description" content="([^"]+)"',s,re.I)
    return title_lab, sorted(found), (html.unescape(d.group(1))[:130] if d else f'len={len(s)}')
if __name__=='__main__':
    ch=int(sys.argv[1])
    for a in sys.argv[2:]:
        print(a, label(ch,a))
