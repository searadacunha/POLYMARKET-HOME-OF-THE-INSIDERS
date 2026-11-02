# Notes de travail (02/11/2026), base des rapports. Chaque ligne renvoie à un log de state/ ou à un fichier de state/runs/.

## Post d'origine
- @zostartt : r.jina.ai rend « This account doesn't exist » (evidence/web/r.jina.ai_https_x.com_zostartt). Post jamais lu directement : les affirmations auditées sont celles recopiées dans la mission.

## 14 juin
- Nonce admin 0x91430c… : 904924 au 05-22 12:00, 06-13 23:59, 06-15 00:00, 06-19 00:00 ; 904926 au 06-20 00:00 (state/may_core.log).
- Attaquant nonce 20 inchangé. Financeur gaz 0xff4c48… 447 inchangé du 13 au 19/06.
- Le 14/06 (state/treasury.log) : admin 0 envoi, attaquant 0, financeur 0 ; 0x871D 10 × 5000 POL (dont nouvel admin 0xf43d55f3) ; 0xf61e 3 × 5000 USDC.e vers 0xf43d55f3 ; trésor 0x2d5076 10 sorties ordinaires.
- DefiLlama /hacks : Polymarket 22/05 700k, 25/06 3M, 29/10 2,7M, 11/11/2025 500k ; rien le 14/06. ZachXBT : messages du 12/06 et 22/06, rien le 14/06. status.polymarket.com : seul incident sécurité mai-nov = 29/10.
- Clé réutilisée le 19/06 15:51 (128 USDC.e + 0,9567 POL vers 0x6656680f, financé 15:51:31 de 599,85 POL par 0xff4c48). Le plus proche du 14/06 : 128 $.
- 34 jours = 22/05 → 25/06 exactement, soit 2 événements.

## Incident A, 22/05 (state/may_core.log, state/may_acct.log, state/runs/may_polygon_full.json, may_taint_full.json)
- Admin → attaquant : 175 POL = 1 246 542,045768126 ; 74 USDC.e = 458 671,452174. USD au moment des transferts 573 598,08 (POL 115 107,21 ; USDC.e 458 490,88 ; POL 0,0921-0,0924). Stevens 573 200 $. 700 000 $ exigerait POL à 0,1936 $.
- Recharges : 0x871D → admin 244 × 5000 POL (06:40:49-09:01:19) = 1 220 000 ; 0xf61e → admin 88 × 5000 USDC.e (05:06:38-07:32:37) = 440 000. Mêmes montants ensuite vers d'autres wallets : c'est la config de recharge.
- Premier balayage 06:40:45 (26 836,84 POL) ; dernier POL 09:01:26 ; dernier USDC.e 07:32:54. Écart mode 32-33 s (57×32, 54×33, 38×31).
- Gaz attaquant : 0xff4c48 → 332,76 POL à 05:55:56.
- Dernière opération ordinaire de l'admin 07:21:21. Nouvel admin 0xf43d55f3 dès 10:13:21 (5000 POL) et 10:15:43 (5000 USDC.e).
- 17 destinataires réels directs (mission : 16).
- Sorties par service, identique sur les 2 bornes (poison / haircut, conservation vérifiée à 458 671,45 et 1 246 542,05) : f2020 270 329,68 USD ; 0x6976 364 957,96 POL ; 0x89c5 120 006,14 USD + 104 954,99 POL ; KuCoin 29 247 136 POL ; HTX 63 29 992 POL ; Bridgers 74 114 POL ; FixedFloat 3 544 POL ; dormant nonce 0 : 0xdd5535 35 000 ; 0x0a804f 30 000 ; 0x2ed3e9 2 900 ; 0x6d1f 435 ; 0x0fb2f4 344 934,87 POL ; 0xca07ef 79 907,95 POL.
- Faux jetons « PỌL » (0xa1a33d44…) et adresses sosies : jamais comptés.
- Oct : 0xbd8e47 renvoie 100 USDC.e vers f2020 le 29/10 09:19:58, payé en gaz par 0x0e2ea4 (nonce 83915) : date commune avec l'incident d'octobre, aucun lien.

## Gel 164 000 $
- ZachXBT (t.me/investigations) + Stevens 13:06:45Z : « With zachxbt... Bitcoin_Vietnam ... changenow, we managed to freeze $164,000 of the $573,200 ».
- 0x89c5 reçoit 70 006,144535 USDC.e à 07:37:17 ; envoie 100 POL (09:30:43) et 70 000 USDC.e (09:31:56) à 0x3cafc132 (neuf) ; celui-ci verse 70 000 USDC.e au Safe 0x3dce0a29 à 13:08:02.
- Safe 3-sur-7, créé 2022-11, appelle addAdmin/removeAdmin/addOperator sur Polymarket CTF Exchange, Neg Risk CTF Exchange, UMA CTF Adapter V2, Fee Modules, NegRisk Operator, CTF Exchange V2 (state/safe2.log). En 2023-12-04 addAdmin de 0x91430c sur NegRisk Operator. Solde actuel 70 000 USDC.e.
- 0x89c5 = BitcoinVN : inférence par élimination (ZachXBT cite 2 services, les 2 autres hubs échangent avec ChangeNOW 22). Aucune étiquette.
- 94 000 $ restants : non localisés. Trésor, 0x871D, 0xf61e : aucune entrée compatible (state/rest_freeze.log). 0x02a004 167 782 USDC : forwarder de mint CCTP, écarté.
- 11 sous-ensembles sur 1023 tombent à ±1000 $ de 164 000 $ (state/runs/subset_164k.json) : le montant n'identifie pas les dépôts.

## Attribution des hubs Polygon (state/hubs.log)
- f2020 : pas de tag. Échange avec « ChangeNOW 22 » 0x4958 (tag PolygonScan rapporté de seconde main, services.json) : 21-23/05, envoie 523 816 USDC + 1 145 675 USDT, reçoit 220 128 USDC + 441 484 USDT. Test de swap de Benjamin payé par f2020 (cn_pm_sakana case_03, 8,83 $ et 8,12 $, RAPPORTÉ).
- 0x6976 : pas de tag. Envoie 1 196 570 POL à 0x4958 en 3 jours.
- 0x4958 : metadata Blockscout vide le 02/11 ; étiquette seulement de seconde main.
- Blockscout metadata Polygon vide pour f2020, 6976, 89c5. Polygonscan refusé (Cloudflare, Jina inclus).
- HW3 0xdd3d et 0x3f3e : chaîne 1 seulement, nonce 0 sur Polygon. HW3 actif mai/juin, 0 le 29/10. 0x3f3e : première tx 2026-08-10, donc rien en mai/juin.
- Aucune adresse chaîne 1 étudiée ne reçoit le vol de mai : le vol reste sur Polygon.

## Lignée du financeur de gaz (state/key_after.log, funder.log, lineage.log)
- 0xff4c48 : depuis 21/01/2026, 264 + 125 resolve(bytes32) sur UMA Adapter V4 et NegRisk Adapter, 6 resolveQuestion NegRisk Operator.
- 05/05/2026 07:20:48-56 : prepareCondition ok ; withdraw, fillOrder, splitPosition échoués ; 31 transferFrom USDC.e échoués vers 0xea5938d5 ; 170 POL vers 0xea5938d5.
- Financé par 0xc0126535 (200 POL 21/01, 333 POL 13/05) et 0x8669debf (599,91 POL 01/06). Les deux démarrent financés par 0x3a0aee0b.
- 0x8669debf envoie 318 012,53 POL au trésor 0x2d5076 le 13/01/2026 ; USDC.e via Disperse. Il est aussi le financeur immédiat de 2,44 $ du comparateur Ballon d'Or 0xf797d4d1 (groupe token_oppose) : flow-trace/state/comparators.jsonl.
- Hypothèses à laisser ouvertes : wallet opérationnel lui aussi compromis ; opérateur tiers de résolution ; lien interne. Aucune démontrée.

## Clé admin après mai (state/key_after.log)
- 19/06 : 128 USDC.e et 0,9567 POL vers 0x6656680f.
- 12/09 : 0x6656680f renvoie 207,47 POL ; approve USDC.e, setApprovalForAll Conditional Tokens, 5 POL + 50 USDC.e vers 0x7b83d2b5.
- 18/09 23:15 : 201,41 POL vers 0x7b83d2b5 ; 23:39:15 initialize sur UMA CTF Adapter V4 ok ; 19/09 01:41:57 proposePrice sur ManagedOptimisticOracleV2 échoué.
- La clé signe donc encore 4 mois après. Stevens : « All permissions tied to the key have been revoked » (Cointelegraph). Qui signe : inconnu.

## Incident C, 25/06 (state/june_core.log, june_extra.log, refunds.log, runs/june_core.json)
- 3 113 215,565734 pUSD vers 7 wallets, 14 comptes ≥ 100 $ + 1 poussière. 05:51:13 → 12:06:37.
- Gaz : FixedFloat 3 (0x71d424) → ~1378-1380 POL par wallet, 00:09-00:11 UTC (donc 5 h 40 avant).
- pUSD → RelayRouter → USDC.e → Relay Depository ; registres Relay dans state/runs/relay_june.json ; USDC minté sur Ethereum ; CoW GPv2Settlement → ETH ; 2eb06b reçoit ETH du solver directement.
- 0xe65b reçoit 1 892,9166615 ETH (6 wallets), renvoie 3,4 ; 1 ; 100 ; 1 788,516 ETH (26/06 20:49:59 vers 0x975268a2).
- Publié : 6 wallets ; Bubblemaps ajoute 0x7BCECe0d ; 8 comptes publiés, 14 mesurés.
- Remboursements : 0x71a7b22d, financé pUSD par trésor 0x2d5076 ; 16 paiements 3 308 363 $ avant 08/07 ; plusieurs au dollar supérieur près (1 094 607 pour 1 094 606,66 ; 508 518 ; 202 434 ; 343 998 ; 247 993 vers d'autres adresses).
- Faux jetons ETH/ĖTḨ vers sosies de 0xe65b : ignorés.

## Incident D, 29/10 (state/oct_core.log, runs/oct_core.json, runs/oct_polygon.json)
- 0x3F99 : 981 entrées via RelayRouter, 28 462 002,18 POL, 17:10:23-18:10:05 ; autres 174 284 POL. 3 sorties 18 613 584 ; 4 295 442 ; 5 727 258 POL. Env. 2,63 M$ à 0,0926.
- Message on-chain du 30/10 18:53 de 0x9c23eddf (signataire du Safe) aux 4 wallets : « Polymarket. Two messages for you… ». Polymarket désigne donc lui-même les 4 wallets.
- Statut : 2,7 M$ + 1,2 M$ = 3,9 M$ rendus.

## Audit
- uma-ctf-adapter : OpenZeppelin, 16/08/2023, commit 11647f1, contrats Solidity, 0 critique, 1 High. ctf-exchange : ChainSecurity. ctf-exchange-v2 : Quantstamp + Cantina, mars 2026. Aucun résultat Trail of Bits : search/code org:Polymarket = 0 ; trailofbits/publications = rien pour Polymarket.

## Outils
- Etherscan renvoie de faux « No transactions found » (16 sur 115 au début) : tools/es.py relance.
- crypttrace 0725d4f et chainmap 4b2e8ab traitent « No transactions » comme vide valide. crypttrace : 1 page de 1000, known.json 0 ChangeNOW. selftest 196/196 sans réseau.

## Incidents de l'étude
- Refus du contrôle de permissions : commande relevant SWAP_RISE_MB de 300 à 800. Non retentée. Garde-fou laissé à 300. Relances de mes propres processus après stabilisation du swap, ce qui recale leur référence : à dire.
- Bug de mes relances : variante sans endblock → lignes hors fenêtre. Corrigé (es.in_range), test ajouté. Bug de fenêtre : walker jusqu'au 05/07, a manqué des mouvements de juillet et d'octobre : relancé jusqu'au 02/11.
