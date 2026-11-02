import json,csv,datetime as dt
A='0xf691384d1023ee41d4e3342eab4f861ecffdda6f'
ROLE={'0xd42f958e1c3e2a10e5d66343c4c9a57726e5b4b6':'MoonPay 6 (payeur stablecoin G0, étiquette Etherscan)','0x22f6cc8738308a8c92a6a71ea67832463d1fec0d':'MoonPay 8 (payeur stablecoin G0, étiquette Etherscan)',
'0x7afc12c8dd2e6591581d95586eb2c2a4905a12a9':'MoonPay 7 (étiquette Etherscan)','0xd108fd0e8c8e71552a167e7a44ff1d345d233ba6':'MoonPay 3 (payeur ETH G0, étiquette Etherscan)','0xb287eac48ab21c5fb1d3723830d60b4c797555b0':'MoonPay 9 (payeur ETH G0, étiquette Etherscan)',
'0x3b6dcfde35e53fb7dca8571f23286631b5123c5b':'trésorerie de la famille','0xeb1d71ae82a1bb7b38218aea41b3cb5343ed53a4':'contrat de dépôt Bitstamp (Forwarder) utilisé par la famille','0x2313c8104832760160bc3da4be7bb4678091af93':'dépôt OKX (étiquette « OKX Deposit ») utilisé par la trésorerie',
'0xfa7dddcf16870a2d9348e98fb201a08b188f78cb':'ancien collecteur G0','0x55fe002aeff02f77364de339a1292923a15844b8':'Circle (étiquette Etherscan)','0x676aecc97bf721c3cb3329a22d49c0ea0ed375f7':'0x676aecc9 (non étiqueté, contrepartie de MoonPay 7)',
'0x0a4850be862df0b6c2ab176fc2fd98941abfe26e':'dépôt Binance alimenté par MoonPay 7','0x9473286c9ea92e47dd75f90ad2106f9e766913b9':'dépôt Binance (étiquette Etherscan)','0x2ab9ac2be0ecb0819bd09b6cbca25cbd25d20a1f':'distributeur de gas G0'}
INTERP={'0xd42f958e1c3e2a10e5d66343c4c9a57726e5b4b6':'mise en service / récupération de solde','0x22f6cc8738308a8c92a6a71ea67832463d1fec0d':'mise en service / récupération de solde','0x3b6dcfde35e53fb7dca8571f23286631b5123c5b':'financement de la trésorerie de la famille','0x2313c8104832760160bc3da4be7bb4678091af93':'test puis dépôt sur le compte OKX de la future trésorerie','0xeb1d71ae82a1bb7b38218aea41b3cb5343ed53a4':'relais vers le compte Bitstamp partagé','0xfa7dddcf16870a2d9348e98fb201a08b188f78cb':'récupération de solde / financement du collecteur'}
rows=[]
for act in ('txlist','tokentx','txlistinternal'):
    for x in json.load(open(f'deep_{A[:10]}_1_{act}.json')):
        try: v=int(x['value'])/10**int(x.get('tokenDecimal') or 18)
        except: continue
        if v==0: continue
        sym=x.get('tokenSymbol','ETH')
        ca=x.get('contractAddress','').lower()
        genuine = act!='tokentx' or ca in ('0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0xdac17f958d2ee523a2206206994597c13d831ec7')
        if not genuine: continue
        f,t=x['from'].lower(),x['to'].lower(); cp=t if f==A else f
        rows.append((int(x['timeStamp']),x['hash'],'OUT' if f==A else 'IN',cp,round(v,6),sym,ROLE.get(cp,cp[:10]),INTERP.get(cp,'')))
rows.sort()
P='/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/phase7/'
with open(P+'timeline_0xf691384d.csv','w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['timestamp','hash','direction','contrepartie','montant','actif','role','source_de_preuve','interpretation'])
    for ts,h,d,cp,v,s,r,i in rows:
        w.writerow([dt.datetime.fromtimestamp(ts,dt.UTC).strftime('%Y-%m-%d %H:%M:%S'),h,d,cp,v,s,r,'on-chain (Etherscan API, txlist/tokentx/txlistinternal) ; rôle via étiquette Etherscan si indiqué',i])
print(len(rows),'rows'); print(rows[0][:6]); print(rows[-1][:6])
