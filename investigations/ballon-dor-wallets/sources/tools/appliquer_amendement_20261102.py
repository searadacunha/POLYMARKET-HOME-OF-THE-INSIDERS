"""Version 2 du rapport = version 1 archivée + ces remplacements. Chaque texte d'origine doit être trouvé le nombre de fois annoncé, sinon rien n'est écrit.
Sert aussi de journal exact : tout ce qui change entre les deux versions est ici. Ne touche ni aux preuves, ni à collective/, ni aux cases/*.json.
Usage : python3 tools/appliquer_amendement_20261102.py [--ecrire]"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARC = ROOT / 'archive/20261102_avant_amendement_audit'
EV = ROOT / 'evidence/contre_verification_20261102'
V1_SHA = 'de683ab687b293fca7d2ed9d09cda0aefe4341e0ee956510238022f76021c8c0'
sha = lambda b: hashlib.sha256(b).hexdigest()
v1 = (ARC / 'rapport_final.md').read_bytes()
assert sha(v1) == V1_SHA, 'archive modifiée'
text = v1.decode()
compl = json.load(open(EV / 'complements.json'))
done = []


def sub(old, new, n=1, why=''):
    global text
    assert text.count(old) == n, (text.count(old), old[:90])
    text = text.replace(old, new)
    done.append((n, old[:70].replace('\n', ' ')))


SECTIONS = ['Thin-Disclaimer-Life', 'VidenteRibeira', 'cookedrice', 'WenZhuanBuPei', '0x86544e4dfde', 'brace227', 'walletwallet8424', 'Zoomman17', 'kraben006', 'OuldLm3alem', '0xdd97e6']
SLUG = dict(zip(SECTIONS, ['thin', 'vidente', 'cookedrice', 'wen', '0x86544e4dfde', 'brace227', 'walletwallet8424', 'zoomman17', 'kraben006', 'ouldlm3alem', '0xdd97e6']))


def in_section(label, old, new):
    global text
    start = text.index(f'\n### {label}\n')
    following = [text.index(f'\n### {x}\n') for x in SECTIONS if text.index(f'\n### {x}\n') > start] + [text.index('\n## 3. Réconciliation')]
    end = min(following)
    block = text[start:end]
    assert block.count(old) == 1, (label, block.count(old), old[:80])
    text = text[:start] + block.replace(old, new) + text[end:]
    done.append((1, f'[{label}] {old[:60]}'))


# En-tête et conclusion
sub("Écrit le 02/11/2026 à 08:18 UTC depuis les fichiers de preuve. Espace : `~/Projects/PolySentinel-investigation`.",
    f"**Version 3 du 02/11/2026, corrigée après audit et complétée par les rapports finaux de l'enquête flow-trace.** La version 1, écrite à 08:18 UTC, est conservée sans changement : `archive/20261102_avant_amendement_audit/rapport_final.md`, sha256 `{V1_SHA}`. La version 2 est dans `archive/20261102_v2_avant_flow_trace/`. Chaque correction : `reports/AMENDEMENT_AUDIT_2026-11-02.md`. Chaque vérification : `reports/CONTRE_VERIFICATION.md`. Espace : `~/Projects/PolySentinel-investigation`.")
sub("**Aucune coordination et aucune information privilégiée ne sont démontrées.** Les onze comptes publics sont reliés à une adresse et leurs flux sont reconstruits, mais rien ne prouve qu'ils ont un propriétaire commun. Le signal collectif testé est visible au 13 octobre, sans être spécifique.",
    "**Ni contrôle commun, ni coordination, ni information privilégiée ne sont démontrés. Deux connexions financières directes existent pourtant.** La clé de brace227 envoie 0,00205 ETH, environ 5,53 $, à celle de kraben006 le 4 octobre. Surtout, elle finance les dépôts d'un wallet non nommé, 5 170 USDC les 9 et 10 octobre, à parts presque égales avec son propre wallet, et ce wallet ne parie que sur Kane. Ces faits ne disent pas qui contrôle ces clés, et ils ne disent rien d'une information privilégiée. Les onze comptes publics sont reliés à une adresse et leurs flux sont reconstruits. Le signal collectif testé est visible au 13 octobre, sans être spécifique.")
sub("| Coordination | **Non démontrée** | 0 transfert direct de fonds, 0 adresse partagée discriminante sur 55 paires, 0 paire nommée dans E4 v2, pas de synchronie nette (centile 95,5 à 5 min non corrigé, 84,2 à 60 min). |",
    "| Connexion financière | **Établie : 1 paire sur 55 entre dossiers, et 1 wallet non nommé** | Transfert natif direct brace227 vers kraben006, lu sur deux nœuds. 5 170 USDC de la clé de brace227 vers la clé du wallet non nommé `0xa8e64a3c…f74a5`, lus sur la chaîne. Aucun autre lien entre dossiers trouvé sur le périmètre lu par l'audit (section 4). Sur la même lecture, selon l'enquête flow-trace, 0 transfert direct sur 1 431 paires de clés témoins. Périmètre non exhaustif : comptes d'exchange invisibles, entrées BSC non lues, autres wallets testés sous 2 formes seulement. |\n| Contrôle commun de wallets | **Non déterminé** | Ni démontré, ni exclu, y compris pour brace227 et kraben006, et pour brace227 et `0xa8e64a3c…`, financé par elle. Financer un compte n'est pas le contrôler. La méthode n'a aucun témoin positif de propriété commune. |\n| Coordination des paris | **Non démontrée** | 0 adresse partagée discriminante sur 55 paires, pas de synchronie nette (centile 95,5 à 5 min non corrigé, 84,2 à 60 min). E4 v2 ne trouve aucune paire nommée, mais 19 paires sur 55 n'y sont jamais testées. Indice le plus fort : brace227 et `0xa8e64a3c…`, même source de fonds les 9 et 10 oct., premiers achats à 13 min d'écart, Kane en commun, pour 954,04 $ chez brace227 ces deux jours contre 5 164,99 $ chez ce wallet jusqu'au 11 oct. Il fonde une hypothèse, pas une démonstration. |")
sub("9 sur 11 ont déposé moins d'une heure avant leur premier achat sur cette famille.", "9 sur 11 ont déposé moins d'une heure avant leur premier achat sur cette famille, comme 32 comptes frais sur 39 selon la relecture de l'enquête flow-trace : ce trait n'a rien de distinctif.")
sub("Aucune preuve d'accès à l'information. Gagner un pari, même tôt, ne prouve pas sa source.", "Aucune preuve d'accès à l'information. Gagner un pari, même tôt, ne prouve pas sa source, et une connexion financière entre deux comptes non plus.")

# Périmètres des montants
sub("Sur les 7 comptes soldés, retraits moins dépôts : **129 367,79 $**. Les 4 autres ne sont pas soldés ou gardent un résidu (0x86544e4dfde, brace227, Zoomman17, OuldLm3alem) : aucun gain n'y est affirmé. Ce total ne recoupe pas les chiffres de presse, dont le périmètre diffère.",
    """**Les deux montants à ne pas confondre.** 493 094,76 $ est un flux brut, 129 367,79 $ un net partiel. Arrondis au cent, d'où un écart d'un cent sur la somme des dépôts.

| Périmètre | Comptes | Dépôts $ | Retraits $ | Retraits moins dépôts $ |
|---|---:|---:|---:|---:|
| Soldés : Thin, VidenteRibeira, cookedrice, WenZhuanBuPei, walletwallet8424, kraben006, 0xdd97e6 | 7 | 183 347,12 | 312 714,91 | **129 367,79** |
| Résidu faible : 0x86544e4dfde, brace227, OuldLm3alem | 3 | 111 047,33 | 173 485,85 | 62 438,52 |
| Retraits inférieurs aux dépôts : Zoomman17 | 1 | 9 743,19 | 6 894,00 | -2 849,19 |
| **Les onze** | 11 | 304 137,63 | **493 094,76** | 188 957,12 |

- **493 094,76 $ n'est pas un gain.** Ce sont les 25 retraits des 11 comptes. Ils rendent d'abord les 304 137,63 $ déposés, et comptent un aller-retour de 438,67 $ de kraben006 (retiré puis redéposé 64 s plus tard).
- **129 367,79 $ ne couvre que 7 comptes.** C'est le seul périmètre où le compte est entièrement fermé. Les 4 autres gardent un résidu ou des positions : aucun gain n'y est affirmé. Ce chiffre ne dit rien de plus que retraits moins dépôts sur ces wallets : ni gas, ni frais hors du wallet, ni autre compte d'une même personne, inconnus ici.
- **Contrôle indépendant, sur la chaîne :** 25 destructions de pUSD sur 25 et 46 frappes sur 46 égales aux montants de l'API. Par ailleurs, dépôts plus activité (188 964,13 $ d'achats, ventes, redemptions, rebates, récompenses) moins retraits donnent 7,01 $, la somme des quatre résidus : c'est une identité du calcul, pas une preuve de plus.
- Ces totaux ne recoupent pas les chiffres de presse, dont le périmètre diffère. Montants reçus à destination : inférieurs aux retraits (frais de pont) et en jetons différents, donc non additionnés ici.""")

# Dossiers : transfert direct
LIEN = "- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus."
for lab in SECTIONS:
    if lab == 'brace227':
        in_section(lab, LIEN, "- **Transfert direct vers le dossier kraben006 :** le 2026-10-04 13:54:35 UTC, la clé `0xc852b0938f5ad79b640d105ed11c14499454af26` envoie 0,002048943671205553 ETH, environ 5,53 $, à `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65`, `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`. Détail et hypothèses : section 4. Aucun autre transfert direct trouvé sur le périmètre lu par l'audit, revérifié ici sur Ethereum pour cette clé. Aucune adresse partagée discriminante.\n- **Hors des onze, wallet non nommé :** cette clé envoie 2 210 et 2 960 USDC à `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`, propriétaire du wallet `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5`, qui ne parie que sur Kane. Détail et hypothèses : section 4.")
    elif lab == 'kraben006':
        in_section(lab, LIEN, "- **Transfert direct depuis le dossier brace227 :** le 2026-10-04 13:54:35 UTC, cette clé reçoit 0,002048943671205553 ETH, environ 5,53 $, de `0xc852b0938f5ad79b640d105ed11c14499454af26`, `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`. Détail et hypothèses : section 4. Aucun autre transfert direct trouvé sur le périmètre lu par l'audit, revérifié ici sur Ethereum pour cette clé. Aucune adresse partagée discriminante.\n- Étiquettes ChangeNOW de Blockscout, source unique, sur cette clé : 834,85 USDC reçus le 23 fév. 2026, et 0,00247 ETH partis le 4 oct. vers `0x7e67…`, puis `0x3f3E…`. Section 6.")
    else:
        in_section(lab, LIEN, "- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.")
for lab in ('brace227', 'kraben006'):
    in_section(lab, "- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.", "- Connexion financière directe avec " + ('kraben006' if lab == 'brace227' else 'brace227') + " : **établie**, 1 transfert. Contrôle commun, coordination et information privilégiée : **non démontrés**. Le transfert n'en est pas la preuve.")
sub("- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.", "- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.", 11)
in_section('brace227', "- Profil de petit parieur actif : nombreux tickets, 8 dépôts, 9 issues, et des retraits en cours de route. Aucune priorité ni comportement dans S_A.", "- Profil de petit parieur actif sur ce wallet : nombreux tickets, 8 dépôts, 9 issues, et des retraits en cours de route. Aucune priorité ni comportement dans S_A. Mais la même clé finance à parts presque égales un second wallet, tout sur Kane : ce profil ne décrit qu'une partie de ses fonds (section 4).\n- Retrait principal 2,8 min après celui de kraben006 : aucun signal mesurable. Il suit de 136 s sa vente à 0,999, vitesse ordinaire, 10 vendeurs comparables sur 20 retirent aussi en moins de 5 min (section 4).")
in_section('kraben006', "- Le plus progressif : 14 petits dépôts depuis le 1er octobre,", "- Retrait principal 2,8 min avant celui de brace227 : aucun signal mesurable. Il suit de 48 s sa vente à 0,999, vitesse ordinaire, 10 vendeurs comparables sur 20 retirent aussi en moins de 5 min (section 4).\n- Le plus progressif : 14 petits dépôts depuis le 1er octobre,")
for lab, other, d in (('0x86544e4dfde', 'walletwallet8424', 96), ('walletwallet8424', '0x86544e4dfde', 189)):
    in_section(lab, "- Biais de sélection : ce compte est étudié", f"- Redemption de Kane le 27 oct. à 01:58:15 UTC, en même temps que {other} : faux positif comme lien, c'est un lot de 2 711 comptes en 136 transactions, le déclencheur n'est pas lu. Le retrait, {d} s plus tard, reste un geste propre et rapide face aux autres comptes du lot : indice faible, exploratoire, qui ne prouve aucun lien (section 4).\n- Biais de sélection : ce compte est étudié")
in_section('VidenteRibeira', "- Relations à identifiant stable : ONCHAIN_CONFIRMED 4, PROTOCOL_CONFIRMED 3, SERVICE_INTERACTION 1.", "- Cette sortie est cosignée par `GxjcMTWW…`, qui en paie les frais, 4 s après la réception. `DMmDPF9s…` est donc probablement une adresse de dépôt tenue par ce service, pas une adresse personnelle.\n- Relations à identifiant stable : ONCHAIN_CONFIRMED 4, PROTOCOL_CONFIRMED 3, SERVICE_INTERACTION 1.")
in_section('cookedrice', "- Relations à identifiant stable : ONCHAIN_CONFIRMED 3, PROTOCOL_CONFIRMED 2, SERVICE_INTERACTION 1.", "- Cette sortie est cosignée par `GxjcMTWW…`, qui en paie les frais, 2 s après la réception. `F7ew8r8X…` est donc probablement une adresse de dépôt tenue par ce service, pas une adresse personnelle.\n- Relations à identifiant stable : ONCHAIN_CONFIRMED 3, PROTOCOL_CONFIRMED 2, SERVICE_INTERACTION 1.")
in_section('OuldLm3alem', "- Swap dans la transaction de retrait `0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1` : le reçu montre l'échange, le paiement natif ne laisse pas de log et le montant reçu repose sur l'enregistrement Relay. Solde natif actuel de `0x1B500B6c…5f2c` : 3,14. Ces fonds sont donc repartis, et leur destination n'a pas été lue : les mouvements natifs ne sont pas scannés.",
           "- Swap dans la transaction de retrait `0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1` : le paiement se lit sur la chaîne, `LogTransfer` de 839 893,73 POL vers la clé, log 463. La version 1 écrivait à tort qu'il ne laisse pas de log. La relation reste classée SERVICE_INTERACTION dans `graphs/relations.jsonl`, fichier non modifié.\n- Sortie : 108 s plus tard, 23:52:41 UTC, la clé échange 839 000 POL contre 75 946,74 USDT par `0xdc264714…7c9f`, `0x8c35829294c002aabcd2bd518e88f46f86e4c5a075c6e89938d4532cc62dd2c3`, USDT reçus par la clé. Selon l'enquête flow-trace, non relu ici : les USDT passent le 29 oct. par deBridge, puis 75 724,74 USDC par CCTP vers Hyperliquid, 303 exécutions sur le perpétuel HYPE, et 73 001,19 USDC reviennent sur la même clé, sur Arbitrum, le même jour.")
in_section('0xdd97e6', "- Relations à identifiant stable : ONCHAIN_CONFIRMED 4, PROTOCOL_CONFIRMED 3, SERVICE_INTERACTION 1.", "- `0xca8B1f1a…6165` détient 26,9716 ETH, nonce 0, lu le 2 nov. : aucune sortie depuis la réception.\n- Relations à identifiant stable : ONCHAIN_CONFIRMED 4, PROTOCOL_CONFIRMED 3, SERVICE_INTERACTION 1.")
for lab in SECTIONS:
    z = compl['E6_par_dossier'][SLUG[lab]]['complets']
    start = text.index(f'\n### {lab}\n')
    m = re.compile(r'(\d+) comparateurs sur 42 font aussi court ou plus court\.').search(text, start)
    assert m, lab
    y = m.group(1)
    text = text[:m.start()] + f"{z} comparateur{'s' if z > 1 else ''} sur 20 à historique complet {'font' if z > 1 else 'fait'} aussi court ou plus court. Publié en version 1 : {y} sur 42, lignes coupées comprises." + text[m.end():]
    done.append((1, f'[{lab}] E6 {y}/42 -> {z}/20'))
E4_D2 = {'0x86544e4dfde', 'brace227', 'kraben006', 'Thin-Disclaimer-Life', 'Zoomman17'}
E4_OUT = {'VidenteRibeira', 'WenZhuanBuPei'}
for lab in SECTIONS:
    new = ("- Combinaisons inhabituelles E4 v2 : **hors univers** : aucun achat au 13 oct., puis un seul token à 100 $ ou plus au 23 oct., écarté par un filtre du code absent du plan. E4 ne dit rien de ce compte." if lab in E4_OUT else
           "- Combinaisons inhabituelles E4 v2 : 0 paire aux deux dates, sur les trois graines. E4 ne voit qu'un extrême, section 5." if lab in E4_D2 else
           "- Combinaisons inhabituelles E4 v2 : hors univers au 13 oct., 0 paire au 23 oct. sur les trois graines. E4 ne voit qu'un extrême, section 5.")
    in_section(lab, "- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.", new)

# Section 3
sub("Les liens Relay classés `PROTOCOL_CONFIRMED` portent le même identifiant", "Contre-vérification après audit, depuis les reçus en cache : chaque retrait a une sortie du wallet et une destruction de pUSD du même montant, 25 sur 25, 493 094,756177 $. Chaque dépôt a une frappe du même montant, 46 sur 46, 304 137,63473 $.\n\nLes liens Relay classés `PROTOCOL_CONFIRMED` portent le même identifiant")

# Section 4
sub("Une règle naïve de « financeur commun » relierait **21 paires sur 55**. Après classement, **0 paire** repose sur une adresse discriminante.", "Une règle naïve de « financeur commun » relierait **21 paires sur 55**. Après classement, **0 paire** repose sur une adresse partagée discriminante. **Mais 1 paire sur 55, brace227 et kraben006, a un transfert direct entre clés**, que ce classement par adresses partagées ne pouvait pas voir.")
sub("| 549 sorties vers 454 destinataires en 10 h |", "| Contrat vérifié nommé SwftSwap. 549 sorties vers 454 destinataires en 10 h |")
sub("**Transferts directs.** Scan de 33 adresses (wallets, clés, adresses de pont, destinations), Polygon et Ethereum, stablecoins, pUSD et positions, depuis le 25 sept. : **0 transfert de fonds entre dossiers**. Une seule exécution de carnet d'ordres entre deux dossiers : OuldLm3alem vend 520,97 parts à 0,53 à 0x86544e4dfde, le 26 oct. 13:29:02 UTC, `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. C'est ordinaire sur un carnet. `graphs/direct_transfers.json`.",
    """**Transferts directs.** Le scan d'origine (33 adresses, Polygon et Ethereum, stablecoins, pUSD et positions, depuis le 25 sept., `graphs/direct_transfers.json`) rendait 0 transfert. Il ne lisait ni l'ETH natif ni l'historique ancien des clés : ce « 0 » de la version 1 était faux pour une paire. Après audit : **1 transfert natif direct, brace227 vers kraben006**, détaillé ci-dessous. Selon l'audit, aucun autre sur 27 adresses EVM lues sur Ethereum, Arbitrum et Base, ni en POL natif sur 46 adresses, ni sur les 9 adresses Solana lues. Ce scan n'est pas refait ici. Pour les deux clés de la paire, l'historique Ethereum complet ne montre que ce seul transfert, et leurs seules contreparties communes sont des services : USDC, Relay Depository, solveur Relay, SwftSwap.

**Exécutions et transactions communes.** Les onze historiques partagent 14 transactions, toutes décodées (`evidence/contre_verification_20261102/transactions_communes.json`). 8 sont des paiements en lot : 5 rebates ou récompenses, 3 redemptions de 20 comptes chacune. 5 sont des exécutions où deux dossiers sont makers face au même tiers, sans échange entre eux, dont une pour brace227 et kraben006 (24 oct. 16:41:44, ventes de Mbappé à 0,84). **1 seule est une exécution directe :** OuldLm3alem vend 520,97 parts à 0,53 à 0x86544e4dfde, le 26 oct. 13:29:02 UTC, `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. C'est ordinaire sur un carnet.""")
sub("### Taux de base et faux positifs\n",
    """### Un wallet non nommé financé par la clé de brace227

Signalé par l'enquête flow-trace, relu ici sur la chaîne : `evidence/contre_verification_20261102/wallet_0xa8e6.json`. **La version 1 écrivait qu'aucun wallet supplémentaire n'était relié aux onze : c'est faux.** Ce financement pèse bien plus que les 5,53 $ du circuit décrit plus bas.

**Le lien.** Le wallet `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` a pour propriétaire, `owner()` lu sur Polygon, `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`. La clé de brace227 envoie à cette clé 2 210 USDC le 9 oct. à 20:28:35 UTC, `0x7e3aecb9b41e6d3f92f25b8760228f15e9b55e798cd27977eb7170445cf64349`, et 2 960 USDC le 10 oct. à 00:51:11, `0xb07c3c53a713d98aea1d1bd5d6facf849b6edc675c0fe2cfd3df5b791db20add`. Sur Ethereum, ce sont ses seules entrées de jetons avant le retrait du 27 oct., et sa plus ancienne transaction listée date du 9 oct. à 20:32:11, page complète (nonce de 14 pour 13 envois listés, écart non expliqué). Ses deux envois à Relay Depository, 2 200 et 2 965 USDC, sont reliés à ces deux dépôts par l'enregistrement Relay, `user` et `recipient` compris (`wallet_0xa8e6_preuves.json`), sans recoupement ici par identifiant sur la chaîne. **Selon cette comptabilité, les dépôts de ce wallet viennent de la clé de brace227.** Autres chaînes non lues ici, hormis un nonce de 0 sur Polygon. Selon flow-trace, non relu ici : le wallet est créé le 8 oct. à 10:13:20 UTC, la veille des premiers fonds, `0xa6e22997…5d7b`.

**Le partage.** Les arrivées de SwftSwap des 9 et 10 oct. sur la clé de brace227 sont coupées en deux, celle du 16 oct. va tout entière au wallet de brace227. Au total, 34,2 % des 15 096,29 USDC reçus de SwftSwap vont à `0x48ec…` :

| Arrivée sur la clé de brace227 | Vers `0x48ec…` | Part | Vers le wallet de brace227 |
|---|---:|---:|---:|
| 9 oct. 20:03 et 20:06, 4 421,41 USDC | 2 210,00 | 49,98 % | 2 186,43 |
| 10 oct. 00:26, 5 925,84 USDC | 2 960,00 | 49,95 % | 2 986,82, en trois dépôts |
| **Sous-total, 9 et 10 oct.** | **5 170,00** | | **5 173,25** |
| 16 oct. 19:16, 4 749,03 USDC | 0 | 0 % | 4 749,54, en trois dépôts |

**Les paris.** Le wallet dépose 2 200 $ à 20:36:28 et achète à 20:37:10. brace227 dépose 2 186,43 $ à 20:49:05 et achète à 20:50, dont du Kane dès 21:14. Le wallet fait 16 achats, tous sur Kane Yes, 5 164,99 $ pour 8 061,89 parts, du 9 oct. à 20:37 au 11 oct. à 17:54 UTC. Il ne vend jamais.

**La sortie.** Redemption de 8 061,89 $ à 01:58:20 le 27 oct., dans le lot Kane. Retrait de 8 061,90 $ vers `0x48ec…` 16 h 51 min plus tard, à 18:49:06. Retraits moins dépôts : 2 896,90 $, hors des totaux de la section 2. Aucun retour vers la clé de brace227 sur Ethereum. Le 2 nov., `0x48ec…` détient 5 062,18 USDC. Il envoie aussi 2 501 USDC à `0x6A2522Df…7973` le 28 oct., rendus le 29 oct., adresse non analysée. Le 29 oct., il échange 3 000 USDC contre 2 969,57 mUSD, envoyés à Relay Depository : suite non lue ici.

**Ce que cela établit :** selon cette comptabilité, une même clé a financé deux comptes Polymarket, à parts presque égales les 9 et 10 oct., et les deux ont acheté Kane le 9 oct. à moins d'une heure d'écart, 741,47 $ chez brace227. **Ce que cela n'établit pas :** un propriétaire commun, puisque financer un compte n'est pas le contrôler, ni une information privilégiée. Rien ne dit non plus que c'est le douzième compte allégué par la presse (`reports/inventaire_adresses.md`).

| Hypothèse, aucune n'est une conclusion | Pour | Contre ou limite |
|---|---|---|
| Un même opérateur, deux comptes | Aucune transaction listée avant le 9 oct. sur Ethereum, dépôts venus de l'autre clé, parts presque égales les 9 et 10 oct. | Deux clés. brace227 vend son Kane à 0,999 le 26 oct. à 23:10, ce wallet attend le lot puis 16 h. 9 issues d'un côté, 1 de l'autre. La tranche du 16 oct. va tout entière à brace227. Son Kane des 9 et 10 oct. ne pèse que 954,04 $ sur 4 917,62 $ d'achats |
| Deux personnes qui misent à parts égales | Parts égales les 9 et 10 oct., deux clés, sorties différentes | Aucune trace de cet accord, invérifiable |
| Prêt ou don | Compatible avec deux virements ponctuels | Aucun remboursement visible sur Ethereum à ce jour, invérifiable |

**Autre proximité.** Dans les sorties gelées, ce wallet figure aussi dans une rafale E2 de 60 min sur Kane, le 11 oct. à 13:34:42 UTC, 10 667,19 $, avec 0x86544e4dfde et walletwallet8424 (`collective/derived/A_E2.json`). Ni brace227 ni aucun transfert entre eux n'y figurent. C'est une proximité d'achat sur un marché actif, pas un lien.

**Pourquoi la version 1 ne l'a pas vu, et ce que cela implique.** Le dossier suit les dépôts et les sorties de Polymarket, pas ce que la clé envoie ailleurs. Ce wallet ne détient pas Mbappé, donc il n'est pas dans la capture Upside. Avec un seul token, il est aussi écarté d'E4. **Selon flow-trace, c'est le seul wallet actif** parmi 50 adresses personnelles testées autour des onze, 94 essais, 44 adresses sous 2 formes de wallet et 6 clés de dossiers sous l'ancienne forme seulement (`state/personal_wallets.json`), calcul validé sur 11 wallets connus. Les anciens proxys Safe et Magic ne sont pas testés : d'autres peuvent exister.

### Le circuit 7XUJs, clé de brace227, clé de kraben006

Heures UTC, 4 octobre 2026. Données en wei : `evidence/contre_verification_20261102/circuit_7xujs_brace_kraben.json`.

| # | Heure | De | Vers | Montant | Preuve | Niveau |
|---|---|---|---|---|---|---|
| 1 | 13:52:35 | `7XUJsJBNp7…frZc` (Solana) | Relay | 4,62476 USDT, plus 0,0298 de frais | `3XaPp5kRsL5M…NfEL` | **Démontré** |
| 2 | 13:52:47 | solveur Relay `0xadA5bb90…F7CB` | clé de brace227 `0xc852b093…af26` | 0,001692408 ETH | Même identifiant `0x30484595…7867` à l'octet près dans l'instruction Solana et le calldata de `0xb17e1c46…ce3c`, sans dépendre de l'API | **Démontré** : même ordre, valeur équivalente, pas les mêmes jetons |
| 3 | 13:54:35 | clé de brace227 | clé de kraben006 `0x101b5f4d…fb65` | 0,002048944 ETH, environ 5,53 $ | `0xd07bea20…2b98`, bloc 26119420, 2 nœuds, envoi simple sans données, 21 000 gas, succès | **Démontré.** Au moins 81,4 % du montant vient forcément du maillon 2 |
| 4 | 23:48:47 | clé de kraben006 | `0x7e67dF45…6E23` | 0,00247406 ETH | `0x1a39308b…dd71`, Blockscout | Transaction démontrée. **Continuité limitée** : au moins 22,7 % de ce qui a été reçu, 23,9 % gas compris |
| 5 | 23:56:59 | `0x7e67dF45…6E23` | `0x3f3Ee0a9…207B` | 0,00241406 ETH | `0x22710b5e…9c26`, Blockscout | Continuité à l'adresse : 1 entrée, 1 sortie. **Destination étiquetée « ChangeNOW Dep » par Blockscout**, source unique, non recoupée, environ 321 000 transactions selon un compteur Blockscout qui rend 0 pour `0x7e67…`, donc peu fiable |

**Continuité démontrée, maillons 1 à 3.** Le maillon 2 est prouvé par la chaîne seule. Pour le maillon 3, la clé détenait 0,000380298 ETH et n'a rien reçu d'autre entre les deux transactions : au moins 0,001668646 ETH envoyés proviennent donc du paiement. Soldes des deux clés lus sur Blockscout et recoupés au wei près à ces blocs sur un nœud d'archive.

**Simple succession, maillon 4.** Il arrive 9 h 54 min plus tard, sur une clé qui détenait déjà 0,002007933 ETH. Seuls 0,000466127 ETH envoyés, 0,000489889 gas compris, sont imposés par la comptabilité. Attribuer le reste à ce transfert dépendrait d'une convention de traçage : l'ETH est fongible. Aucune lecture ne relie ces montants au capital d'un dépôt Polymarket, fait en USDC. L'ETH étant fongible, le solde de la clé a pu payer le gas de ses dépôts suivants, 0,00018 ETH consommés après l'envoi. Selon flow-trace, `0x7e67…` a le profil d'une adresse de dépôt ChangeNOW : une partie de cet ETH a pu être revendue, ce qui n'est pas démontré.

**Le payeur Solana.** `7XUJs…` compte 8 signatures en tout, depuis le 6 juin 2026 : il reçoit 304,70 USDT, en envoie 300, et le 4 octobre envoie presque tout le reste. Il garde 0,047 USDT. Une seule requête Relay à son nom. Aucune des 27 adresses qu'il touche n'apparaît dans les dossiers, hormis le jeton USDT lui-même.

**Portée du vidage de la clé de brace227.** Le transfert laisse 0,000000494 ETH : 98,85 % du solde envoyés, 1,12 % de gas, 0,02 % restant. Cela ressemble à un envoi du solde maximal, pas à un montant choisi.

- *Ce qui est vidé :* l'ETH seul, et la clé était déjà presque vide. Ses USDT étaient à 0 depuis le 28 avril 2025.
- *Ce n'est ni un abandon, ni un compte drainé :* la clé reçoit 4 337,52 USDC de SwftSwap le 9 octobre, et 22 024,57 USDC y dorment encore le 2 novembre.
- *Ensuite :* le 9 octobre, ses transactions passent par des relais de gas à fort trafic, étiquetés MetaMask par Blockscout, et le 16 octobre elle reçoit 0,00202 ETH de `0x2CfF890f…`, étiqueté NEAR Intents. Le lien de cause avec le vidage n'est pas établi.
- *En montant, ce n'est pas un financement significatif :* 5,53 $, soit 0,055 % des dépôts de brace227 et 0,097 % de ceux de kraben006.
- *La lecture « don de gas » de l'audit est peu soutenue :* la clé de kraben006 détenait déjà 0,0020 ETH et n'en a consommé que 0,00018 depuis. Un donateur peut toutefois ignorer le solde du destinataire.
- *« Première sortie en 17 mois » ne vaut que pour Ethereum.* La clé a un nonce de 109 sur BSC, visible dans son dossier mais jamais lu. Lu par l'enquête flow-trace, relu ici dans son fichier : 5 sorties de décembre 2024 au 17 mai 2025 à 11:52:55 UTC, aucune vers une adresse de dossier, 104 antérieures à juillet 2022 non énumérées. Sa dernière sortie précède donc le transfert de 16 mois et demi, toutes chaînes lues. Entrées BSC non lues.

**Ce que ce circuit établit :** une transaction signée par la clé de brace227 vise l'adresse de celle de kraben006, sans service entre elles. Qui l'a signée, et s'il connaissait le destinataire, reste inconnu. **Ce qu'il n'établit pas :** un propriétaire commun, un pari concerté, une information privilégiée.

| Hypothèse, aucune n'est une conclusion | Pour | Contre ou limite |
|---|---|---|
| Un même opérateur regroupe ses restes | Résidu d'USDT Solana et résidu d'ETH réunis en 2 min, envoi du solde maximal | Aucun autre transfert direct, aucune contrepartie personnelle commune sur Ethereum |
| Deux personnes qui se connaissent, petit paiement | Un seul envoi de 5,53 $ suffit à l'expliquer | Pas de mémo ni de contrepartie visible, invérifiable |
| Paiement sans rapport avec les paris | 5 jours avant le premier achat de brace227 | kraben006 était déjà actif, invérifiable |
| Clé compromise | Sortie 108 s après la réception | Peu probable : 22 024,57 USDC restent sur la clé, qui continue à financer des comptes ensuite |
| Erreur d'adresse | La clé de kraben006 reçoit des transactions de leurre à 0 valeur | Peu probable, et aucune trace d'une relation antérieure qui l'expliquerait |

Aucune donnée lue ici ne les départage : entrées BSC et sauts de la section 7 non lus. Un exchange ou un fournisseur de portefeuille pourrait le faire sur demande légale.

### Retraits rapprochés : ce que le calendrier explique, et ce qu'il n'explique pas

Tests exploratoires, écrits après avoir vu les données, non inscrits au registre gelé. Liste : `evidence/contre_verification_20261102/tests_exploratoires.jsonl`. Résultats : `stats_retraits_kane.json`.

**brace227 et kraben006, 2,8 min d'écart : aucun signal mesurable.** Kane atteint 0,99 à 22:50:24 UTC le 26 octobre. kraben006 retire 48 s après sa vente à 0,999, brace227 136 s après la sienne. Parmi 20 autres vendeurs comparables (5 000 $ ou plus, dans les 30 min après le premier 0,99), **10 retirent eux aussi en moins de 5 min**, p = 0,29 : la vitesse est ordinaire. Leurs ventes sont à 78 s d'écart, pour un écart médian de 45 s entre deux ventes consécutives de ces 22 vendeurs. Leurs retraits sont à 166 s : 8 paires sur 105 font aussi peu parmi les 15 vendeurs qui retirent sous 24 h, sans correction pour le choix de cette paire. Rien ici ne les distingue nettement.

**0x86544e4dfde et walletwallet8424, 1,6 min d'écart : deux faits distincts.**

- *La redemption simultanée est un faux positif.* Le marché Kane est résolu sur la chaîne à 01:57:41 UTC le 27 octobre, `0xf3684759…2430`. De 01:58:14 à 01:58:24, **2 711 comptes sont remboursés en 136 transactions**, 6 204 783,28 $. Les deux comptes y sont, à 01:58:15. Le déclencheur n'est pas lu, mais cette forme rend une décision individuelle synchrone très improbable.
- *La vitesse de retrait ne s'explique pas par le calendrier.* Ils retirent 96 s et 189 s après leur redemption (91 et 184 s après le repère de 01:58:20), et tout leur solde. L'audit classait ce point en faux positif : c'est trop fort.

Face aux autres comptes du lot à 5 000 $ ou plus. 178 lus, 175 retenus : 2 atteignent le plafond de lecture et ne sont pas comptés comme « sans retrait », 1 est le wallet financé par la clé de brace227, décrit plus haut, qui retire 16 h 51 min après. Le p teste 2 nommés sur 2 sous 5 min (Fisher unilatéral). La colonne x 55 corrige le choix de cette paire parmi 55. Sept strates sur treize, toutes dans `reports/CONTRE_VERIFICATION.md`.

| Comparateurs | n | Retrait en moins de 5 min | p brut | p x 55 |
|---|---:|---:|---:|---:|
| Tous | 175 | 1 | 0,0002 | 0,011 |
| Même taille, 20 000 à 50 000 $ | 40 | 0 | 0,0012 | 0,064 |
| Compte de 30 jours ou moins | 22 | 0 | 0,0036 | 0,20 |
| Aucun trade dans l'heure | 124 | 1 | 0,0004 | 0,021 |
| A retiré sous 24 h | 48 | 1 | 0,0024 | 0,13 |
| A retiré sous 24 h, Kane dernière clôture | 27 | 0 | 0,0025 | 0,14 |
| Compte de 60 jours ou moins, a retiré sous 24 h | 19 | 0 | 0,0048 | 0,26 |

Lecture :

- **Atypique à l'état brut, dans toutes les strates. Non significatif après correction dans les strates les plus comparables.**
- **L'écart de 93 s entre eux n'ajoute rien.** Une fois admis que les deux sont rapides, deux délais tirés au hasard sous 5 min sont aussi proches dans 52 % des cas.
- **C'est plutôt un trait du groupe que de la paire.** Entre la dernière clôture et le retrait principal, 8 nommés sur 11 mettent moins de 10 min, contre 9 sur 48 comparateurs qui retirent sous 24 h, p = 0,0011 non corrigé. Le taux des nommés sous 5 min, 4 sur 11, inclut ces deux comptes : appliqué à eux, 13 %. Sur les 9 autres nommés, 2 sur 9 donne 4,9 %. Sélection par la presse dans les deux cas.
- **Biais non contrôlés.** La presse a choisi les nommés après coup, parmi des comptes récents et concentrés. Les strates sont emboîtées, choisies après coup, sur un seul événement. Non mesurés : notifications, logiciel de portefeuille, fuseau horaire (02:00 UTC), autres positions au-delà de 24 h. Les deux clés ont le même contrat de délégation 7702 sur Polygon : le nombre d'adresses qui le partagent n'est pas mesuré ici, et rien n'en fait un lien.

Classement : indice faible, exploratoire. Compatible avec deux comptes dont Kane est la dernière position et qui guettent ce paiement, avec une consigne commune, ou avec un même opérateur. Le test ne les départage pas.

### Taux de base et faux positifs
""")
a = text.index("Même lecteur sur un dépôt par wallet, 11 nommés et 50 comparateurs :")
b = text.index("**Faux positifs identifiés et écartés :**")
text = text[:a] + """**Le tableau publié en version 1 n'est pas valable.** Il comptait 50 comparateurs lus comme s'ils étaient tous mesurés. Prévus : 83 lignes, soit 78 wallets distincts, 5 figurant dans deux groupes. **Seuls 30 étaient utilisables, 48 ne l'étaient pas :**

| Cause | Wallets |
|---|---:|
| Jamais lus, tous des comptes frais | 28 |
| Lus, sans origine : la ligne comptait comme « pas KuCoin, pas Solana » | 16 |
| Origine lue, mais historique coupé avant le premier achat | 4 |
| **Total inutilisable** | **48** |

L'audit et la version 2 de ce rapport écrivaient 53 sur 83, en comptant comme jamais lus 5 wallets déjà lus sous un autre groupe.

**Les 17 historiques coupés.** `tools/baseline.py` s'arrête à 12 pages, 6 000 lignes, sans le signaler. Rejoué depuis le cache : les 17 s'arrêtent avant leur premier achat de la famille, 17 sur 17, dont 13 sans origine lue. Le dépôt retenu précède cet achat de 61 à 736 jours, par exemple 0,04 $ en octobre 2024 pour un achat de 2026. Aucun nommé n'est touché : 11 historiques sur 11 sont complets, donc la comptabilité des dossiers ne bouge pas. Liste complète : `reports/CONTRE_VERIFICATION.md`.

**Relecture complète par l'enquête flow-trace.** 77 témoins lus sur 78, tous les dépôts lus depuis l'API, mêmes groupes : `~/Projects/PolySentinel-flow-trace/state/compare_rates.json`, `reports/COMMON_FUNDERS.md`, section 4. RAPPORTÉ : son lecteur n'est pas refait ici. Recoupé ici : ses p sont égaux à mon recalcul, et sur 30 wallets lus par nos deux lecteurs, l'origine concorde 29 fois (`evidence/contre_verification_20261102/recoupe_flow_trace.json`).

| Trait, un dépôt par wallet | Nommés | Tous témoins | p | Comptes frais | p |
|---|---|---:|---:|---:|---:|
| Financement moins d'1 h avant le premier achat | 9/11 | 41/76 | 0,074 | 32/39 | 0,69 |
| Origine Solana, par Relay | 3/11 | 6/68 | 0,11 | 3/39 | 0,11 |
| KuCoin Hot Wallet 2, parmi les origines Solana | 3/3 | 1/6 | 0,048 | 0/3 | 0,050 |
| Dépôt via `0xc8a6…`, VaultDepositooor | 5/11 | 9/77 | 0,013 | 5/39 | 0,030 |
| Adresse de pont 7702 | 6/11 | 59/77 | 0,97 | 34/39 | 1,00 |
| Clé touche SwftSwap | 2/11 | 0/54 | 0,026 | 0/39 | 0,045 |
| Clé reçoit de MetaMask Gas Station | 3/11 | 2/54 | 0,031 | 1/39 | 0,029 |

Fisher unilatéral, non corrigé. **Aucun trait ne passe le seuil corrigé pour 9 tests, 0,0056.** Traits choisis après coup, groupe choisi par la presse : exploratoire.

- **Financement moins d'une heure : rien de distinctif** face aux comptes frais, 9/11 contre 32/39.
- **Le « KuCoin plus fréquent » de la version 1, 3/11 contre 1/50, est retiré.** Reste un indice faible : Solana 3/11 contre 6/68, et KuCoin 3/3 contre 1/6 sur 9 wallets seulement. Son libellé n'est lu que sur une origine Solana, donc c'est la même observation, et l'étiquette a une source unique.
- **`0xc8a6…` est l'écart le plus net.** C'est un outil de dépôt, contrat vérifié selon flow-trace, pas un lien entre personnes.
- **SwftSwap :** les 2 comptes sont brace227 et kraben006, ce n'est pas un trait indépendant de leur lien. **MetaMask Gas Station :** un logiciel de portefeuille.
- **Liens directs entre clés (Ethereum, Polygon, Arbitrum) :** 1 sur 55 paires nommées, 0 sur 1 431 paires de témoins, dont 0 sur 741 chez les comptes frais. Ce n'est pas un test, les paires n'étant pas indépendantes, et seules 54 clés sont lisibles sur 77 wallets. Mais un tel transfert n'est pas banal dans ces témoins.

### Résultats de l'enquête flow-trace, non revérifiés ici

Rapports finaux : `~/Projects/PolySentinel-flow-trace/reports/`. Même famille de modèle : pas un audit indépendant au sens fort.

- **Origine des fonds :** Relay est le seul service commun aux onze. Plus de la moitié des 304 137,63 $ remonte à des plateformes étiquetées : KuCoin Hot Wallet 2 pour 5 comptes et 102 833,93 $, Binance pour 3 comptes et 65 755,73 $, plus Revolut et BloFin. Le reste vient de services non attribués, de SwftSwap et de Chainflip.
- **Sorties :** **aucune destination finale commune.** Environ 74 % des 493 094,76 $ n'avaient pas quitté leur première adresse ou y étaient revenus le 2 nov. Trois comptes ont déposé 118 371,00 $ chez des services non identifiés. Zoomman17 a envoyé 6 893,00 USDC vers une adresse balayée par `0xf7c8da79…d921`, étiqueté Revolut 5.
- **Mixeurs et Monero :** aucune interaction lue avec Tornado Cash, Railgun ou un contrat de confidentialité étiqueté, sur les adresses connues. Monero absent des données accessibles, ni démontré ni exclu derrière les comptes de plateforme et les services non identifiés.
- **Étiquettes :** `0xee7ae85f…4055`, partagé par OuldLm3alem et WenZhuanBuPei, est étiqueté Binance: Hot Wallet 34, `0x8894e0a0…d4e3`, source de Thin, Binance: Hot Wallet. Une étiquette dit ce qu'une source a écrit, elle n'identifie aucun client.
- **Recoupement :** 46 dépôts et 25 retraits rapprochés de la chaîne par un autre lecteur, soldes pUSD égaux sur 11 wallets. Mêmes totaux qu'ici.

""" + text[b:]
done.append((1, 'Taux de base, section remplacée'))
sub("- `GxjcMTWW…` : VidenteRibeira et cookedrice y déposent à un jour d'écart (51 489,00 USDT, 39 158,00 USDC). Service à 1 % de frais, payant par morceaux.", "- `GxjcMTWW…` : VidenteRibeira et cookedrice y déposent à un jour d'écart (51 489,00 USDT, 39 158,00 USDC). Les deux sorties sont cosignées par ce service, qui en paie les frais, 4 et 2 s après réception : le « même comportement » de sortie est donc son automatisme, seul le choix commun du service reste à expliquer. Service à 1 % de frais, payant par morceaux.")
sub("- Pièges de lecture évités :", "- Le candidat de 59,09 POL de `0xc590175e…c02b` vers `0x408ce42a…c5b3`, repéré par l'audit, n'est pas un transfert entre dossiers : dans `0x4b89cf4f…5ac8`, `0x408c…` paie lui-même 5,62 USDC et reçoit ces POL. `0xc590…` est un contrat d'échange mutualisé qui a seulement servi aussi au dépôt de walletwallet8424.\n- Relais `0xb42f…` et `0xb01c…` et adresses `0xc066…`, `0xe347…`, partagés par plusieurs dossiers : 160 000 à 850 000 transactions chacun selon l'audit, écartés.\n- Redemptions dans une même transaction entre 0x86544e4dfde et cookedrice, VidenteRibeira et WenZhuanBuPei : lots de 20 comptes, sans lien.\n- Pièges de lecture évités :")

# Section 5
sub("Plan gelé avant tout calcul de taux (`collective/analysis_plan.md`, `PROTOCOL.lock`), partie A scellée avant la lecture des noms et des résultats. **L'auteur connaissait l'affaire : aucune validation n'en découle.**", "Plan gelé avant tout calcul de taux (`collective/analysis_plan.md`, `PROTOCOL.lock`), partie A scellée le 1er nov. à 23:28 UTC, 6 fichiers sur 6 intacts. C'est le code de A qui ne lit pas les noms, pas l'auteur, qui les connaissait avant le gel. **L'auteur connaissait l'affaire : aucune validation n'en découle.**")
sub("**Verdict fixé d'avance, au 13 oct. 18:51 UTC comme au 23 oct. 15:17 UTC : `VISIBLE_NON_SPECIFIQUE`.**", "**Verdict fixé d'avance, au 13 oct. 18:51 UTC comme au 23 oct. 15:17 UTC : `VISIBLE_NON_SPECIFIQUE`.** Il est appliqué à la main dans l'étude, recalculé par code par l'audit : il tient, car le rang l'emporte seul. La date de 18:51:00 tombe 60 s après un achat de Thin à 18:50:00 : 15 053,97 $ dans son activité, dont 14 743,44 $ en flux taker. Le plan ne justifie pas cette date. Selon l'audit, E1 s'arrête au tick de 18:00 et ne voit pas cet achat, E4 et les sommes « avant le 13 octobre » l'incluent.")
sub("Témoins tirés : 4 sur 59. Femmes : 0 sur 148, sans puissance.", "Témoins tirés : 4 sur 59. Femmes : 0 sur 148, sans puissance. Portée : sur tables synthétiques, A0 détecte une cohorte d'au moins 3 wallets à 4 000 $ chacun en moins de 72 h, et ne détecte pas 2 wallets. Puissance sur données réelles inconnue : aucun cas vérifié n'existe (`collective/controles/CONTROLES.md`).")
sub("Charge : au plus 12 nouveaux tokens par jour hors famille.", "Charge : au plus 12 premières alertes par jour hors famille. Le plan parle de tokens en alerte : jusqu'à 37 par jour selon une estimation de l'audit, non recomptés exactement. Le verdict n'en dépend pas.")
sub("La fraîcheur ne se concentre pas plus qu'au hasard. Aucun p de cette étude n'approche le seuil de Bonferroni du registre, voir `collective/results.md`.", "Au tirage gelé, pas de concentration détectée. La lecture dépend du nul, selon l'audit : 0,174 et 0,318 en recalculant ce tirage, 0,15 et 0,87 avec un mélange réalisable, 0,008 et 0,077 en variante stricte, non retenue car elle abaisse le nul, et 0,012 sur les témoins au 13 oct. Le tirage gelé laisse 10 à 13 % des dates tomber après l'achat. Le seuil de Bonferroni du registre, 3,57e-07, est inatteignable à 1 000 tirages : ne pas l'atteindre ne prouve rien.")
sub("Reproduction en copie fraîche : E1, E1G, E2, E3 et le placebo identiques au sceau (`collective/audit/REPRODUCTION.json`).", "Reproduction en copie fraîche : E1, E1G, E2, E3 et le placebo identiques au sceau (`collective/audit/REPRODUCTION.json`). E4 v2 relancé après audit sur ses trois graines et deux dates, sous un autre hachage : identique, 6 sur 6.")
sub("50 comparateurs pour le financement, dont les 6 non surlignés ;", "50 comparateurs lus sur 78 wallets distincts prévus pour le financement, dont 30 utilisables, plus la relecture de 77 témoins par flow-trace (section 4) ;")
sub("dont 57 544,64 $ avant le 13 oct. 18:51 UTC et 155 188,28 $ avant l'article.", "dont 57 544,64 $ avant le 13 oct. 18:51 UTC, 15 053,97 $ de cette somme dans la dernière minute, et 155 188,28 $ avant l'article.")
sub("Ces achats sont étalés sur des semaines, pas groupés.", "Ces achats sont étalés sur des semaines, pas groupés. Au-delà de ce flux, sur toute leur activité : brace227 et kraben006 ont 9 achats à moins de 5 min d'écart, dédoublonnés à 60 s, 0 avant le 13 oct., 1 le 17 oct., **8 sur Kane le 24 oct., le lendemain de l'article**. L'audit donne p = 0,0012 avec des décalages de plusieurs jours, au-dessus du seuil corrigé de 0,00091. Dans le seul créneau de 14:00 à 17:00 UTC, un décalage donne p = 0,40, sur 9 achats de brace227 sur 17, moyenne nulle 7,38 : ils achètent beaucoup au même moment de la journée, sans synchronie plus fine. Ce sont pourtant les deux plus gros acheteurs taker du créneau, 45 % des 21 753 $ achetés, et aucun des 14 autres acheteurs à 100 $ ou plus n'atteint leurs scores, maximum 7 contre 9 et 5 contre 7. Exploratoire, créneau choisi après coup. C'est un fait à instruire, pas une preuve.")
sub("**Combinaisons de paris (E4 v2, trois graines) :** 12 paires inhabituelles au 13 octobre, 37 au 23 octobre, dont **0 impliquant un compte nommé**. 23 paires stables sur les trois graines au 23 octobre. Le nombre change avec la graine (25 à 34), donc il ne faut pas lire ce chiffre au point près.",
    "**Combinaisons de paris (E4 v2, trois graines) :** par graine, 11, 11 et 12 paires inhabituelles au 13 octobre, 31, 25 et 34 au 23 octobre, soit 12 et 37 en union. 23 paires stables sur les trois graines au 23 octobre. **0 paire nommée au-dessus du seuil, ce qui ne veut pas dire 0 paire nommée similaire.** Le code exige 2 tokens à 100 $, filtre absent du plan. Au 23 octobre, il écarte VidenteRibeira et WenZhuanBuPei : **19 paires nommées sur 55 ne sont jamais testées**. Au 13 octobre, **45 sur 55** : 40 parce qu'un des deux comptes n'avait encore rien acheté sur la famille, 5 par ce filtre, qui écarte walletwallet8424. À cette dernière date, le seuil pour 1 ou 2 tokens communs égale le maximum possible : une telle paire ne peut pas le dépasser. Le seuil est un maximum sur toutes les paires et ne voit qu'un extrême : la meilleure paire nommée, OuldLm3alem et 0xdd97e6, est à 0,90 du seuil, selon l'audit. L'audit relève aussi un chevauchement du groupe nommé plus fort que des groupes tirés sur le même token au 23 octobre (part à ou au-dessus : 0,04), pas au 13 (0,27) : exploratoire, non corrigé, confondu avec la sélection par la presse.")
sub("**Financement avant achat :** écart médian 2,6 min chez les nommés, 9/11 sous une heure. Non surlignés 2/6, même token 1/10, token opposé 7/27. Confondu avec l'âge : un compte neuf dépose puis mise.", "**Financement avant achat :** écart médian 2,6 min chez les nommés, 9/11 sous une heure. Le 10/43, p = 0,0006, publié dans l'étude est surestimé : 21 lignes sur 43 sont coupées, et 38 wallets y comptent pour 43 lignes. Sur les 20 comparateurs distincts à historique complet et écart mesurable : 9/20, p = 0,052. **Relecture complète de l'enquête flow-trace : 9/11 contre 41/76, p = 0,074, et contre 32/39 comptes frais, p = 0,69, rien de distinctif.** E6 est exploratoire : écrit après le sceau et après la lecture de E5. Confondu avec l'âge : un compte neuf dépose puis mise.")
sub("| Ont-ils misé au même moment ? | Non, pas de manière distincte : étalés du 1er au 26 octobre, peu de paires proches. |", "| Ont-ils misé au même moment ? | Pas de manière distincte au niveau du groupe : étalés du 1er au 26 octobre, peu de paires proches. Deux cas à instruire : brace227 et kraben006 le 24 oct., brace227 et `0xa8e64a3c…` le 9 oct. |")
sub("| Combinaisons statistiquement rares ? | Non établi : aucune paire nommée dans E4 v2, combinaison exacte déjà cotée environ 28 %. |", "| Combinaisons statistiquement rares ? | Non tranché : aucune paire nommée au-dessus du seuil d'E4 v2, mais 19 paires sur 55 non testées. Combinaison exacte déjà cotée environ 28 %. |")
sub("| Financements similaires avant les achats ? | Oui en apparence, mais confondu avec l'âge des comptes. |", "| Financements similaires avant les achats ? | Oui, comme 32 comptes frais sur 39 : rien de distinctif, écart surestimé en version 1. |")
sub("| Routes communes ? | Oui, uniquement des services. Aucune discriminante. |", "| Routes communes ? | Oui, uniquement des services, aucune adresse partagée discriminante. À part : un transfert direct brace227 vers kraben006, hors service. |")

# Section 6
sub("Sur les sauts lus, **aucune interaction avec une adresse étiquetée ChangeNOW ou FixedFloat, et aucun échange XMR**. Le statut `XMR_VISIBILITY_BOUNDARY` n'est donc jamais posé. Cela n'exclut rien :",
    """**La version 1 écrivait « aucune interaction avec une adresse étiquetée ChangeNOW » : c'est faux pour la clé de kraben006.** Les étiquettes publiques de Blockscout en portent deux, absentes de `tools/services.json`, source unique, non recoupée (`evidence/contre_verification_20261102/etiquettes_blockscout.json`) :

- `0xdd3d72C53Ff982ff59853da71158bf1538b3Ceee`, « ChangeNOW: Hot Wallet 3 », envoie 654,47 et 180,38 USDC à cette clé le 23 février 2026, `0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219` et `0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80`, sept mois avant l'affaire.
- `0x3f3Ee0a9cAC2d01DB44001eca3E8382fbe40207B`, « ChangeNOW Dep », reçoit 0,00241406 ETH le 4 octobre, maillon 5 du circuit de la section 4.

Ces étiquettes ne disent ni qui a envoyé ces fonds, ni si un échange a eu lieu, ni ce qu'il aurait rendu, et elles ne relient pas ces fonds à un pari. **Aucun échange XMR n'est observé.** Le statut `XMR_VISIBILITY_BOUNDARY` n'est pas posé : ce qui sort de ChangeNOW n'est pas visible d'ici, et le poser ou non reste une décision de Benjamin. Autres étiquettes sur la clé de brace227, lues sans analyse : THORChain Router (7 USDC le 12 oct.), NEAR Intents (0,00202 ETH le 16 oct.), BloFin: Hot Wallet 1 (110,20 USDC le 20 oct., déposés ensuite), Bridgers (avril 2025), et en 2022 des adresses KuCoin et Binance.

**Ma relecture ne couvre que ces deux clés sur Ethereum.** Selon l'enquête flow-trace, qui a relu ces étiquettes sur 73 adresses de services, 40 étiquetées (`evidence/blockscout_tags.json`), ChangeNOW est le seul service proposant XMR rencontré, avec un troisième point : `0x3eaef6d5…`, qu'il finance, envoie 291,32 USDT à la clé de brace227 en janvier 2025. Aucune interaction lue avec Tornado Cash, Railgun ou FixedFloat. Une rupture de trace n'est pas un indice de Monero. Tout cela reste partiel :""")
sub("`GxjcMTWW…` est le point le plus proche : un service non identifié qui prélève 1 % et paie par morceaux. Rien ne permet de dire ce qu'il est, ni de suivre ce qui en sort.", "`GxjcMTWW…` est le point le plus proche : un service non identifié qui prélève 1 %, paie par morceaux et cosigne les sorties de ses adresses de dépôt probables. Rien ne permet de dire ce qu'il est, ni de suivre ce qui en sort. `0xc1d13492…a1b5`, utilisé par brace227 et kraben006, est un contrat vérifié nommé SwftSwap, service d'échange de la même famille, absent de ces listes.")

# Section 7
sub("- Stablecoins lus dans les logs : les mouvements natifs (ETH, POL, BNB, SOL) ne le sont pas, sauf là où un enregistrement Relay les nomme. Exemple : 0xdd97e6 sort en ETH, OuldLm3alem en partie en jeton natif.", "- Le scan d'origine lit les stablecoins dans les logs, pas les mouvements natifs. Ajoutés par l'audit, non refaits ici sauf les deux clés sur Ethereum : Ethereum, Arbitrum et Base sur 27 adresses, POL natif sur 46 adresses. Selon flow-trace, natif lu sur Ethereum, Polygon, Arbitrum et Optimism, entrées BSC et Base non lues, Solana limité à 60 transactions par adresse. Plafonnés dans le scan de l'audit : historiques à 3 pages sur 4 adresses (`0x3ab2…`, `0x7ff8…`, `0xa322…`, `0xf7c8…`).\n- **Aucun témoin positif de propriété commune :** la méthode n'a pas été éprouvée sur des paires connues, et elle a manqué deux liens réels en version 1. Son silence sur les 54 autres paires n'est pas une preuve d'absence.")
sub("Aucun wallet supplémentaire n'est relié aux onze par une preuve de chaîne.", "Pour ces trois wallets, aucun lien de chaîne n'a été cherché. Un wallet supplémentaire, lui, est relié aux onze par une preuve de chaîne : `0xa8e64a3c…f74a5`, section 4. D'autres adresses sont reliées aux clés, comme `7XUJs…` et `0x7e67…`, sans qu'on sache qui les tient.")
sub("- `Non surlignés`, `Même token`, `Token opposé` et `Comptes frais` sont des échantillons partiels pour le taux de base (voir section 4).", "- Taux de base : version 1 inutilisable, 48 wallets sur 78. Relecture de flow-trace sur 77 témoins, exploratoire, traits post hoc, un dépôt par wallet (section 4).")
sub("- Sorties natives non suivies : les 839 893,73 POL d'OuldLm3alem et les 26,97 ETH de 0xdd97e6. Destination des premiers non lue, solde des seconds non vérifié.", "- Sorties : les 26,97 ETH de 0xdd97e6 n'ont pas bougé (nonce 0). Les 839 000 POL d'OuldLm3alem sont devenus 75 946,74 USDT, puis, selon flow-trace, sont passés par deBridge, CCTP et Hyperliquid, avant que 73 001,19 USDC reviennent sur la même clé.")
sub("- Non lancés : les quatre audits indépendants à l'aveugle et les deux audits de conclusions du protocole d'étude gelée. Ce rapport n'a pas de relecture indépendante.", "- Relectures : un audit indépendant (`~/Projects/PolySentinel-audit-20261102/RAPPORT_AUDIT.md`) puis cette contre-vérification, puis un auditeur de conclusions, FAIL à ses deux passages, tous par des instances de Claude, avec les mêmes angles morts possibles. Sa dernière série de corrections n'a pas été relue une troisième fois, ni l'intégration des rapports de flow-trace. Aucune relecture humaine ni externe. Les audits du protocole d'étude gelée n'ont pas été faits sous leur forme prévue.\n- Tests de cette version sur les retraits et les achats rapprochés : exploratoires, écrits après lecture des données, hors registre gelé.\n- Amendement 001 de l'étude : décidé par Claude alors que la règle réserve les amendements à Benjamin, toujours à relire. Le fichier gelé n'est pas modifié.")

# Section 8
sub("**Confirmées :** H1, H2. **Réfutées, dans le périmètre indiqué :** H5, H6, H10. **Affaiblies :** H3, H4, H7, H8, H9, H11. **Non tranchées :** H12, H13, H14, H15.", "**Confirmées :** H1, H2, H16, H17. **Réfutées, dans le périmètre indiqué :** H5, H6. **Affaiblies :** H7, H8, H11. **Non soutenues :** H10, H12. **Non tranchées :** H3, H4, H9, H13, H14, H15.")
sub("Confirmée : les données la soutiennent directement. Affaiblie : testée, non soutenue, sans pouvoir l'exclure. Réfutée : contredite par les données, dans le périmètre indiqué. Non tranchée : indice faible, listes incomplètes, ou données publiques insuffisantes.", "Confirmée : les données la soutiennent directement. Affaiblie : testée, sans soutien, puissance non mesurée, sans pouvoir l'exclure. Non soutenue : rien de solide en sa faveur, sans preuve du contraire. Réfutée : contredite par les données, dans le périmètre indiqué. Non tranchée : la méthode ne pouvait pas répondre, listes incomplètes, ou données publiques insuffisantes. L'absence de preuve n'est jamais lue comme une preuve d'absence.")
sub("| H3 | Un même opérateur contrôle les onze | **AFFAIBLIE** | 11 clés distinctes, routes différentes, 0 transfert direct, 0 lien discriminant. Des comptes d'exchange restent invisibles : non exclue |", "| H3 | Un même opérateur contrôle les onze | **NON TRANCHÉE** | 11 clés distinctes et routes différentes : un opérateur prudent laisserait la même empreinte. Aucun témoin positif, comptes d'exchange invisibles. Rien ne la soutient, rien ne l'exclut |")
sub("| H4 | Un financeur personnel commun relie certains comptes | **AFFAIBLIE** | 21 paires naïves, 0 après reclassement. Hors des sauts lus, inconnu |", "| H4 | Un financeur personnel commun relie certains comptes | **NON TRANCHÉE entre les onze** | 21 paires naïves, 0 après reclassement. Le transfert de 5,53 $ pèse 0,055 % et 0,097 % des dépôts des deux comptes. Hors des onze, voir H17. Hors des sauts lus, inconnu |")
sub("| H7 | Des comptes frais se concentrent sur une issue plus que le hasard | **AFFAIBLIE** | Placebo p = 0,145 puis 0,298, 1 000 tirages |", "| H7 | Des comptes frais se concentrent sur une issue plus que le hasard | **AFFAIBLIE** | Placebo p = 0,145 puis 0,298, 1 000 tirages. Lecture sensible au choix du nul, section 5 |")
sub("| H8 | Les comptes nommés achètent de façon synchrone | **AFFAIBLIE** | 5 paires à 5 min sur 55, centile 95,5 non corrigé, mais centile 84,2 à 60 min et 9,8 sur la concentration en 24 h |", "| H8 | Les comptes nommés achètent de façon synchrone | **AFFAIBLIE** | 5 paires à 5 min sur 55, centile 95,5 non corrigé, mais centile 84,2 à 60 min et 9,8 sur la concentration en 24 h. Paire brace227 et kraben006 à instruire : 8 achats rapprochés le 24 oct., après l'article |")
sub("| H9 | Les nommés partagent des combinaisons inhabituelles | **AFFAIBLIE** | E4 v2 : 0 paire nommée sur 37 paires et trois graines |", "| H9 | Les nommés partagent des combinaisons inhabituelles | **NON TRANCHÉE** | E4 v2 : 0 paire nommée au-dessus du seuil, mais 19 paires sur 55 non testées et un seuil qui ne voit que l'extrême |")
sub("| H10 | Détenir le classement exact était rare | **RÉFUTÉE par rapport aux prix** | Combinaison cotée environ 0,28 avant l'article, marchés de rangs ouverts vers 0,6 |", "| H10 | Détenir le classement exact était rare | **NON SOUTENUE par rapport aux prix** | Combinaison cotée environ 0,28 avant l'article, marchés de rangs ouverts vers 0,6. Ce produit de prix suppose des rangs indépendants, ce qu'ils ne sont pas : le sens tient, « réfutée » était trop fort |")
sub("| H11 | Les comptes nommés ont eux-mêmes lancé la hausse de Kane | **AFFAIBLIE** | Hausse amorcée le 8 octobre : 24 444 $ d'achats, 0 $ de comptes nommés. Ils pèsent ensuite 25 à 53 % des achats du 9 au 11 |", "| H11 | Les comptes nommés ont eux-mêmes lancé la hausse de Kane | **AFFAIBLIE** | Hausse amorcée le 8 octobre : 24 444 $ d'achats, 0 $ de comptes nommés ce jour-là. Mais kraben006 achète 2 499 $ de Kane les 1er et 2 oct., Zoomman17 855 $ le 6, kraben006 243 $ le 7. Ils pèsent ensuite 25 à 53 % des achats du 9 au 11 |")
sub("| H12 | Une route KuCoin plus fréquente chez les nommés | **INDICE FAIBLE, non confirmée** | 3/11 contre 1/50, p ≈ 0,016 non corrigé, 0,093 face aux seuls comptes frais, étiquette à source unique |", "| H12 | Une route KuCoin plus fréquente chez les nommés | **NON SOUTENUE au seuil corrigé, indice faible** | Relecture de flow-trace : origine Solana 3/11 contre 6/68, p = 0,11. KuCoin 3/3 contre 1/6 parmi les origines Solana, p = 0,048, 9 wallets, non corrigé, seuil 0,0056. Étiquette à source unique. Le 3/11 contre 1/50 de la version 1 est retiré |")
sub("| H13 | Les fonds passent par ChangeNOW, FixedFloat ou XMR | **NON SOUTENUE** | Aucune interaction sur les sauts lus, listes incomplètes, deux chaînes s'arrêtent à un service non identifié |", "| H13 | Les fonds passent par ChangeNOW, FixedFloat ou XMR | **NON TRANCHÉE** | Deux adresses étiquetées ChangeNOW sur la clé de kraben006, source unique, dont 0,0024 ETH le 4 oct., et un financeur ancien de la clé de brace227 selon flow-trace. Petits montants. Aucun échange XMR observé, aucun mixeur lu, rien ne relie ces fonds à un pari. Listes incomplètes, deux chaînes s'arrêtent à un service non identifié. SwftSwap, service d'échange de la même famille, est utilisé par brace227 et kraben006 |")
sub("| H14 | Des retraits coordonnés | **NON DÉMONTRÉE** | Plusieurs retraits peu après la résolution, ce qu'impose le calendrier du marché. Aucun comparateur daté de cette fenêtre |", "| H14 | Des retraits coordonnés | **NON TRANCHÉE, non démontrée** | brace227 et kraben006 : aucun signal mesurable, 10 vendeurs comparables sur 20 retirent aussi vite. 0x86544e4dfde et walletwallet8424 : redemption en lot, mais retrait rapide atypique face au lot, p brut de 0,0002 à 0,0069 selon les 13 strates, de 0,010 à 0,38 après correction, exploratoire. 8 retraits principaux sur 11 suivent de moins de 10 min la dernière clôture. Selon flow-trace, aucune destination finale commune |")
sub("| H15 | Une information privilégiée | **NON TESTABLE ici** | Aucune preuve d'accès. Des données publiques seules ne peuvent pas trancher |", "| H15 | Une information privilégiée | **NON TESTABLE ici** | Aucune preuve d'accès. Des données publiques seules ne peuvent pas trancher, et aucun lien financier entre comptes n'y répond |\n| H16 | Un transfert direct relie deux dossiers | **CONFIRMÉE pour une paire** | 0,002048944 ETH de la clé de brace227 vers celle de kraben006. Lien entre clés, pas propriété commune |\n| H17 | Un wallet non nommé est relié aux onze par une preuve de chaîne | **CONFIRMÉE pour un wallet** | La clé de brace227 envoie 5 170 USDC à la clé de `0xa8e64a3c…f74a5`, qui dépose 5 165 $ et ne parie que sur Kane. Seul wallet actif parmi les adresses testées par flow-trace. Lien financier, pas propriété commune. Douzième compte allégué : aucune preuve |")

# Section 9
sub("- Aucun transfert de fonds direct entre ces dossiers, sur les chaînes et jetons lus.", "- Un seul transfert direct trouvé entre deux dossiers : 0,002048944 ETH, environ 5,53 $, de la clé de brace227 à celle de kraben006, le 4 oct. 13:54:35 UTC, `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`.\n- Ce transfert vide l'ETH de la clé de brace227, 108 s après un paiement Relay commandé depuis l'adresse Solana `7XUJs…frZc`, même identifiant sur les deux chaînes.\n- La clé de brace227 envoie 5 170 USDC à `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`, propriétaire du wallet non nommé `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5`, et 5 173,25 $ à son propre wallet, les 9 et 10 oct. Ce wallet ne parie que sur Kane.\n- Le 27 oct., les comptes détenteurs de Kane sont remboursés par un lot de 2 711 comptes en 136 transactions, moins d'une minute après la résolution. Le déclencheur n'est pas lu.")
sub("- 7 comptes soldés totalisent 129 367,79 $ de retraits moins dépôts.", "- 25 retraits pour 493 094,76 $ et 46 dépôts pour 304 137,63 $ sur les onze comptes. 7 comptes soldés totalisent 129 367,79 $ de retraits moins dépôts. Le premier montant est brut, le second un net partiel.")
sub("- Des comptes neufs convaincus, ou des suiveurs d'un mouvement de marché : la hausse de Kane du 8 au 11 octobre est large et ne dépend pas d'eux seuls.", "- Des comptes neufs convaincus, ou des suiveurs d'un mouvement de marché : la hausse de Kane du 8 au 11 octobre est large et ne dépend pas d'eux seuls.\n- Pour brace227 et kraben006 : un même opérateur, deux personnes qui se connaissent, ou un paiement sans rapport avec les paris. Aucune n'est établie (section 4).\n- Pour brace227 et `0xa8e64a3c…` : un même opérateur avec deux comptes, deux personnes qui misent à parts égales, ou un prêt. Aucune n'est établie (section 4).")
sub("- KuCoin plus fréquent chez les nommés (3/11 contre 1/50, non corrigé).\n- Le même service à 1 % pour VidenteRibeira et cookedrice, à un jour d'écart.", "- Financement commun de brace227 et `0xa8e64a3c…` : connexion démontrée, coordination seulement possible, limites en section 4.\n- Origine Solana puis KuCoin : 3/11 contre 6/68, p = 0,11, et 3/3 contre 1/6, très peu de lignes, non corrigé.\n- brace227 et kraben006, plus gros acheteurs taker de Kane du créneau du 24 oct., après l'article, avec des achats rapprochés (p = 0,40 dans ce créneau).\n- Retrait rapide après le lot Kane pour 0x86544e4dfde et walletwallet8424, et sortie rapide de la plupart des nommés : exploratoire, biais de sélection.\n- Même service à 1 % pour VidenteRibeira et cookedrice, à un jour d'écart. Le balayage vient de son automatisme, le choix commun reste sans explication ni valeur de lien démontrée.")
sub("- Qui contrôle ces wallets, et si plusieurs ont le même propriétaire.", "- Qui contrôle ces wallets, et si plusieurs ont le même propriétaire, brace227 et kraben006 compris.\n- Le taux de base au-delà d'une relecture exploratoire de 77 témoins.\n- Qui tient `0x48ec…`, si `0xa8e64a3c…` est le douzième compte allégué, et si d'autres wallets existent hors des formes testées.")
sub("- Ce qui sort de `GxjcMTWW…`, et l'identité de ce service.", "- Ce qui sort de `GxjcMTWW…`, et l'identité de ce service.\n- La nature exacte de `0x3f3Ee0a9…207B`, étiquette ChangeNOW à source unique, si un échange a eu lieu et ce qu'il aurait rendu.")
sub("### FAITS DÉMONTRÉS\n", "Trois niveaux à ne jamais confondre. **Connexion financière :** un transfert relie deux adresses. **Contrôle commun :** une même personne tient ces adresses. **Insider trading :** quelqu'un a parié en connaissant le résultat. Le premier est établi pour une paire des onze et entre brace227 et un wallet non nommé. Les deux autres ne sont établis pour personne, et le premier ne prouve pas les suivants.\n\n### FAITS DÉMONTRÉS\n")

# Section 10 et 11
sub("- **Trois workers réseau pendant moins de 2 minutes,**", "- **Erreurs de la version 1, corrigées après audit :** « 0 transfert direct » sur un scan sans natif, « aucun wallet supplémentaire relié » sans suivre ce que les clés envoient ailleurs, taux de base avec historiques coupés, lignes illisibles comptées comme négatives et doublons comptés comme non lus, E6 sur lignes coupées et doublonnées, H3, H4 et H9 lues comme affaiblies sans témoin positif, phrase trompeuse sur le sceau de la partie A. Détail : `reports/AMENDEMENT_AUDIT_2026-11-02.md`.\n- **Trois workers réseau pendant moins de 2 minutes,**")
sub("| `reports/liens_entre_wallets.md` | Reclassement et faux positifs |", "| `reports/AMENDEMENT_AUDIT_2026-11-02.md` | Chaque correction : ancienne affirmation, preuves, nouvelle conclusion, raison |\n| `reports/CONTRE_VERIFICATION.md` | Tableau des conclusions, vérification de l'audit, 17 historiques coupés |\n| `reports/JOURNAL_MODIFICATIONS_2026-11-02.md` | Empreintes avant et après de chaque fichier modifié |\n| `reports/POUR_FLOW_TRACE_2026-11-02.md` | Points échangés avec l'enquête flow-trace |\n| `~/Projects/PolySentinel-flow-trace/reports/` | Rapports finaux de cette enquête : origines, sorties, exposition, taux de base. Cités, non revérifiés sauf mention |\n| `archive/20261102_v2_avant_flow_trace/` | Version 2 de ces fichiers, avec leurs empreintes |\n| `evidence/contre_verification_20261102/`, `tools/cv_*.py` | Lectures et calculs de la contre-vérification |\n| `archive/20261102_avant_amendement_audit/` | Rapport, liens et dossiers `.md` de la version 1, avec leurs empreintes |\n| `reports/liens_entre_wallets.md` | Reclassement et faux positifs |")

# Accords hérités du gabarit de la version 1
text = re.sub(r'\b1 relations\b', '1 relation', text)
text = re.sub(r'\b1 issues\b', '1 issue', text)
# Contrôles du résultat
for bad in ("0 transfert de fonds entre dossiers", "Aucun transfert de fonds direct entre ces dossiers", "KuCoin ressort donc plus souvent", "Aucun p de cette étude", "le paiement natif ne laisse pas de log et", "partie A scellée avant la lecture", "comparateurs sur 42 font", "sur les chaînes et jetons lus", "**AFFAIBLIE** | 11 clés", "Aucun wallet supplémentaire n'est relié", "53 comparateurs", "en attente", "sur 83 prévus"):
    assert bad not in text, bad
for must in ("1 paire sur 55", "0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98", "0x30484595", "2 711 comptes", "81,4 %", "98,85 %", "129 367,79", "493 094,76", "48 ne l'étaient pas", "**NON TRANCHÉE** | 11 clés", "0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5", "5 173,25", "| H17 |"):
    assert must in text, must
assert text.count('—') == v1.decode().count('—'), 'cadratin ajouté'
v2 = text.encode()

# Extrait des liens, même découpe que tools/final_report.py
lines = text.split('\n')
i, j = lines.index('## 4. Liens de financement reclassés'), lines.index('## 5. Détection collective')
liens = '\n'.join(['# Liens entre les onze wallets', '', "Extrait de la version 2 du rapport final, corrigée après audit le 02/11/2026. Version 1 : `archive/20261102_avant_amendement_audit/liens_entre_wallets.md`. Un service commun ne relie personne, un transfert direct relie deux adresses, et aucune de ces lignes n'attribue deux wallets à un même propriétaire. Données : `graphs/links_classified.json`, `evidence/contre_verification_20261102/`.", ''] + lines[i + 1:j])

# Dossiers .md : la phrase de périmètre et un addendum
ADD = {
    'brace227': ["**Transfert direct vers kraben006 :** 2026-10-04 13:54:35 UTC, `0xc852b0938f5ad79b640d105ed11c14499454af26` envoie 0,002048943671205553 ETH, environ 5,53 $, à `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65`, `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`. Ni propriété commune, ni pari concerté, ni information privilégiée n'en découlent.", "Ce transfert vide l'ETH de la clé (98,85 % du solde envoyés), 108 s après 0,001692408 ETH payés via Relay depuis l'adresse Solana `7XUJsJBNp7WykVXG4y76ntsSn3H7tFdLVcmehAgJfrZc`.", "**Wallet non nommé financé par cette clé :** 2 210 USDC le 9 oct. et 2 960 USDC le 10 oct. vers `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`, propriétaire de `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5`, qui ne parie que sur Kane. Parts presque égales avec les 5 173,25 $ déposés sur ce wallet-ci. Ni propriété commune, ni information privilégiée n'en découlent.", "Nonce de 109 sur BSC. Selon flow-trace, dernière sortie BSC le 17 mai 2025 : « aucune sortie depuis avril 2025 » ne vaut que pour Ethereum. Entrées BSC non lues.", "Retrait principal 2,8 min après kraben006 : aucun signal mesurable, 10 vendeurs comparables sur 20 retirent aussi en moins de 5 min."],
    'kraben006': ["**Transfert direct depuis brace227 :** 2026-10-04 13:54:35 UTC, cette clé reçoit 0,002048943671205553 ETH, environ 5,53 $, de `0xc852b0938f5ad79b640d105ed11c14499454af26`, `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`. Ni propriété commune, ni pari concerté, ni information privilégiée n'en découlent.", "La clé détenait déjà 0,002007933 ETH. 9 h 54 min plus tard, elle envoie 0,00247406 ETH à `0x7e67dF45E0a0Bab092cbB2FF045f8AA8DFaB6E23`, qui les transfère à `0x3f3Ee0a9cAC2d01DB44001eca3E8382fbe40207B`, adresse à fort trafic sans étiquette. Seule une partie de ce montant suit forcément le transfert reçu.", "Retrait principal 2,8 min avant brace227 : aucun signal mesurable, 10 vendeurs comparables sur 20 retirent aussi en moins de 5 min."],
    '0x86544e4dfde': ["Redemption de Kane du 27 oct. 01:58:15 UTC : lot de 2 711 comptes, déclencheur non lu, faux positif comme lien. Redemptions partagées avec cookedrice : lots de 20 comptes, sans lien.", "Retrait 96 s après ce lot : rapide face aux autres comptes du lot, indice faible et exploratoire, qui ne prouve aucun lien.", "Candidat de 59,09 POL depuis `0xc590175e…`, repéré par l'audit : échange payé par `0x408ce42a…` lui-même, pas un transfert entre dossiers."],
    'walletwallet8424': ["Redemption de Kane du 27 oct. 01:58:15 UTC : lot de 2 711 comptes, déclencheur non lu, faux positif comme lien.", "Retrait 189 s après ce lot : rapide face aux autres comptes du lot, indice faible et exploratoire, qui ne prouve aucun lien.", "Candidat de 59,09 POL depuis `0xc590175e…` : ce contrat est mutualisé, il n'appartient pas à ce dossier."],
    'vidente': ["La sortie vers `GxjcMTWW…` est cosignée par ce service, 4 s après réception : `DMmDPF9s…` est probablement une adresse de dépôt du service. Le balayage semblable à cookedrice tient à cet automatisme.", "E4 : hors univers, aucun achat au 13 oct., puis un seul token à 100 $ ou plus au 23 oct., écarté par un filtre absent du plan. Le « 0 paire » ne dit rien de ce compte.", "Redemption partagée avec WenZhuanBuPei : lot de 20 comptes, sans lien."],
    'cookedrice': ["La sortie vers `GxjcMTWW…` est cosignée par ce service, 2 s après réception : `F7ew8r8X…` est probablement une adresse de dépôt du service. Le balayage semblable à VidenteRibeira tient à cet automatisme.", "Redemptions partagées avec 0x86544e4dfde : lots de 20 comptes, sans lien."],
    'wen': ["E4 : hors univers, aucun achat au 13 oct., puis un seul token à 100 $ ou plus au 23 oct., écarté par un filtre absent du plan. Le « 0 paire » ne dit rien de ce compte.", "Redemption partagée avec VidenteRibeira : lot de 20 comptes, sans lien."],
    'ouldlm3alem': ["Le retrait de 77 050,77 $ se lit sur la chaîne : `LogTransfer` de 839 893,73 POL vers la clé, log 463 de `0x909d9602…a6f1`. 108 s plus tard, 839 000 POL sont échangés contre 75 946,74 USDT, `0x8c358292…c2d3`. Selon flow-trace : deBridge, CCTP, Hyperliquid, puis 73 001,19 USDC revenus sur la clé, sur Arbitrum.", "`graphs/relations.jsonl` n'est pas modifié : la relation y reste classée SERVICE_INTERACTION."],
    '0xdd97e6': ["`0xca8B1f1a…6165` détient 26,9716 ETH, nonce 0, lu le 2 nov. : aucune sortie depuis la réception."],
    'thin': ["Le 13 oct., 15 053,97 $ sont achetés à 18:50:00 UTC, dont 14 743,44 $ en flux taker, 60 s avant la date D2 du plan, qui ne justifie pas cette heure."],
    'zoomman17': ["Retraits inférieurs aux dépôts : -2 849,19 $, résultat non affirmé, 4 positions à valeur nulle, 59 % des achats hors de la famille.", "Selon flow-trace : 6 893,00 USDC vers `0x8c5dc729…10fe`, balayés vers `0xf7c8da79…d921`, étiqueté Revolut 5."],
}
COMMUN = "E6 : le rang de financement publié sur 42 lignes contient des lignes coupées. Rang corrigé sur 20 comparateurs à historique complet : {z} font aussi court ou plus court. Le « KuCoin 3/11 contre 1/50 » est retiré : 48 comparateurs sur 78 étaient inutilisables. Relecture flow-trace : origine Solana 3/11 contre 6/68, p = 0,11, et financement sous 1 h 9/11 contre 32/39 comptes frais, rien de distinctif. Absence d'autre lien : sur un périmètre relu, non exhaustif, sans témoin positif de propriété commune."
cases_new = {}
for s, items in ADD.items():
    p = ROOT / f'cases/{s}.md'
    src = (ARC / f'cases/{s}.md').read_text()
    if s in ('brace227', 'kraben006'):
        src, n = re.subn(r"^- Transfert direct de fonds vers ou depuis un autre dossier : .*$", "- Transfert direct de fonds avec un autre dossier : **1 transfert ETH entre les clés de brace227 et kraben006**, voir l'addendum. La version 1 écrivait « aucun », sur un scan limité aux stablecoins et au pUSD.", src, flags=re.M)
    else:
        src, n = re.subn(r"^(- Transfert direct de fonds vers ou depuis un autre dossier : .*)$", r"\1 Périmètre élargi après audit : voir l'addendum.", src, flags=re.M)
    assert n == 1, s
    z = compl['E6_par_dossier'][s]['complets']
    cases_new[s] = src.rstrip('\n') + '\n\n## Addendum après audit, 02/11/2026\n\nCe dossier est celui du 2 nov. 08:18 UTC, conservé dans `archive/20261102_avant_amendement_audit/cases/`. Corrections : `reports/AMENDEMENT_AUDIT_2026-11-02.md`.\n\n' + '\n'.join(f'- {x}' for x in items + [COMMUN.format(z=z)]) + '\n'

if '--brouillon' in sys.argv:
    Path(sys.argv[sys.argv.index('--brouillon') + 1]).write_bytes(v2)

if '--ecrire' in sys.argv:
    now = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
    log = ['# Journal des modifications du 02/11/2026' if not (ROOT / 'reports/JOURNAL_MODIFICATIONS_2026-11-02.md').exists() else '## Passe suivante', '', f'Écrit par `tools/appliquer_amendement_20261102.py` à {now}. Rejouable : version 1 archivée plus ce script donnent la version 2. Corrections et raisons : `reports/AMENDEMENT_AUDIT_2026-11-02.md`.', '', 'Non modifiés : `collective/` (dont `results.md` et le plan gelé), `graphs/`, `controls/`, `evidence/` existant, `state/`, `cases/*.json`, `reports/inventaire_adresses.md`, `reports/iris_requetes.md`, `reports/proposition_shadow.md`, `reports/sources_cinq_depots.md`.', '', '| Fichier | sha256 avant | sha256 après |', '|---|---|---|']
    def write(path, new):
        before = path.read_bytes()
        path.write_text(new)
        log.append(f'| `{path.relative_to(ROOT)}` | `{sha(before)}` | `{sha(new.encode())}` |')
    write(ROOT / 'reports/rapport_final.md', v2.decode())
    write(ROOT / 'reports/liens_entre_wallets.md', liens)
    for s, new in sorted(cases_new.items()):
        write(ROOT / f'cases/{s}.md', new)
    log += ['', f'Remplacements dans `reports/rapport_final.md` : {len(done)}, dont la section du taux de base réécrite.', '', 'Avant toute modification : aucun écrivain détecté sur ces fichiers (`lsof`, `find -mmin`), session flow-trace prévenue. Copies : `archive/20261102_avant_amendement_audit/`, empreintes dans `SHA256SUMS`.', '']
    journal = ROOT / 'reports/JOURNAL_MODIFICATIONS_2026-11-02.md'
    ancien = journal.read_text().rstrip('\n') + '\n\n---\n\n' if journal.exists() else ''
    journal.write_text(ancien + '\n'.join(log))
    print('écrit', len(cases_new) + 2, 'fichiers')
print('remplacements', len(done), 'sha v2', sha(v2), 'lignes', text.count('\n'))
