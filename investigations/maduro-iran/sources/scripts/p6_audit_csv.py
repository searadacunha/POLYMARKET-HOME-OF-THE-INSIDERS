import json,csv
P='/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/'
H=json.load(open('p6_hashes.json'))
def h(k): v=H.get(k); return v[0] if isinstance(v,list) and len(v)==2 and isinstance(v[0],str) and v[0].startswith('0x') else (v[0] if v else '')
def t(k): v=H.get(k); return v[1] if v else ''
COLS=['id','observation','wallet','contrepartie','timestamp','hash','source','type_de_preuve','niveau','compatible_moonpay','contradictoire','commentaire']
rows=[]
def add(obs,w,cp,ts,hs,src,typ,niv,comp,contra,com): rows.append([len(rows)+1,obs,w,cp,ts,hs,src,typ,niv,comp,contra,com])
ET='étiquette Etherscan (attribution externe)'
# A. les 21 lignes de liens_famille_moonpay.csv
L=list(csv.DictReader(open(P+'phase5/liens_famille_moonpay.csv')))
for l in L:
    de,ve,act=l['de'],l['vers'],l['actif']
    if 'dépôt Bitstamp' in ve:
        add(f"Lien phase 5 : {de} → {ve} ({l['montant']} {act})",'MoonPay 7 (0x7afc12c8)','contrat de dépôt Bitstamp 0xeb1d71ae',l['date_utc'],l['hash'],'on-chain + '+ET,'INDIRECT (même adresse de dépôt Bitstamp)','INFERÉ','oui','non',"Même adresse de dépôt que les collecteurs et la trésorerie ; individualisation par compte déduite (Forwarder créé par Bitstamp 1), non publique")
        continue
    if de.startswith('MoonPay 8'):
        disc='DIRECT, discriminant (stock ensemencé 2 jours après la mise en service, parts égales aux deux jumeaux, test 100 puis solde)'
    elif act in ('RLUSD','PYUSD'):
        disc='DIRECT, discriminant en contexte (échanges de stock répétés ; PYUSD envoyé par un payeur retiré en 2026)'
    else:
        disc='DIRECT, faiblement discriminant seul (un règlement entre deux sociétés produirait le même transfert)'
    add(f"Lien phase 5 : {de} → {ve} ({l['montant']} {act})",de if 'MoonPay' not in de else ve,de if 'MoonPay' in de else ve,l['date_utc'],l['hash'],'on-chain + '+ET,disc,'MESURÉ (transfert) ; nom MoonPay = attribution externe','oui','non','')
# B. wallet d'administration 0xf691384d
A='0xf691384d (admin, non étiqueté)'
add('Admin met en service MoonPay 6 (100 000 USDC)',A,'MoonPay 6',t('0xe7e132997278bfaf'),h('0xe7e132997278bfaf'),'on-chain + '+ET,'DIRECT','MESURÉ','oui','non','Même admin a ensemencé MoonPay 8, MoonPay 3 et 9 en 09/2021')
add('Admin met en service MoonPay 8 (100 000 USDC)',A,'MoonPay 8',t('0x66588523c0ff1422'),h('0x66588523c0ff1422'),'on-chain + '+ET,'DIRECT','MESURÉ','oui','non','')
add('MoonPay 7 → admin 300 ETH puis admin → MoonPay 9 et MoonPay 3 (150 ETH chacun)',A,'MoonPay 7 / 9 / 3',t('0x0abffec2b3fc4a31'),h('0x0abffec2b3fc4a31')+' ; '+h('0x2534e315a46d304e')+' ; '+h('0xbc3c816de6e88c13'),'on-chain + '+ET,'DIRECT','MESURÉ','oui','non','Parts égales aux deux payeurs ETH jumeaux, même logique que la famille')
add('Admin finance le 1er distributeur de gas 0x2ab9ac2b (7 ETH)',A,'0x2ab9ac2b',t('0xc69c35673c3a6a90'),h('0xc69c35673c3a6a90'),'on-chain','DIRECT','MESURÉ','oui','non','0x2ab9ac2b verse 0,01 ETH aux adresses de dépôt du collecteur 0xfa7dddcf')
add('Soldes de MoonPay 8, 0xfa7dddcf et MoonPay 6 rapatriés vers l\'admin',A,'MoonPay 8 / 0xfa7dddcf / MoonPay 6',t('0xeb522f2ffec75d2a'),h('0xeb522f2ffec75d2a')+' ; '+h('0x58a65ba876efc792')+' ; '+h('0x453feee5fefa7ce3'),'on-chain + '+ET,'DIRECT','MESURÉ','oui','non','Relie l\'ancien collecteur 0xfa7dddcf au même opérateur que MoonPay 6/8')
add('MoonPay 7 → admin → dépôt Bitstamp 0xeb1d71ae (250 000 USDC, 3 min)',A,'MoonPay 7 ; 0xeb1d71ae',t('0x7063d2f8f2dad89b'),h('0x7063d2f8f2dad89b')+' ; '+h('0x6c9d520bcb385343'),'on-chain + '+ET,'DIRECT puis INDIRECT','MESURÉ','oui','non','Idem le 19/12/2023 avec 500 000 USDC')
add('MoonPay 7 → admin → dépôt Bitstamp (500 000 USDC)',A,'MoonPay 7 ; 0xeb1d71ae',t('0xb7ab8967679d051d'),h('0xb7ab8967679d051d')+' ; '+h('0xed0907a15f60f0a6'),'on-chain + '+ET,'DIRECT puis INDIRECT','MESURÉ','oui','non','')
add('Admin teste le compte OKX 0x2313c810 (3 × 50 USDT) 4 mois avant que la trésorerie ne l\'utilise',A,'dépôt OKX 0x2313c810',t('0x2bbffdc184f438cf'),h('0x2bbffdc184f438cf')+' ; '+h('0x564302810cfe50c4')+' ; '+h('0x748de23ea9e8efe3'),'on-chain','INDIRECT (même adresse de dépôt OKX, étiquetée « OKX Deposit »)','MESURÉ','oui','non','Puis 23 300,67 USDT le 21/03/2024 ; la trésorerie y envoie 32,5 M$ dès le 21/05/2024')
add('Admin reçoit les soldes de MoonPay 9 et MoonPay 3 (15,34 et 15,00 ETH)',A,'MoonPay 9 / MoonPay 3',t('0x54680a00ef982fad'),h('0x54680a00ef982fad')+' ; '+h('0x8a3d3c172f598487'),'on-chain + '+ET,'DIRECT','MESURÉ','oui','non','Retrait des anciens payeurs ETH, 10 jours après la mise en service')
add('Admin → trésorerie 0x3b6dcfde : 0,01 ETH de test puis 30 ETH',A,'trésorerie 0x3b6dcfde',t('0x2455a0062af29bd7'),h('0x2455a0062af29bd7')+' ; '+h('0xced5a4f2a5f40e0f'),'on-chain','DIRECT, discriminant (le même admin a créé MoonPay 6/8 et finance la trésorerie)','MESURÉ','oui','non','Lien opérateur entre la famille et le groupe de wallets étiquetés MoonPay')
# C. bascules
add('Bascule payeurs stablecoin : MoonPay 6/8 (≈80-120 paiements/jour chacun) → 0 le 23/05/2024 ; b93e/26c5 démarrent le 21/05/2024','MoonPay 6/8','0xb93e3d70 / 0x26c50e67','2024-05-21 → 2024-05-23','','historiques complets','CORRÉLATION temporelle forte','MESURÉ','oui','non','Volume combiné continu')
add('Bascule payeurs ETH : MoonPay 3/9 (≈2 000/jour) → 0 après le 21/05/2024 ; 0x0e9e3919 et 0xa7ceed38 démarrent le 21/05/2024 à 14:56 (12 s d\'écart)','MoonPay 3/9','0x0e9e3919 / 0xa7ceed38','2024-05-21','','txlist par fenêtre de blocs','CORRÉLATION temporelle forte','MESURÉ','oui','non','')
add('Bascule collecteurs dans le même compte Bitstamp : 0xfa7dddcf (→ 30/06/2024) → 0x7f227df2 (28/06/2024 →) → 0xabe7931e (16/04/2025 →)','0xfa7dddcf','0x7f227df2 / 0xabe7931e','2024-06-28','','expéditeurs de 0xeb1d71ae (historique complet)','INDIRECT + CORRÉLATION','MESURÉ','oui','non','0xfa7dddcf alimente aussi le dépôt Binance de MoonPay 7')
add('Bascule distributeurs de gas : 0x2ab9ac2b → 0xa26ebecc (5,11 ETH) → 0x9d34c01d (26/06/2024) ; mêmes variantes 0,01/0,0099/0,0021/0,0022','0x2ab9ac2b','0xa26ebecc / 0x9d34c01d',H['gas_handover'][0][1],H['gas_handover'][0][0],'on-chain','DIRECT (0x2ab9ac2b→0xa26ebecc) + CORRÉLATION (0x9d34c01d)','MESURÉ','oui','non','Aucun transfert direct entre 0xa26ebecc et 0x9d34c01d observé')
add('Continuité des bénéficiaires : MoonPay 6 et 8 ont payé 58 % et 55 % de 160 bénéficiaires précoces de b93e/26c5','MoonPay 6/8','b93e/26c5','avant 21/05/2024','','échantillon (p5_predecessor.json)','CORRÉLATION','MESURÉ (échantillon)','oui','non','Coinbase 10 : 16 % ; Zero Hash 1 : 11 % ; mercuryo : 4 %')
add('Continuité des bénéficiaires ETH : 0xa7ceed38 et 0x0e9e3919 paient 64 % et 60 % de 120 bénéficiaires de MoonPay 3/9','MoonPay 3/9','0xa7ceed38 / 0x0e9e3919','après 21/05/2024','','échantillon (p6_eth_successor.json)','CORRÉLATION','MESURÉ (échantillon)','oui','non','Zero Hash 1 : 8 % ; mercuryo : 7 % ; Transak : 3 %')
add('Même moteur de paiement : limite de gas 84 000 (MoonPay 6 : 98,5 % ; b93e : 100 %), réappro de 50 000, heures corrélées à 0,99, 26 % le week-end','MoonPay 6/8','b93e/26c5','fenêtres de 12 mois','','p6_operator.json','CORRÉLATION','MESURÉ','oui','non','Paramètres communs, pas propres à une société')
add('Différence : MoonPay 6/8 financés par des hot wallets Binance ; génération 1 par sa propre trésorerie (Coinbase Prime, Kraken, Circle, OKX)','MoonPay 6/8','b93e/26c5','2023-2025','','p6_operator.json','DIFFÉRENCE','MESURÉ','neutre','affaiblit légèrement','Compatible avec une refonte interne du financement')
# D. jetons
add('RLUSD : canal Ripple dédié (multisig 0x2591c2af créé par « Ripple: Deployer » le 10/10/2024) qui ne livre que 0xb93e3d70',"0x2591c2af (Ripple)","0xb93e3d70",H['RLUSD_first_in_ripple'][1],H['RLUSD_first_in_ripple'][0],'on-chain + étiquette « Ripple: Deployer »','DIRECT (Ripple → famille)','MESURÉ','oui','non','Partenaires annoncés le 15/10/2024 : Uphold, Bitstamp, Bitso, MoonPay, Independent Reserve, CoinMENA, Bullish, Archax')
add('Élimination : Uphold, Bitso, B2C2 et Zero Hash ont chacun un canal Ripple distinct de celui de la famille','Ripple multisigs','Uphold / Bitso 1 / B2C2 Group 1 / Zero Hash 1','09-12/2024','','p6_ripple_multisigs.json','INDIRECT (élimination)','MESURÉ + '+ET,'oui','non','Aucun canal séparé ne mène à un wallet MoonPay étiqueté')
add('USAT : 1er paiement le jour du lancement (27/01/2026 17:12), MoonPay cité parmi les plateformes de lancement',"0xb7152d59",H['USAT_first_payout'][3],H['USAT_first_payout'][1],H['USAT_first_payout'][0],'on-chain + presse (CoinDesk, Tether)','CORRÉLATION temporelle','MESURÉ + source publique','oui','non','Aussi listés : Kraken, OKX, Bybit, Crypto.com ; source USAT de la famille = 0x17edcb15, qui traite aussi avec Kraken ; aucun wallet MoonPay étiqueté ne manipule USAT')
add('XAUt : 1er paiement le 24/04/2025, 5 jours avant l\'annonce MoonPay (29/04/2025) ; MoonPay 7 envoie 30,19 XAUt à la trésorerie la veille',"0xb93e3d70",H['XAUt_first_payout'][3],H['XAUt_first_payout'][1],H['XAUt_first_payout'][0],'on-chain + moonpay.com','CORRÉLATION temporelle + DIRECT','MESURÉ + source publique','oui','non','')
add('PYUSD : 1er paiement le 01/10/2024 22:10, 1 à 2 jours avant l\'annonce MoonPay (02-03/10/2024)',"0x26c50e67",H['PYUSD_first_payout'][3],H['PYUSD_first_payout'][1],H['PYUSD_first_payout'][0],'on-chain + The Block, moonpay.com','CORRÉLATION temporelle','MESURÉ + source publique','oui','non','Même destinataire 0xb7aec302 que l\'un des premiers paiements RLUSD : compatible avec un wallet de test')
add('USD1 et GODS : date MoonPay introuvable','famille','','2025-05-20 ; 2024-06-04','','web','INCONNU','INCONNU','indéterminé','non','Données insuffisantes')
add('MoonPay 5 (étiqueté) paie en 2026 SHIB, POL, LINK, PYUSD, APE, IMX : les altcoins que la génération 1 payait et que la génération 2 ne paie plus','MoonPay 5','famille','2026','','tokentx MoonPay 5 (1 000 dernières)','CORRÉLATION fonctionnelle','MESURÉ (échantillon)','oui','non','Complémentarité, pas preuve')
# E. Polymarket et clients
add('Polymarket : 0/250 paiements Ethereum vers une adresse de dépôt Polymarket ; 1/150 sur Polygon et 1/150 sur Ethereum vers un compte Polymarket','payeurs G2','échantillons','2025-2026','','p5_pm_baserate.json ; p6_polygon_pm.json','TEST NÉGATIF','MESURÉ (échantillon)','neutre','non','Aucune signature de l\'intégration MoonPay × Polymarket ; les 16 paiements ressemblent à des envois ordinaires')
add('Bénéficiaires des 16 paiements : aucun ne reçoit d\'un wallet étiqueté MoonPay ni de l\'admin ; seuls liens de service = la famille','5 adresses bénéficiaires','MoonPay 2,3,5,6,7,8,9 + admin','2025-2026','','p6_client_test.json','TEST NÉGATIF','MESURÉ','neutre','non','Client non identifiable publiquement')
# F. contradictoires / alternatives
add('Zero Hash 1 → trésorerie : 135,52 USDT + 100 USDC','Zero Hash 1','trésorerie','2025-07-24','0x9d277b0469eab3c61be27d093b4ba7f9d64f589a0fa9c5ca0813a7ede1417059 ; 0xc2a9ea9220011887ed0853743e87cc41a4e387389f1db4d86893a5e501e70516','on-chain + '+ET,'DIRECT (autre rampe)','MESURÉ','neutre','non (montant marginal)','Envoi d\'un utilisateur ou erreur d\'adresse ; aucun lien opérateur')
add('Coinbase 10 → trésorerie : 1,00 USDC','Coinbase 10','trésorerie','2025-11-19','0xeff88ab8e2827fec66b700302c181a4f9e864cde49bec7c7fa598d75cd4863e2','on-chain + '+ET,'DIRECT (CEX)','MESURÉ','neutre','non','Test ou erreur d\'adresse')
add('Toutes les appellations « MoonPay N » viennent de la famille Etherscan (Etherscan, BscScan, Blockscan) ; un agrégateur tiers reprend « MoonPay » pour MoonPay 7','MoonPay 2-9','','','','web','SOURCE UNIQUE','ATTRIBUTION EXTERNE','oui','affaiblit','Méthode d\'étiquetage d\'Etherscan non publique')
add('Aucune attribution publique des adresses de la famille (Etherscan, Polygonscan, web, jeux publics)','famille','','','','web + explorateurs','ABSENCE','INCONNU','neutre','non','Une absence de résultat n\'est pas une preuve')
with open(P+'phase6/audit_attribution_moonpay.csv','w',newline='') as fh:
    w=csv.writer(fh); w.writerow(COLS); w.writerows(rows)
print(len(rows),'lignes')
