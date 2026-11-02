"""The sentences of the reports. Tables come from the data; each figure quoted here is checked by tests/test_claims.py."""
import json
from collections import Counter, defaultdict

import net
import walk

STATE = net.ROOT / 'state'
SOLANA = walk.SOLANA
CHAIN = {1: 'ethereum', 137: 'polygon', 42161: 'arbitrum', 8453: 'base', 10: 'optimism', 56: 'bsc', SOLANA: 'solana'}
ORDER = ['thin', 'vidente', 'cookedrice', 'wen', '0x86544e4dfde', 'brace227', 'walletwallet8424', 'zoomman17', 'kraben006', 'ouldlm3alem', '0xdd97e6']
LEGEND = "Niveaux : **démontré** (lu sur la chaîne), **protocole** (identifiant d'un pont lu sur les deux chaînes ou enregistrement du protocole), **attribution** (flux démontré, nom du service selon une étiquette ou une mesure), **hypothèse** (compatible, non démontré), **inaccessible** (registre privé)."

FINAL_HEAD = "# Financement et sorties des 11 comptes du Ballon d'Or 2026\n\nEnquête historique, données lues le 2 novembre 2026. " + LEGEND

NOT_XMR = "Absente des données accessibles : aucune interaction avec un service proposant XMR sur ce chemin."

ABSENT = "Absente des données accessibles"
CASES = {
    'thin': dict(
        bref="Trois dépôts, deux plateformes. Le premier sort de KuCoin Hot Wallet 2 sur Solana, les deux autres de Binance Hot Wallet 6 sur BSC. Tout passe par Relay. Les retraits partent vers deux adresses Solana qui n'ont plus bougé : 79 537,63 USDC et 4,93 SOL y restent. Rien n'est sorti.",
        table=[
            ['Origine des financements', "45 679,23 $ en 3 dépôts : 11 833,23 $ par KuCoin Hot Wallet 2, 33 846,00 $ par Binance Hot Wallet 6", 'démontré pour les flux, attribution pour les noms'],
            ['Premier financeur identifiable', "`BmFdpraQhk…ymy6` (KuCoin Hot Wallet 2, Solana) et `0x8894e0a0…2d4e3` (Binance Hot Wallet 6, BSC)", 'attribution'],
            ['Dernier maillon avant dépôt', "Adresse de pont `0x8e43af99…9865`, payée par le solveur Relay", 'démontré, protocole'],
            ['Services', "KuCoin, Binance, Relay", 'attribution, protocole'],
            ['XMR', ABSENT, 'aucun indice'],
            ['Retraits', "80 037,93 $ vers `CXVYMP5q…GrfJ` et `EnHRjTP4…PZ8B` (Solana)", 'protocole'],
            ['Où la trace devient incertaine', "En amont, dans les comptes des deux plateformes. Aucune sortie en aval.", 'inaccessible'],
        ],
        chemins=["Qui a approvisionné les comptes KuCoin et Binance : registres privés. La clé `0x1bf0b469…6028` n'a aucun flux lu sur Ethereum, Polygon, Arbitrum et Optimism, et un nonce de 0 sur les six chaînes testées."],
        confiance="Flux : haute. Noms : moyenne : KuCoin repose sur Orb seul, Binance sur deux sources publiques (liste de 2023 et Blockscout). Alternatives : deux personnes différentes derrière ces comptes de plateforme, ou un intermédiaire qui retire pour autrui."),
    'vidente': dict(
        bref="Deux dépôts depuis KuCoin Hot Wallet 2, par une adresse Solana de passage, puis Relay. Le retrait de 51 509,88 $ arrive en USDT sur une adresse de dépôt d'un service dépositaire non identifié, qui le balaie 4 secondes plus tard avec sa propre signature. La trace s'arrête là.",
        table=[
            ['Origine des financements', "28 029,96 $ en 2 dépôts, tous deux par KuCoin Hot Wallet 2", 'démontré pour les flux, attribution pour le nom'],
            ['Premier financeur identifiable', "`BmFdpraQhk…ymy6` (KuCoin Hot Wallet 2)", 'attribution'],
            ['Dernier maillon avant dépôt', "`5xHWduZu…uz1a` (Solana) puis Relay, puis `0x6d24d945…6df8`", 'démontré, protocole'],
            ['Services', "KuCoin, Relay, `GxjcMTWW…nvBW` (service non identifié)", 'attribution, protocole, mesure'],
            ['XMR', ABSENT + " : la trace s'arrête à un service non identifié, ce qui n'est pas un indice", 'aucun indice'],
            ['Retraits', "51 509,88 $ devenus 51 489,09 USDT sur `DMmDPF9s…1wt5T`, puis 51 489,00 USDT vers `GxjcMTWW…nvBW`", 'protocole, démontré'],
            ['Où la trace devient incertaine', "À l'entrée de `GxjcMTWW…nvBW` : ce service mêle ses clients", 'inaccessible'],
        ],
        chemins=["Sortie de `GxjcMTWW…nvBW` : dans les 6 h suivant le balayage, 128 destinataires sur 260 transactions tirées, aucun ne reçoit un total proche de 99 à 101 % du montant. Il faudrait le registre du service."],
        confiance="Flux : haute. Le balayage cosigné désigne une adresse de dépôt tenue par le service. Alternatives : plateforme, service de paiement ou échange : aucune étiquette ne permet de choisir."),
    'cookedrice': dict(
        bref="Un seul dépôt depuis KuCoin Hot Wallet 2, par une adresse Solana de passage. Le retrait de 39 158,78 $ part vers une adresse de dépôt du même service dépositaire non identifié que VidenteRibeira. Ce service est mutualisé, ce n'est pas un lien entre les deux comptes.",
        table=[
            ['Origine des financements', "21 873,74 $, par KuCoin Hot Wallet 2", 'démontré pour le flux, attribution pour le nom'],
            ['Premier financeur identifiable', "`BmFdpraQhk…ymy6` (KuCoin Hot Wallet 2)", 'attribution'],
            ['Dernier maillon avant dépôt', "`BJcZxhXF…JJxFU` (Solana) puis Relay, puis `0xd628c333…5c58`", 'démontré, protocole'],
            ['Services', "KuCoin, Relay, `GxjcMTWW…nvBW`", 'attribution, protocole, mesure'],
            ['XMR', ABSENT + " : même remarque que VidenteRibeira", 'aucun indice'],
            ['Retraits', "39 158,78 $ devenus 39 158,63 USDC sur `F7ew8r8X…Nh5Eh`, puis 39 158,00 USDC vers `GxjcMTWW…nvBW`", 'protocole, démontré'],
            ['Où la trace devient incertaine', "À l'entrée de `GxjcMTWW…nvBW`", 'inaccessible'],
        ],
        chemins=["Sortie de `GxjcMTWW…nvBW` : 126 destinataires sur 260 transactions tirées dans les 6 h, aucun total proche du montant."],
        confiance="Flux : haute. Alternatives : voir VidenteRibeira. Les deux comptes passent par le même service à un jour d'écart : `GxjcMTWW…nvBW` traite environ 90 à 95 transactions par heure sur les fenêtres lues, ce rapprochement n'a pas de valeur de lien."),
    'wen': dict(
        bref="Un dépôt de 15 926,88 $, payé sur Polygon par `0xee7ae85f…4055`, étiqueté Binance: Hot Wallet 34 sur Blockscout, dans une transaction envoyée par une adresse étiquetée Binance dans deux sources. Le retrait va sur Arbitrum, puis vers un intermédiaire à commission de 1,00 %, qui répartit le reste en trois morceaux. Ces trois morceaux sont regroupés 18 h plus tard par une adresse de service à 62 528 transactions.",
        table=[
            ['Origine des financements', "15 926,88 $ depuis `0xee7ae85f…4055` (Binance: Hot Wallet 34), transaction envoyée par `0xe7804c37…e245` (Binance 48, et Binance: Hot Wallet 2 dans une liste de 2023)", 'démontré pour le flux, attribution pour le nom'],
            ['Premier financeur identifiable', "Binance, sur le payeur et sur l'expéditeur de la transaction", 'attribution'],
            ['Dernier maillon avant dépôt', "`0x315ac6e7…14c5` (adresse de pont), Relay", 'démontré, protocole'],
            ['Services', "Binance, Relay, `0x3ab2206b…7d50` (intermédiaire), `0x51cf2d9f…4999` (service)", 'protocole, attribution, mesure'],
            ['XMR', ABSENT + " : l'intermédiaire à 1 % est non identifié, aucun indice de conversion", 'aucun indice'],
            ['Retraits', "27 724,79 $ vers `0xe820ecb3…87cd` (Arbitrum), 27 724,00 USDC vers `0x3ab2206b…7d50`", 'protocole, démontré'],
            ['Où la trace devient incertaine', "À `0x51cf2d9f…4999`, qui reçoit 3 037 expéditeurs et paie 1 630 destinataires", 'inaccessible'],
        ],
        chemins=["Après `0x51cf2d9f…4999` : le service mêle ses clients, et son historique lu est tronqué au milieu. Il faudrait son registre."],
        confiance="Flux : haute jusqu'à `0x51cf2d9f…4999`, y compris les trois morceaux regroupés dans une seule transaction (`0x6ef3a7e7…1547`), ce qui prouve un contrôle commun de ces trois adresses par le service. Le mot « commission » décrit une mesure, pas un contrat : 277,24 USDC vont à `0x435e3931…dd1d` dans la seconde qui suit, exactement 1,00 %. Alternatives : gestionnaire de paiement, courtier de gré à gré, service de sortie de fonds. Aucune étiquette."),
    '0x86544e4dfde': dict(
        bref="Plus gros compte du groupe : 44 847,24 $ déposés en 4 fois. Trois dépôts viennent d'un compte intelligent Circle d'un service dépositaire non attribué, sur Polygon. Le quatrième vient d'un vieux portefeuille personnel, `0x408ce42a…c5b3`, alimenté de 2023 à 2024 par Kraken et Binance. Les 74 198,32 $ retirés sont intacts sur la clé, qui n'a jamais signé une seule transaction sur Ethereum.",
        table=[
            ['Origine des financements', "42 389,48 $ par `0x0ce9bdf3…f06d`, 2 457,76 $ par `0x408ce42a…c5b3`", 'démontré pour les flux'],
            ['Premier financeur identifiable', "Service non attribué `0x0ce9bdf3…f06d`. Pour la branche `0x408ce42a…c5b3` : Kraken 4 et Binance 14, 15 et 18, de 2023 à 2024", 'mesure ; attribution'],
            ['Dernier maillon avant dépôt', "Clé `0x69837228…0ded` et `0x99a5baa3…22be` (adresse de pont), Relay", 'démontré, protocole'],
            ['Services', "Service Circle non attribué, Relay, Polygon PoS, MetaMask, UniswapX ; Kraken et Binance dans l'historique de `0x408ce42a…c5b3`", 'mesure, protocole, attribution'],
            ['XMR', ABSENT, 'aucun indice'],
            ['Retraits', "74 198,32 $ vers la clé sur Ethereum", 'protocole'],
            ['Où la trace devient incertaine', "En amont de `0x0ce9bdf3…f06d`, et rien en aval : 74 198,32 USDC encore en place", 'inaccessible'],
        ],
        chemins=["Le service derrière `0x0ce9bdf3…f06d` : 1 001 destinataires sur 2 000 lignes en 84 h, expéditeur `0x0853ea40…4d0b` (nonce 407 684) sans étiquette."],
        confiance="Flux : haute. `0x408ce42a…c5b3` n'a envoyé que 2 457,76 $ : le lien entre lui et le titulaire de la clé reste une hypothèse. Alternatives : un proche ou un autre compte du même titulaire. Le compte a touché 15,86 $ de primes de parrainage, ce qui explique son résidu."),
    'brace227': dict(
        bref="La clé reçoit 15 096,29 $ de SwftSwap, service d'échange instantané, et en partage la moitié avec une autre clé, `0x48ec106c…b12d`, qui possède un **autre wallet Polymarket**. Ce wallet n'a acheté que du Kane Oui. C'est le seul compte supplémentaire relié aux onze par la chaîne, et le fait le plus discriminant de cette enquête. La clé envoie aussi 0,00205 ETH à la clé de kraben006. Ses retraits restent sur la clé : 22 024,57 USDC.",
        table=[
            ['Origine des financements', "SwftSwap 15 096,29 $ en 4 versements du 9 au 16 oct., BloFin (Hot Wallet 1) 110,20 $. Gaz : `7XUJsJBN…JfrZc` (Solana) par Relay", 'démontré, attribution pour les noms'],
            ['Premier financeur identifiable', "SwftSwap pour la période des paris. Plus ancien : KuCoin 10 et Binance 20 en mars 2022. `0x3eaef6d5…`, financé entièrement par ChangeNOW (Hot Wallet 3 et 4), envoie 291,32 USDT en janv. 2025", 'attribution'],
            ['Dernier maillon avant dépôt', "La clé `0xc852b093…af26`, Relay, `0xc8a6871d…8d64`", 'démontré, protocole'],
            ['Services', "SwftSwap, BloFin, Relay, THORChain (7 USDC), NEAR Intents (5 USDC contre du gaz), MetaMask ; ChangeNOW fin 2024 sur un financeur ancien", 'nom vérifié, attribution, protocole'],
            ['XMR', ABSENT + " : SwftSwap ne liste pas XMR à la lecture ; ChangeNOW le liste, et finance fin 2024 l'adresse qui envoie 291,32 USDT à la clé : simple compatibilité, 21 mois avant les paris", 'aucun indice'],
            ['Retraits', "22 036,76 $ vers la clé. 22 024,57 USDC y restent", 'protocole'],
            ['Où la trace devient incertaine', "Derrière SwftSwap : l'actif d'origine et le client de chaque ordre ne sont pas publics", 'inaccessible'],
        ],
        chemins=["Origine des 15 096,29 $ : SwftSwap paie par `withdraw` depuis son contrat. Sa route d'état d'ordre exige un identifiant d'ordre que la chaîne ne donne pas.", "BSC : 109 transactions signées, 104 avant le 30 juil. 2022 et non énumérées une à une, 5 lues : la dernière date du 17 mai 2025. Entrées BSC non lues."],
        confiance="Le partage et le second wallet : haute, voir `COMMON_FUNDERS.md`. Ils démontrent un lien financier, pas un propriétaire commun : don, prêt, ou ami à qui on avance les fonds restent possibles. Rien sur une information privilégiée."),
    'walletwallet8424': dict(
        bref="Trois dépôts. Deux viennent du même service Circle non attribué que 0x86544e4dfde. Le gros, 16 508,26 $, suit un chemin long mais démontré : 16 808,96 USDC d'une adresse très active, échangés en 6,63 ETH, passés sur Polygon par le pont officiel, puis ré-échangés en USDC. Les 35 546,89 $ retirés sont intacts sur la clé.",
        table=[
            ['Origine des financements', "`0xcc0f311e…23f7` 16 808,96 USDC ; `0x0ce9bdf3…f06d` 1 674,43 et 3 907,03 USDC", 'démontré pour les flux'],
            ['Premier financeur identifiable', "`0xcc0f311e…23f7`, sans étiquette, 672 contreparties, et parmi ses entrées Stake.com et CoinsPaid", 'mesure'],
            ['Dernier maillon avant dépôt', "La clé `0x82775eb8…a3a1`, Relay, `0xc8a6871d…8d64`", 'démontré, protocole'],
            ['Services', "Service Circle non attribué, MetaMask (échange et gaz), pont Polygon PoS, `0xc590175e…c02b`, Relay", 'mesure, attribution, protocole'],
            ['XMR', ABSENT, 'aucun indice'],
            ['Retraits', "35 546,89 $ vers la clé sur Ethereum", 'protocole'],
            ['Où la trace devient incertaine', "En amont de `0xcc0f311e…23f7`. Rien en aval : les fonds sont en place", 'inaccessible'],
        ],
        chemins=["`0xcc0f311e…23f7` : 672 contreparties, historique lu aux deux bouts seulement. Aucune entrée d'au moins 1 USDC dans les 36 h autour du paiement, sur les lignes lues : il paie sur son stock."],
        confiance="Flux : haute. Le passage en ETH puis retour en USDC ressemble à un chemin choisi par l'interface MetaMask, rien n'indique une volonté de brouiller. Alternatives pour `0xcc0f311e…23f7` : gré à gré, paiement, salaire, gain de jeu."),
    'zoomman17': dict(
        bref="Seul compte perdant du groupe. L'argent vient d'adresses étiquetées Revolut, de Chainflip et d'un service dépositaire non attribué. Les retraits repartent par `0x8c5dc729…10fe`, adresse à une seule sortie, vers `0xf7c8da79…d921`, étiquetée Revolut 5 : c'est le profil d'une adresse de dépôt chez Revolut. L'argent semble être revenu d'où il venait.",
        table=[
            ['Origine des financements', "Chainflip 1 5 439,33 $, Revolut 1 3 227,76 $ sur 7 versements, `0x58f298e3…0214` 867,98 $ ; 0,11 ETH par `0x09c30cdc…` (Revolut 6)", 'démontré pour les flux, attribution pour les noms'],
            ['Premier financeur identifiable', "Revolut 1 et Chainflip 1, chacune dans deux sources publiques", 'attribution'],
            ['Dernier maillon avant dépôt', "La clé `0xd90d0013…f444`, Relay, `0xc8a6871d…8d64`", 'démontré, protocole'],
            ['Services', "Revolut, Chainflip, `0x58f298e3…0214`, MetaMask, Relay", 'attribution, mesure, protocole'],
            ['XMR', ABSENT, 'aucun indice'],
            ['Retraits', "6 894,00 $ vers la clé, dont 6 893,00 USDC en 4 envois vers `0x8c5dc729…10fe`, balayés vers `0xf7c8da79…d921` (Revolut 5)", 'protocole, démontré, attribution'],
            ['Où la trace devient incertaine', "À `0xf7c8da79…d921`", 'inaccessible'],
        ],
        chemins=["L'actif d'origine avant Chainflip : registre du protocole non lu. `0xf7c8da79…d921` : étiquette Revolut 5 sur Blockscout seule, confortée par 27 lignes avec Revolut 1."],
        confiance="Flux : haute. « Dépôt chez Revolut » repose sur le profil (adresse à nonce 1, un seul balayage) et sur une étiquette à source unique. Les retraits moins dépôts donnent une perte de 2 849,19 $."),
    'kraben006': dict(
        bref="Beaucoup de petits dépôts, 14 pour 5 689,47 $, et une source principale : quatre portefeuilles de paiement à fort trafic, dont trois rechargés par la même trésorerie. S'y ajoutent 188,97 $ de SwftSwap. Plus tôt dans l'année, la clé a reçu de Deblock et de ChangeNOW. Le 4 octobre, elle reçoit 0,00205 ETH de la clé de brace227 et envoie 0,00247 ETH vers une adresse de dépôt de ChangeNOW. Les retraits restent sur la clé : 15 154,83 USDC.",
        table=[
            ['Origine des financements', "`0x58f298e3…0214`, `0xbd1f4462…eb3b`, `0x0c58909d…270d`, `0x7bef1627…5c24`, SwftSwap 188,97 $. Plus tôt en 2026, `0xdd3d72c5…` (ChangeNOW: Hot Wallet 3) et `0xb43c1981…` (Deblock: Wallet 1) : au PEPS, ces fonds sont sortis avant les dépôts de la période", 'démontré pour les flux, mesure'],
            ['Premier financeur identifiable', "Service dépositaire non attribué. Ces portefeuilles reçoivent de l'ETH de Kraken: Hot Wallet 2 pour leur gaz, ce qui ne suffit pas à en faire Kraken", 'mesure'],
            ['Dernier maillon avant dépôt', "La clé `0x101b5f4d…fb65`, Relay, `0xc8a6871d…8d64`", 'démontré, protocole'],
            ['Services', "Service non attribué, SwftSwap, ChangeNOW, Deblock, Across (49,18 USDC en fév. 2026), Relay", 'mesure, nom vérifié, attribution, protocole'],
            ['XMR', ABSENT + " : la clé touche ChangeNOW, qui liste XMR, mais rien ne dit quel actif était en face. Simple compatibilité", 'aucun indice'],
            ['Retraits', "15 593,54 $ vers la clé. 15 154,83 USDC y restent", 'protocole'],
            ['Où la trace devient incertaine', "En amont du service non attribué. En aval, seule sortie non Relay : 0,00247 ETH vers `0x7e67df45…6e23`, balayés vers `0x3f3ee0a9…207b` (ChangeNOW Dep)", 'inaccessible'],
        ],
        chemins=["`0x7e67df45…6e23` : 2 transactions, reçoit 0,00247 ETH et renvoie 0,00241 ETH 8 minutes plus tard vers `0x3f3ee0a9…207b`, étiqueté ChangeNOW Dep sur Blockscout : profil d'une adresse de dépôt ChangeNOW. Ce que la clé a reçu en échange, et où, n'est pas public."],
        confiance="Flux : haute. Le lien avec brace227 porte sur 0,00205 ETH, environ 5,5 $, soit moins de 0,1 % des dépôts : c'est un lien entre deux clés, pas un financement. Il est instruit dans `COMMON_FUNDERS.md`."),
    'ouldlm3alem': dict(
        bref="Trois dépôts, chacun par une route différente : un contrat de paiement à fort trafic sur Ethereum, KuCoin Hot Wallet 2 sur Solana, une adresse étiquetée Binance sur Arbitrum. Le retrait principal, 77 050,77 $, a été converti en POL, puis en USDT, puis passé sur Arbitrum, puis sur Hyperliquid, où il a servi à trader. 73 001,19 USDC sont revenus sur la clé et y restent.",
        table=[
            ['Origine des financements', "`0xa3222357…59b3` 23 386,26 $, KuCoin Hot Wallet 2 16 798,01 $, `0xee7ae85f…4055` 15 982,84 $", 'démontré pour les flux, attribution pour les noms'],
            ['Premier financeur identifiable', "KuCoin Hot Wallet 2 ; `0xee7ae85f…4055` (Binance: Hot Wallet 34) ; `0xa3222357…59b3` non attribué, 721 destinataires en 20 h, expéditeur `0x963737c5…ef9a` étiqueté Union Chain", 'attribution, mesure'],
            ['Dernier maillon avant dépôt', "`0xb3afcdc7…b0ba` (adresse de pont), Relay", 'démontré, protocole'],
            ['Services', "KuCoin, Binance, Relay, Uniswap, deBridge, CCTP, Hyperliquid", 'attribution, protocole'],
            ['XMR', ABSENT, 'aucun indice'],
            ['Retraits', "77 250,77 $ : 77 050,77 $ devenus 839 893,73 POL sur la clé ; 200,00 $ devenus 0,1333 BNB et 99,80 USDT sur `0xae232f78…c026` (BSC)", 'protocole'],
            ['Où la trace devient incertaine', "En amont seulement. Tout le reste est lu jusqu'au solde final", 'inaccessible'],
        ],
        chemins=["Le burn de pUSD du retrait `0x909d9602…a6f1` n'est pas une destination : la destination est la clé, payée en POL natif dans la même transaction."],
        confiance="Flux : haute, chaque saut est porté par un identifiant de protocole. Hyperliquid se réconcilie à 0,02 $ près : 75 724,54 $ reçus, 2 415,41 $ de pertes réalisées et 306,71 $ de frais sur 303 exécutions du contrat perpétuel HYPE, 73 002,40 $ repartis. Ce n'est pas une sortie déguisée. Un mouvement de 0,20 pUSD d'un autre wallet, absent de l'API, ressemble à un pourboire, non vérifié."),
    '0xdd97e6': dict(
        bref="Deux dépôts : 19 760,16 $ depuis un portefeuille BSC à fort trafic non étiqueté, 24 299,00 $ depuis KuCoin Hot Wallet 2. Le retrait de 63 143,10 $ a été converti en 26,97 ETH et n'a pas bougé. L'adresse de destination n'a signé aucune transaction.",
        table=[
            ['Origine des financements', "`0x6bf18baf…7e95` 19 760,16 $ (BSC), KuCoin Hot Wallet 2 24 299,00 $ (Solana)", 'démontré pour les flux'],
            ['Premier financeur identifiable', "KuCoin Hot Wallet 2. `0x6bf18baf…7e95` : nonce 966 093, sans étiquette", 'attribution, mesure'],
            ['Dernier maillon avant dépôt', "`0x22cec127…2e76` (adresse de pont), Relay", 'démontré, protocole'],
            ['Services', "KuCoin, service BSC non attribué, Relay", 'attribution, mesure, protocole'],
            ['XMR', ABSENT, 'aucun indice'],
            ['Retraits', "63 143,10 $ devenus 26,97 ETH sur `0xca8b1f1a…6165`", 'protocole'],
            ['Où la trace devient incertaine', "En amont seulement. Lien avec le wallet : préfixe de presse de six caractères, unique, non certifié", 'inaccessible'],
        ],
        chemins=["Le lien entre l'étiquette de presse et ce wallet reste au niveau de l'inventaire de l'enquête d'origine."],
        confiance="Flux : haute. Alternatives : deux clients de plateforme distincts, ou le même : on ne peut pas trancher."),
}

COMPARE = {
    'thin': ["KuCoin (Solana), Binance (BSC)", "Relay, adresse de pont", "2 adresses Solana", "Non : 79 537,63 USDC en place", ABSENT, "Comptes de plateforme, en amont"],
    'vidente': ["KuCoin (Solana)", "Relay, adresse de pont", "Dépôt chez `GxjcMTWW…nvBW`", "Oui, balayé en 4 s", ABSENT, "Service non identifié, en aval"],
    'cookedrice': ["KuCoin (Solana)", "Relay, adresse de pont", "Dépôt chez `GxjcMTWW…nvBW`", "Oui, balayé en 2 s", ABSENT, "Service non identifié, en aval"],
    'wen': ["Binance (Polygon)", "Relay, adresse de pont", "Intermédiaire à 1 %, puis service", "Oui", ABSENT, "`0x51cf2d9f…4999`, en aval"],
    '0x86544e4dfde': ["Service Circle non attribué ; portefeuille ancien", "Relay, interface et adresse de pont", "Clé, Ethereum", "Non : 74 198,32 USDC en place", ABSENT, "Service non attribué, en amont"],
    'brace227': ["SwftSwap, BloFin", "Relay, interface", "Clé, Ethereum", "Non : 22 024,57 USDC en place", ABSENT, "SwftSwap, en amont"],
    'walletwallet8424': ["Adresse active non étiquetée ; service Circle", "Relay, interface", "Clé, Ethereum", "Non : 35 546,89 USDC en place", ABSENT, "`0xcc0f311e…23f7`, en amont"],
    'zoomman17': ["Revolut, Chainflip", "Relay, interface", "Adresse de dépôt, puis Revolut 5", "Oui", ABSENT, "Revolut, en aval ; Chainflip, en amont"],
    'kraben006': ["Portefeuilles de paiement non attribués", "Relay, interface", "Clé, Ethereum", "Non : 15 154,83 USDC en place", ABSENT, "Service non attribué, en amont"],
    'ouldlm3alem': ["KuCoin, Binance, contrat non attribué", "Relay, adresse de pont", "Clé, puis Hyperliquid, retour", "Revenu : 73 001,19 USDC sur Arbitrum", ABSENT, "En amont seulement"],
    '0xdd97e6': ["KuCoin ; service BSC non attribué", "Relay, adresse de pont", "`0xca8b1f1a…6165`", "Non : 26,97 ETH en place", ABSENT, "En amont seulement"],
}

RESULT = """**Relay est le seul service commun aux onze comptes.** Aucune source personnelle commune n'apparaît à l'échelle du groupe. L'argent sort presque partout de plateformes ou de services dépositaires, puis traverse Relay, qui met fin à la lecture directe entre chaînes mais laisse un identifiant vérifiable.

1. **D'où vient l'argent ?** Les 304 137,63 $ de dépôts remontent à des plateformes étiquetées pour plus de la moitié : KuCoin Hot Wallet 2 sur Solana pour 5 comptes et 102 833,93 $, des adresses étiquetées Binance pour 3 comptes et 65 755,73 $, plus Revolut et BloFin. Le reste vient de services non attribués, de SwftSwap et de Chainflip. Une seule branche remonte à un portefeuille personnel ancien : `0x408ce42a…c5b3`, pour 2 457,76 $.
2. **Exchange, pont, mixeur, Monero ?** Relay sur les 46 dépôts et sur 24 des 25 retraits, le 25e étant un échange Relay sur la même chaîne. **Aucune interaction lue avec Tornado Cash, Railgun ou un autre mixeur étiqueté. Aucun indice de Monero.** Cela ne l'exclut pas derrière les comptes de plateforme et les services non identifiés.
3. **Où est allé l'argent ?** Sur 493 094,76 $ retirés, **environ 74 % n'avaient pas quitté leur première adresse ou y étaient revenus le 2 novembre** : 299 565,17 $ en stablecoins et 26,97 ETH sur 7 comptes. Trois comptes ont déposé chez des services non identifiés, soit 118 371,00 $ ; Zoomman17 a envoyé 6 893,00 USDC vers une adresse de dépôt balayée par Revolut 5. **Aucune destination finale commune.**
4. **Financeurs ou destinations communs ?** **Un lien fort, et il est nouveau.** La clé de brace227 finance à 100 % une autre clé, qui possède un wallet Polymarket non nommé par la presse à ma connaissance, `0xa8e64a3c…74a5`. Ce wallet n'a acheté que du Kane Oui, et le partage se fait à parts presque égales avec brace227. La même clé envoie aussi 0,00205 ETH à la clé de kraben006. Aucune autre paire n'a de lien direct ni d'adresse personnelle partagée.

**Ce que cela ne démontre pas.** Ni propriétaire commun, ni coordination, ni information privilégiée. Une origine commune n'est pas un délit d'initié. La presse a choisi ces comptes après coup, ce qui biaise toute comparaison."""

MATRIX_READING = """**La seule paire avec un lien direct est brace227 et kraben006.** Les « s » sont des services communs (Relay, KuCoin, MetaMask, SwftSwap, ChangeNOW…) et ne relient personne. Le wallet `0xa8e64a3c…74a5` n'est pas dans cette matrice : il n'est pas un des onze, il est relié à brace227 seul."""

LIMITS = """- **Chaînes :** BSC et Base n'ont pas d'historique gratuit. Sur BSC : reçus connus, nonces et soldes ; pour la clé de brace227, 5 sorties récentes par dichotomie du nonce. Les entrées BSC et Base ne sont pas lues.
- **Natif :** lu sur Ethereum, Polygon, Arbitrum et Optimism. Solana : 60 transactions au plus par adresse.
- **Étiquettes :** trois sources publiques : deux listes, dont une datée de 2023, et les tags de Blockscout, lus sur Ethereum et Optimism pour les 73 adresses de services rencontrées. KuCoin Hot Wallet 2 : Orb seul. Une étiquette dit ce qu'une source a écrit, et aucune n'identifie un client.
- **Service absent des listes :** un exchange ou un mixeur récent peut ne pas y être. « Aucune interaction » veut dire aucune interaction avec une adresse connue, sur les historiques lus. Les adresses de dépôt de plateforme sont souvent éphémères et sans étiquette.
- **Budgets :** 4 sauts et 45 nœuds par sens et par dossier, au-dessus de 400 contreparties une adresse est traitée en hub. Aucun budget n'a été atteint ici, sauf le hub `0xcc0f311e…23f7`, dont l'historique est lu aux deux bouts.
- **PEPS :** la répartition entre entrées mêlées est une convention comptable.
- **Témoins :** échantillon partiel, traits choisis après coup, un seul témoin positif de lien direct.
- **Lien étiquette vers adresse :** niveaux inégaux, repris de l'inventaire de l'enquête d'origine.
- **Relecture :** faite par une session Claude parallèle, qui a relu le wallet `0xa8e64a3c…74a5` sur la chaîne. Même famille de modèle, pas un audit indépendant au sens fort."""

COMMON_ANSWER = """**Un seul groupe de comptes est relié par la chaîne : brace227, le wallet non nommé `0xa8e64a3c…74a5`, et dans une moindre mesure kraben006.** Sur les 55 paires des onze comptes, 1 a un transfert direct. Les autres n'ont en commun que des services nommés ou des hubs mesurés.

Cela corrige « 0 lien discriminant » de l'enquête d'origine et complète l'audit, qui avait trouvé le transfert vers kraben006 mais pas le second wallet."""

BRACE_KRABEN = """### Le financement du wallet `0xa8e64a3c…74a5` par la clé de brace227

**Démontré par la chaîne :**

| UTC | Fait | Transaction |
|---|---|---|
| 10-08 10:13:20 | Wallet `0xa8e64a3c…74a5` créé par la fabrique Polymarket, propriétaire `0x48ec106c…b12d` (`owner()` lu, adresse recalculée) | `0xa6e22997…5d7b` |
| 10-09 20:03:47 et 20:06:35 | SwftSwap paie 4 337,52 et 83,89 USDC à la clé de brace227 | `0xead283d8…2f3f`, `0xb193c0e9…` |
| 10-09 20:28:35 | La clé envoie **2 210,00 USDC** à `0x48ec106c…b12d` : sa première entrée | `0x7e3aecb9…` |
| 10-09 20:36:28 | Dépôt de 2 200,00 $ sur `0xa8e64a3c…74a5` | `0x3cd7757a…` |
| 10-09 20:37:10 | Premier achat de ce wallet, sur Kane Oui | |
| 10-09 20:48:59 | La clé dépose 2 186,43 $ sur le wallet de brace227 | `0xdade8977…` |
| 10-10 00:26:47 | SwftSwap paie 5 925,84 USDC à la clé | `0x492e2f05…` |
| 10-10 00:51:11 | La clé envoie **2 960,00 USDC** à `0x48ec106c…b12d` | `0xb07c3c53…` |
| 10-10 10:48:04 | Dépôt de 2 965,00 $ sur `0xa8e64a3c…74a5` | `0xdcf9e178…` |
| 10-27 01:58:20 | Redemption de 8 061,89 $ sur `0xa8e64a3c…74a5`, marché Kane | `0xe33c61e7…` |
| 10-27 18:49:06 | Retrait de 8 061,90 $ vers `0x48ec106c…b12d`, qui détient encore 5 062,18 USDC et a échangé 3 000 USDC contre 2 969,57 mUSD le 29 oct. | `0x09d05d70…` |

- **Exclusif.** L'activité de `0xa8e64a3c…74a5` : 2 dépôts, 16 achats, tous sur « Will Harry Kane win the 2026 Ballon d'Or? », Oui, pour 5 164,99 $ et 8 061,89 parts, du 9 au 11 oct., 1 redemption, 1 retrait. Retraits moins dépôts : 2 896,90 $.
- **Parts égales** (relevé par la session parallèle de l'enquête, relu ici) : 2 210,00 sur 4 421,41 USDC, soit 49,98 %, le 9 oct. ; 2 960,00 sur 5 925,84 USDC, soit 49,95 %, le 10 oct. Total 5 170,00 $ vers `0x48ec106c…b12d`, contre 5 173,25 $ vers le wallet de brace227 sur ses 4 premiers dépôts.
- **Clé neuve.** Avant son premier dépôt, `0x48ec106c…b12d` ne reçoit que les 2 210,00 USDC de la clé de brace227, plus du gaz de MetaMask. Sur 50 adresses testées, 94 essais en tout, seule celle-ci possède un Deposit Wallet actif : 44 adresses touchées par les clés des onze ou par la marche, sous les 2 formes de wallet, et 6 clés de dossiers sous l'ancienne forme seulement, leur forme récente étant leur wallet déjà connu. Le calcul de l'adresse retrouve 11 wallets connus sur 11. Limite : 5 clés de dossiers sans flux lu, et les anciens proxys Safe et Magic, ne sont pas testés.
- **Création avant les fonds.** Le wallet est créé la veille du premier versement.

**Le lien avec kraben006.** `0xd07bea20…2b98`, 4 oct. 13:54:35 UTC, 0,00205 ETH de la clé de brace227 vers celle de kraben006, envoi simple. Il suit de 108 s un paiement Relay de 0,00169 ETH venu de `7XUJsJBN…JfrZc` sur Solana, pour 4,62 USDT, prouvé par le même identifiant sur les deux chaînes. La clé part ainsi de 0,00207 ETH et n'en garde presque rien. Sa dernière sortie avant cette date remonte au 28 avril 2025 sur Ethereum et au 17 mai 2025 sur BSC : « première sortie en 17 mois » de l'audit devient 16 mois et demi. Sur la continuité de la valeur, relevée par la même session : au moins 81 % de l'envoi vient forcément du paiement Relay.

**Autres points communs entre brace227 et kraben006, plus faibles :** SwftSwap (15 096,29 $ et 188,97 $) et ChangeNOW (`0xdd3d72c5…`, Hot Wallet 3), deux services. La clé de kraben006 envoie aussi, 10 h après le transfert, 0,00247 ETH vers une adresse de dépôt de ChangeNOW : le gaz reçu semble donc avoir été revendu, ce qui n'est pas démontré.

**Ce qui va contre un opérateur unique** (même source, relu) : brace227 vend son Kane à 0,999 le 26 oct. à 23:10, alors que `0xa8e64a3c…74a5` ne vend jamais, attend le lot de redemption et retire 16 h 51 plus tard. Deux clés distinctes, deux stratégies de sortie.

**Ce que cela établit :** un lien financier direct et important entre ces deux clés, dont l'une finance presque entièrement l'autre juste avant des paris sur le même marché.

**Ce que cela n'établit pas :** qu'une seule personne contrôle les deux clés. Deux proches, un prêteur et un emprunteur, ou une avance entre amis donnent la même image. Rien ne permet de dire si ce wallet est le 12e compte allégué par la presse. Aucune information privilégiée n'en découle."""

TIMING = """- **Premier achat après le premier dépôt :** de 59 s à 607 s pour 9 comptes sur 11, 3,34 h pour VidenteRibeira et 8,88 h pour Thin-Disclaimer-Life. Ce délai n'a rien de distinctif face à des comptes du même âge, voir la section 4.
- **Calendrier :** les retraits principaux suivent la résolution du marché Kane, le 27 oct. à 01:57:41 UTC (relevé par la session parallèle), ou la vente qui l'a précédée. C'est le calendrier qui les rapproche.
- **Montants :** Thin-Disclaimer-Life et OuldLm3alem font des retraits de petite taille avant les gros (250 $ en SOL, 100 $ en BNB et en USDT). Un retrait d'essai et l'achat de gaz l'expliquent simplement. Aucun schéma de répartition commun, sauf le partage à parts égales de brace227.
- **Regroupements et circuits :** aucune sortie d'un dossier ne revient dans un autre dossier. La seule boucle lue reste interne : 2 500 USDC envoyés de `0x48ec106c…b12d` à `0x6a2522df…7973` et rendus le lendemain."""

RATE_READING = """**Lecture.** Ces rapports décrivent des routes, pas une intention. Aucun trait ne passe un seuil corrigé pour 9 tests (0,0056). Les traits ont été choisis après coup, et le groupe par la presse.

- **Financement moins d'une heure avant le premier achat : rien de distinctif.** 9/11 contre 32/39 comptes frais, p = 0,69. Le 9/11 contre 10/43, p = 0,0006, publié d'abord par l'enquête, venait d'historiques tronqués et d'âges mêlés : l'audit l'avait déjà ramené à 10/22, et cette lecture complète le confirme.
- **Origine Solana et KuCoin : indice faible.** 3/11 contre 6/68, p = 0,11. KuCoin Hot Wallet 2 : 3/3 contre 1/6, sur très peu de lignes. Ce tableau lit un seul dépôt par wallet ; sur tous les dépôts, 5 comptes nommés sur 11 passent par cette étiquette, sans comparaison possible avec cette ligne.
- **`VaultDepositooor` : l'écart le plus net.** 5/11 contre 9/77, p = 0,013, et 5/39 chez les comptes frais, p = 0,030. Cela désigne un outil de dépôt, pas un lien entre personnes.
- **SwftSwap :** 2/11 contre 0/54, p = 0,026. Ces deux comptes sont brace227 et kraben006 : ce n'est pas un trait indépendant du lien déjà lu.
- **MetaMask Gas Station :** 3/11 contre 2/54, p = 0,031. Un logiciel de portefeuille, pas un lien.
- **Liens directs entre clés :** 1 sur 55 paires nommées, 0 sur 1 431 paires de témoins, dont 0 sur 741 chez les comptes frais. Ce n'est pas un test, les paires n'étant pas indépendantes. Mais un transfert direct entre clés n'est pas banal dans ces témoins.
- **Clés lues :** 54 clés témoins sur 77 wallets, les autres n'ayant pas de propriétaire lisible par `owner()`, souvent d'anciens proxys."""

EXPOSURE_ANSWER = """- **Plateformes :** oui, mais seulement à l'entrée pour l'essentiel. KuCoin Hot Wallet 2 sur Solana pour 5 comptes, des adresses étiquetées Binance pour 3 comptes, Revolut et BloFin pour 1 chacun. En sortie : Revolut 5 pour Zoomman17. Étiquettes publiques, pas des preuves d'identité.
- **Échange instantané :** SwftSwap, nom de contrat vérifié, pour brace227 et kraben006. **ChangeNOW**, deux tags Blockscout concordants : sur la clé de kraben006 (834,85 USDC reçus en fév. 2026, 0,00247 ETH envoyés le 4 oct. vers une adresse de dépôt), et sur `0x3eaef6d5…`, financeur de la clé de brace227 fin 2024. NEAR Intents pour un petit échange de gaz de brace227.
- **Ponts :** Relay partout. Aussi Polygon PoS, deBridge, CCTP, Chainflip, THORChain et Across, chacun sur un ou deux comptes.
- **Mixeurs et protocoles de confidentialité :** aucune interaction lue avec Tornado Cash, Railgun ou un contrat étiqueté comme tel, sur tous les historiques lus.
- **Monero :** aucun indice, sur aucun compte."""

EXPOSURE = {
    'thin': ['KuCoin HW2, Binance HW6', '—', 'Relay', '—', 'Aucune lue', ABSENT],
    'vidente': ['KuCoin HW2', '—', 'Relay', '`GxjcMTWW…nvBW`', 'Aucune lue', ABSENT],
    'cookedrice': ['KuCoin HW2', '—', 'Relay', '`GxjcMTWW…nvBW`', 'Aucune lue', ABSENT],
    'wen': ['Binance (Hot Wallet 34)', '—', 'Relay', '`0x3ab2206b…7d50`, `0x51cf2d9f…4999`', 'Aucune lue', ABSENT],
    '0x86544e4dfde': ['Kraken et Binance sur `0x408ce42a…c5b3`, 2023-24', '—', 'Relay, Polygon PoS', '`0x0ce9bdf3…f06d`', 'Aucune lue', ABSENT],
    'brace227': ['BloFin ; KuCoin 10 et Binance 20 en 2022', 'SwftSwap ; ChangeNOW en amont, fin 2024', 'Relay, THORChain, NEAR Intents', '—', 'Aucune lue', ABSENT],
    'walletwallet8424': ['—', '—', 'Relay, Polygon PoS', '`0x0ce9bdf3…f06d`, `0xcc0f311e…23f7`', 'Aucune lue', ABSENT],
    'zoomman17': ['Revolut 1, 5 et 6', '—', 'Relay, Chainflip', '`0x58f298e3…0214`', 'Aucune lue', ABSENT],
    'kraben006': ['Deblock', 'SwftSwap, ChangeNOW', 'Relay, Across', '`0x58f298e3…0214`, `0xbd1f4462…eb3b`, `0x0c58909d…270d`, `0x7bef1627…5c24`', 'Aucune lue', ABSENT],
    'ouldlm3alem': ['KuCoin HW2, Binance (Hot Wallet 34)', '—', 'Relay, deBridge, CCTP', '`0xa3222357…59b3`', 'Aucune lue', ABSENT],
    '0xdd97e6': ['KuCoin HW2', '—', 'Relay', '`0x6bf18baf…7e95`', 'Aucune lue', ABSENT],
}

LEVELS = [
    ['Interaction directe confirmée', "Relay (documents officiels et identifiant sur les deux chaînes), SwftSwap (nom vérifié), deBridge (ordre lu), CCTP (message lu), Hyperliquid (registre public), Polygon PoS, Uniswap, THORChain"],
    ['Attribution probable, avec justification', "Binance, Kraken, Revolut, Chainflip, BloFin, KuCoin 10, ChangeNOW, NEAR Intents, Deblock, MetaMask (listes publiques et tags Blockscout). KuCoin Hot Wallet 2 : une seule source, Orb"],
    ['Simple compatibilité', "ChangeNOW liste XMR, et touche la clé de kraben006 et un financeur ancien de la clé de brace227 : rien ne dit quel actif était en face. Un service qui proposerait XMR derrière `GxjcMTWW…nvBW`, `0x3ab2206b…7d50` ou `0x51cf2d9f…4999` : rien ne l'indique, rien ne l'exclut"],
    ['Hypothèse non vérifiée', "Dépôt chez Revolut pour `0x8c5dc729…10fe` ; plateforme de sortie pour `0x51cf2d9f…4999` ; Kraken derrière les portefeuilles rechargés en ETH par Kraken: Hot Wallet 2"],
    ['Aucune preuve observée', "Tornado Cash, Railgun et tout contrat de confidentialité étiqueté ; toute conversion XMR ; FixedFloat et SimpleSwap"],
]

XMR_TEXT = """**Statut pour les 11 comptes : absent des données accessibles.** Aucune transaction lue n'implique un service dont on peut montrer qu'il a converti ces fonds en XMR.

- **Ce qui a été cherché :** toute adresse étiquetée parmi les services proposant XMR, y compris ChangeNOW, FixedFloat, SimpleSwap, StealthEX et Exolix, dans les listes publiques, les tags Blockscout et sur tous les historiques lus. **Seul résultat : ChangeNOW.** Il paie 834,85 USDC à la clé de kraben006 en fév. 2026 et reçoit d'elle, par une adresse de dépôt, 0,00241 ETH le 4 oct. 2026. Il finance `0x3eaef6d5…`, qui envoie 291,32 USDT à la clé de brace227 en janv. 2025. Ces montants sont petits, et aucun de ces flux n'est lu comme une conversion XMR : ChangeNOW échange des centaines d'actifs.
- **Liste de coins :** ChangeNOW liste XMR aujourd'hui (`evidence/docs/changenow_currencies.json`). SWFT ne le liste pas aujourd'hui (`evidence/docs/swft_coinlist_all.json`). Ces listes datent de la lecture, pas des transactions.
- **Ce que cela ne dit pas :** les fonds entrent dans des comptes de plateforme et des services non identifiés. Ce qui s'y passe est invisible. Une conversion XMR avant le financement, ou après `GxjcMTWW…nvBW`, n'est ni démontrée ni exclue. Une rupture de trace n'est pas un indice de Monero.
- **Ce qu'il faudrait :** le registre des services, par voie légale."""

CASHOUT_ANSWER = """**Sur 493 094,76 $ retirés, environ 74 % n'avaient pas bougé ou étaient revenus sur leur adresse le 2 novembre.** Sept comptes gardent 299 565,17 $ en stablecoins et 26,97 ETH. Trois comptes ont déposé chez des services non identifiés, soit 118 371,00 $, et Zoomman17 a envoyé 6 893,00 USDC vers une adresse de dépôt balayée par Revolut 5. **Aucune destination finale commune.** Le service `GxjcMTWW…nvBW` reçoit deux comptes : il est mutualisé."""

CASHOUT = {
    'thin': ['`CXVYMP5q…GrfJ`, `EnHRjTP4…PZ8B` (Solana)', 'Aucune', '79 537,63 USDC, 4,93 SOL', 'Ces deux adresses'],
    'vidente': ['`DMmDPF9s…1wt5T` (Solana)', '51 489,00 USDT balayés vers `GxjcMTWW…nvBW`, cosigné', '0,09 USDT', '`GxjcMTWW…nvBW`'],
    'cookedrice': ['`F7ew8r8X…Nh5Eh` (Solana)', '39 158,00 USDC balayés vers `GxjcMTWW…nvBW`, cosigné', '0,63 USDC', '`GxjcMTWW…nvBW`'],
    'wen': ['`0xe820ecb3…87cd` (Arbitrum)', '27 724,00 USDC vers `0x3ab2206b…7d50`, 1 % de côté, 3 morceaux regroupés par `0x51cf2d9f…4999`', '0,79 USDC', '`0x51cf2d9f…4999`'],
    '0x86544e4dfde': ['Clé `0x69837228…0ded` (Ethereum)', 'Aucune', '74 198,32 USDC', 'La clé'],
    'brace227': ['Clé `0xc852b093…af26` (Ethereum)', 'Petits échanges de gaz', '22 024,57 USDC', 'La clé'],
    'walletwallet8424': ['Clé `0x82775eb8…a3a1` (Ethereum)', 'Aucune', '35 546,89 USDC', 'La clé'],
    'zoomman17': ['Clé `0xd90d0013…f444` (Ethereum)', '6 893,00 USDC vers `0x8c5dc729…10fe`, puis `0xf7c8da79…d921` (Revolut 5)', '0,00 USDC', 'Revolut 5, étiquette à source unique'],
    'kraben006': ['Clé `0x101b5f4d…fb65` (Ethereum)', 'Dépôts Relay vers son propre wallet jusqu\'au 21 oct. ; 0,00247 ETH vers ChangeNOW le 4 oct.', '15 154,83 USDC', 'La clé'],
    'ouldlm3alem': ['Clé `0x1b500b6c…5f2c` (Polygon) ; `0xae232f78…c026` (BSC)', 'POL, USDT, deBridge, CCTP, Hyperliquid, retour', '73 001,19 USDC (Arbitrum), 99,80 USDT et 0,13 BNB (BSC)', 'La clé, Arbitrum'],
    '0xdd97e6': ['`0xca8b1f1a…6165` (Ethereum)', 'Aucune, nonce 0', '26,97 ETH', 'Cette adresse'],
}

MOVES = """Le rapprochement (`state/reconcile.json`) classe tous les mouvements de pUSD et de positions des 11 wallets :

- **Dépôts :** chacune des 46 frappes de pUSD liées à un `DEPOSIT` de l'API est trouvée. Les autres frappes sont toutes des `REDEEM`.
- **Retraits :** les 25 sorties de pUSD sont trouvées. Elles passent par le contrat de sortie, qui détruit le pUSD et rend de l'USDC.e, envoyé à Relay. **Le burn n'est pas une destination.**
- **Marché :** achats, ventes et redemptions passent par les contrats Polymarket, ou par des contreparties directes dans la même transaction. Ce sont des exécutions, pas des transferts.
- **Primes :** toutes les autres lignes correspondent à `REWARD`, `MAKER_REBATE`, `TAKER_REBATE` ou `REFERRAL_REWARD`, à une exception près : 0,20 pUSD reçu par OuldLm3alem d'un autre wallet.
- **Transferts de positions hors marché :** 0 sur les 11 wallets.
- **Soldes :** le solde pUSD calculé égale le solde lu sur 11 wallets sur 11."""

OULD_PATH = """Chaque saut est lu, avec l'actif qui change. Rien ne repose sur une ressemblance de montant.

| UTC | Saut | Preuve |
|---|---|---|
| 10-26 23:50:53 | 77 050,77 $ de pUSD détruits, USDC.e vers Relay, 839 893,73 POL natifs vers la clé dans la même transaction | Reçu `0x909d9602…a6f1`, `LogTransfer` du POL |
| 10-26 23:52:41 | 839 000 POL échangés contre 75 946,74 USDT par la clé elle-même, Uniswap | `0x8c358292…c2d3` |
| 10-29 20:54:51 | 75 946,74 USDT vers le transfert deBridge, ordre donné et reçu par la clé | Ordre `0xb6a2ccbf…3f8e`, statut `ClaimedUnlock` |
| 10-29 20:54:55 | 75 724,74 USDC reçus sur Arbitrum, du solveur `0x555ce236…c35b` | `0x88a0d82f…66b7` |
| 10-29 20:55:52 | 75 724,74 USDC envoyés par CCTP vers Hyperliquid | Message Circle `0x5c5e1650…223a`, `cctp-forward` vers la clé |
| 10-29 21:18 à 21:35 | 303 exécutions sur le perpétuel HYPE, 1 384 778,39 $ de volume, -2 415,41 $ réalisés, 306,71 $ de frais | Registre public Hyperliquid |
| 10-29 22:11:18 | 73 001,19 USDC reviennent sur Arbitrum par CCTP depuis HyperEVM | `0x6edc469d…55a5`, domaine source 19 |
| 10-29 22:11:59 | 888,19 POL deviennent 0,0343 ETH par deBridge | Ordre `0x95a84eb2…df58` |
| 11-02 | La clé détient 73 001,19 USDC et 0,0343 ETH sur Arbitrum, 3,14 POL sur Polygon | Soldes lus |

Attribution de Hyperliquid : registre public de l'adresse, `api.hyperliquid.xyz/info`, lu le 2 nov."""

WEN_PATH = """| UTC | Saut | Transaction |
|---|---|---|
| 10-27 22:58:06 | 27 724,79 $ retirés, USDC reçus sur `0xe820ecb3…87cd` (Arbitrum) par Relay | `0x094f60bf…9b91` |
| 10-27 22:58:10 | 27 724,00 USDC vers `0x3ab2206b…7d50` | `0xa06fecae…40da` |
| 10-27 22:58:11 | 277,24 USDC vers `0x435e3931…dd1d`, soit 1,00 % | `0x8246f439…` |
| 10-27 22:58:14 | 9 943,96 USDC vers `0xbf8f747e…621c` | `0xcad77f71…` |
| 10-27 23:44:29 | 9 436,20 USDC vers `0x5012817a…6ed7` | `0xc73ea34d…` |
| 10-28 00:02:54 | 8 066,60 USDC vers `0x15ba4d74…e552` | `0xd2ced301…` |
| 10-28 17:23:07 | Les trois morceaux, 27 446,76 USDC, regroupés dans une seule transaction vers `0x51cf2d9f…4999` | `0x6ef3a7e7…1547` |

`0x3ab2206b…7d50` a d'autres flux au même rapport : 238 567 reçus pour 236 181,33 envoyés, 75 000 pour 74 250, 60 000 pour 59 400, 50 000 pour 49 500. Les trois adresses à morceaux sont neuves et déléguées (EIP-7702), et `0x51cf2d9f…4999` (nonce 62 528) reçoit de 3 037 expéditeurs : profil d'un service, qui n'a pas d'étiquette. **Ni plateforme ni mixeur n'est démontré.**"""

BREAKS = [
    ['Comptes KuCoin, Binance, Revolut, BloFin', 'Thin-Disclaimer-Life, VidenteRibeira, cookedrice, WenZhuanBuPei, Zoomman17, OuldLm3alem, 0xdd97e6, brace227', '168 589,66 $ pour KuCoin et Binance, plus Revolut et BloFin', "Registre interne d'une plateforme", 'Réquisition légale auprès de la plateforme'],
    ['SwftSwap', 'brace227, kraben006', '15 285,26 $', "Le contrat paie par `withdraw`, sans identifiant d'ordre sur la chaîne", "Registre de SWFT"],
    ['`0x0ce9bdf3…f06d`', '0x86544e4dfde, walletwallet8424', '47 972,01 $', 'Compte Circle, même code que `0xee7ae85f…4055` (Binance), expéditeur sans étiquette : la ressemblance de code ne prouve pas l\'opérateur', "Identification de l'opérateur, puis son registre"],
    ['`0x58f298e3…0214` et trois autres', 'kraben006, Zoomman17', 'Dépôts de kraben006 et 867,98 $', 'Portefeuilles de paiement non attribués', "Identification de l'opérateur"],
    ['`0xa3222357…59b3`', 'OuldLm3alem', '23 386,26 $', 'Contrat non vérifié, 721 destinataires en 20 h', "Identification de l'opérateur"],
    ['`0x6bf18baf…7e95`', '0xdd97e6', '19 760,16 $', 'Portefeuille BSC à nonce 966 093, sans étiquette, BSC sans historique gratuit', "Explorateur BSC payant, puis identification"],
    ['`0xcc0f311e…23f7`', 'walletwallet8424', '16 808,96 $', '672 contreparties, sans étiquette', "Identification, ou enquête sur Stake.com et CoinsPaid en amont"],
    ['Chainflip', 'Zoomman17', '5 439,33 $', 'Actif source non lu', "Explorateur Chainflip : pas d'accès public testé qui ait répondu"],
    ['`GxjcMTWW…nvBW`', 'VidenteRibeira, cookedrice', '90 647,00 $ en aval', 'Service non identifié, mélange ses clients', 'Registre du service'],
    ['`0x51cf2d9f…4999`', 'WenZhuanBuPei', '27 446,76 $ en aval', 'Service non identifié', 'Registre du service'],
    ['`0xf7c8da79…d921` (Revolut 5)', 'Zoomman17', '6 893,00 $ en aval', 'Registre interne, étiquette à source unique', 'Réquisition auprès de Revolut'],
    ['`0x3f3ee0a9…207b` (ChangeNOW Dep)', 'kraben006', '0,00241 ETH en aval', 'Registre de ChangeNOW', 'Faible valeur : gaz seulement'],
    ['ChangeNOW, en amont', 'kraben006, brace227 (financeur ancien)', '834,85 $ et 291,32 $', 'Actif source de l\'ordre non public', 'Registre de ChangeNOW'],
    ['Entrées sur BSC et Base', 'brace227 surtout', 'Inconnu', 'Pas d\'historique gratuit, contrôle anti-robot sur `base.blockscout.com` non contourné', 'Plan payant, ou un explorateur sans contrôle'],
]

UNRESOLVED_INTRO = "Parties de dépôts que le PEPS en stablecoins ne couvre pas : financement en natif, échange, ou jeton hors liste. Elles sont racontées dans le dossier du compte quand le chemin est lu autrement."

READ_LIMITS = "`HIGH_VOLUME_AT_READ` : adresse à au moins 400 contreparties réelles, traitée en hub. `CHAIN_NOT_READABLE` : chaîne sans historique gratuit. Aucun `READ_FAILED`, `NODE_BUDGET` ni `DEPTH_BUDGET` n'apparaît s'ils ne sont pas listés ici."


def usd(x):
    return f'{float(x):,.2f}'.replace(',', ' ').replace('.', ',')


def short(a):
    return f'`{a[:10]}…{a[-4:]}`' if a and len(a) > 16 else f'`{a}`'


def table(head, lines):
    return '\n'.join(['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)] + ['| ' + ' | '.join(str(x) for x in l) + ' |' for l in lines])


def coverage(fund, cash, recon, unresolved, verify, tests, cases):
    dep = sum(c['account']['deposits'] for c in cases.values())
    wd = sum(c['account']['withdrawals'] for c in cases.values())
    n_dep = sum(len(c['deposits']) for c in cases.values())
    n_wd = sum(len(c['withdrawals']) for c in cases.values())
    unres = sum(u['usd'] for u in unresolved)
    passed = sum(1 for t in tests if t[1])
    lines = [
        ['Dépôts lus', f'{n_dep}, {usd(dep)} $'],
        ['Retraits lus', f'{n_wd}, {usd(wd)} $'],
        ['Dépôts rapprochés d\'une frappe de pUSD', f"{sum(r['deposits_matched'] for r in recon.values())} sur {n_dep}"],
        ['Retraits rapprochés d\'une sortie de pUSD', f"{sum(r['withdrawals_matched'] for r in recon.values())} sur {n_wd}"],
        ['Soldes pUSD calculés égaux au solde lu', f"{sum(1 for r in recon.values() if abs(r['computed_balance'] - r['balance_now']) < .01)} sur 11"],
        ['Segments non résolus, en dollars d\'entrée', f'{len(unresolved)} sur {n_dep} dépôts, {usd(unres)} $ (voir `UNKNOWN_PATHS.md`)'],
        ['Tests sur cas connus', f'{passed} sur {len(tests)} (`tests/test_forensics.py`)'],
    ]
    second = Counter()
    for k, n in verify.items():
        second[k.split('|')[1].split(':')[0]] += n
    if second:
        lines.append(['Seconde source par saut (nœud public ou second RPC)', ' ; '.join(f'{k} : {n}' for k, n in second.most_common())])
    return table(['Mesure', 'Valeur'], lines)


SERVICE_NOTE = {
    'exchange': 'plateforme',
    'instant_exchange': 'échange instantané',
    'bridge': 'pont',
    'dex_or_router': 'routeur ou infrastructure de portefeuille',
    'custodial_unattributed': 'service dépositaire non attribué',
    'polymarket_contract': 'contrat Polymarket',
    'mixer_or_privacy': 'mixeur ou confidentialité',
    'other_labeled': 'autre étiquette',
}


def common_funders(pairs, rates, cases, walks):
    label = {s: c['label'] for s, c in cases.items()}
    direct = pairs['direct']
    lines = [
        "# Financeurs et destinations communs", "",
        "Lu le 2 novembre 2026. Un service commun ne relie personne. Une origine commune, même démontrée, ne prouve ni un propriétaire commun ni une information privilégiée.", "",
        "## 1. Réponse", "", COMMON_ANSWER, "",
        "## 2. Transferts directs entre adresses de dossiers différents", "",
        f"{len(direct)} sur les historiques bruts lus : natif, internes et tous les ERC-20, spam compris, sur Ethereum, Polygon, Arbitrum et Optimism, plus Solana. La seule exécution de carnet entre deux dossiers (OuldLm3alem vers 0x86544e4dfde, `0x870eaa6c…`) n'est pas un transfert : c'est une exécution sur le marché.", "",
        table(['UTC', 'Chaîne', 'De', 'Vers', 'Montant', 'Transaction'], [[d['utc'], CHAIN.get(d['chain'], d['chain']), f"{label[d['src_case'][0]]} {short(d['src'])}", f"{label[d['dst_case'][0]]} {short(d['dst'])}", f"{d['amount']} {d['token']}", f"`{d['tx']}`"] for d in direct]), "",
        BRACE_KRABEN, "",
        "## 3. Adresses partagées, par classe", "",
    ]
    rows = []
    for x in sorted(pairs['shared'], key=lambda x: (-len(x['cases']), x['address'])):
        if x['address'] in pairs['nodes'].get(x['cases'][0], []) and x['cls'] == 'PERSONAL_SIZED':
            continue
        lab = x.get('label') or {}
        name = lab.get('name') or x.get('contract_name') or 'sans étiquette'
        cat = SERVICE_NOTE.get(lab.get('category'), lab.get('category') or x['cls'])
        rows.append([short(x['address']), CHAIN.get(x['chain'], x['chain']), name[:60], cat, x.get('nonce') if x.get('nonce') is not None else '—', ', '.join(label[c] for c in x['cases'])])
    lines += [table(['Adresse', 'Chaîne', 'Nom', 'Classe', 'Nonce', 'Dossiers'], rows), "", "Aucune de ces lignes n'est un lien entre personnes : chacune est un service nommé, ou un hub mesuré.", "", "**Adresse de taille personnelle partagée entre deux dossiers : aucune**, en dehors des deux clés du transfert direct ci-dessus.", ""]
    lines += ["## 4. Taux de base", "", rate_section(rates), ""]
    lines += ["## 5. Délais et montants", "", TIMING, ""]
    return '\n'.join(lines)


def rate_section(rates):
    if not rates:
        return "Comptes témoins non terminés à la date du rapport : aucun taux n'est donné."
    groups = rates['read_by_group']
    out = [f"Même lecteur sur {rates['comparators']} wallets témoins distincts, {rates['distinct_read']} lus, tous les dépôts lus depuis l'API avec pagination complète, et lignes illisibles retirées du dénominateur : " + ', '.join(f"{k} {v}" for k, v in groups.items()) + ". Les étiquettes sont réduites aux listes publiques, pour les nommés comme pour les témoins. Les 11 nommés passent par le même lecteur. Tirage et groupes repris de l'enquête d'origine. Exploratoire, sans correction pour tests multiples.", ""]
    rows = []
    for r in rates['traits']:
        rows.append([r['trait'], f"{r['named'][0]}/{r['named'][1]}", f"{r['all'][0]}/{r['all'][1]}", f"{r['p_all']:.3f}" if r.get('p_all') is not None else '—', f"{r['fresh'][0]}/{r['fresh'][1]}", f"{r['p_fresh']:.3f}" if r.get('p_fresh') is not None else '—'])
    out.append(table(['Trait', 'Nommés', 'Tous témoins', 'p', 'Comptes frais', 'p'], rows))
    nl, cl, fl = rates['named_links'], rates['comparator_links'], rates['fresh_links']
    cross = rates.get('named_comparator_direct') or []
    out += ["", "p : test exact unilatéral, nommés plus fréquents que témoins, non corrigé.", "", "**Liens clé à clé, même lecture (Ethereum, Polygon, Arbitrum) :**", "", table(['Groupe', 'Clés', 'Paires', 'Transferts directs', 'Contreparties personnelles partagées'], [['Nommés', nl['keys'], nl['pairs'], len(nl['direct']), len(nl['shared_personal'])], ['Tous témoins', cl['keys'], cl['pairs'], len(cl['direct']), len(cl['shared_personal'])], ['Comptes frais', fl['keys'], fl['pairs'], len(fl['direct']), len(fl['shared_personal'])]]), "", f"Liens directs entre une clé nommée et une clé témoin : {len(cross)}. Le lien brace227 et kraben006 sert de témoin positif : le lecteur le retrouve. Un seul témoin positif ne mesure pas la sensibilité de la méthode.", "", RATE_READING]
    return '\n'.join(out)


def exposure(rows, cases):
    label = {s: c['label'] for s, c in cases.items()}
    lines = ["# Exposition aux plateformes, ponts et services de confidentialité", "", "Lu le 2 novembre 2026. Une interaction avec une plateforme dit où l'argent est passé, pas à qui il appartient.", "", "## 1. Réponse", "", EXPOSURE_ANSWER, ""]
    lines += ["## 2. Par compte", "", table(['Compte'] + ['Plateformes', 'Échange instantané', 'Ponts', 'Service dépositaire non attribué', 'Mixeur ou confidentialité', 'XMR'], [[label[s]] + EXPOSURE[s] for s in ORDER]), ""]
    lines += ["## 3. Niveau de preuve par catégorie", "", table(['Niveau demandé', 'Ce qui y entre ici'], LEVELS), ""]
    lines += ["## 4. Monero", "", XMR_TEXT, ""]
    grouped = defaultdict(lambda: dict(cases=set(), n=0, usd=0.0, level='', src='', cat='', chains=set()))
    for r in rows:
        k = r['name'] or r['address']
        g = grouped[k]
        g['cases'].add(label[r['case']])
        g['n'] += int(r['transfers'])
        g['usd'] += float(r['usd_order_of_magnitude'])
        g['level'], g['src'], g['cat'] = r['attribution_level'], r['attribution_source'], r['category']
        g['chains'].add(r['chain'])
    tab = [[k[:58], SERVICE_NOTE.get(g['cat'], g['cat'] or 'mesuré'), ', '.join(sorted(g['chains'])), ', '.join(sorted(g['cases'])), g['n'], f"{g['usd']:,.0f}".replace(',', ' '), g['level']] for k, g in sorted(grouped.items(), key=lambda kv: -kv[1]['usd'])]
    lines += ["## 5. Tous les services touchés", "", "Montant : ordre de grandeur en dollars, natifs compris au cours approximatif, entrées et sorties additionnées, pour classer seulement. Une ligne par service, détail par dossier dans `data/service_attributions.csv`.", "", table(['Service', 'Catégorie', 'Chaînes', 'Dossiers', 'Transferts', 'Ordre de grandeur $', 'Niveau'], tab), ""]
    return '\n'.join(lines)


def cashout(cases, walks, cash, bridges):
    label = {s: c['label'] for s, c in cases.items()}
    total = sum(c['account']['withdrawals'] for c in cases.values())
    lines = ["# Sorties des 11 comptes", "", "Lu le 2 novembre 2026. Le burn de pUSD n'est pas une destination : l'adresse zéro n'apparaît comme cible d'aucun retrait. La destination est technique : elle ne dit rien du bénéficiaire économique.", "", "## 1. Réponse", "", CASHOUT_ANSWER, "", "## 2. Par compte", "", table(['Compte', 'Retraits $', 'Destination technique', 'Suite vérifiable', 'Encore sur la première adresse le 2 nov.', 'Dernier point public'], [[label[s], usd(cases[s]['account']['withdrawals'])] + CASHOUT[s] for s in ORDER]), "", f"Total des retraits : {usd(total)} $, 25 retraits.", "", "## 3. Ce que sont les mouvements", "", MOVES, ""]
    h = bridges.get('hyperliquid') or {}
    if h:
        lines += ["## 4. OuldLm3alem : le chemin complet", "", OULD_PATH, ""]
    lines += ["## 5. WenZhuanBuPei : le chemin complet", "", WEN_PATH, "", "## 6. Toutes les lignes", "", "`data/cashout_paths.csv` donne chaque saut, et `graphs/cashout_network.graphml` le graphe.", ""]
    return '\n'.join(lines)


def unknown(unresolved, walks, cases):
    label = {s: c['label'] for s, c in cases.items()}
    lines = ["# Ruptures de traçabilité", "", "Lu le 2 novembre 2026. Une rupture n'est pas une preuve de passage par Monero ni par un mixeur : elle dit seulement où la lecture publique s'arrête.", "", "## 1. Où la trace s'arrête", "", table(['Point d\'arrêt', 'Dossiers', 'Montant', 'Pourquoi', 'Ce qu\'il faudrait'], BREAKS), "", "## 2. Segments comptables non résolus", ""]
    if unresolved:
        lines += [UNRESOLVED_INTRO, "", table(['Dossier', 'Chemin', 'Adresse', 'Chaîne', 'Raison', '$'], [[label[u['case']], u['path'], short(u['where']), CHAIN.get(u.get('chain'), u.get('chain') or ''), u['reason'], usd(u['usd'])] for u in unresolved])]
    else:
        lines.append("Aucun.")
    gaps = defaultdict(list)
    for s, w in walks.items():
        for x in w['stops']:
            if x['reason'] in ('READ_FAILED', 'NODE_BUDGET', 'DEPTH_BUDGET', 'CHAIN_NOT_READABLE', 'HIGH_VOLUME_AT_READ'):
                gaps[x['reason']].append((label[s], x['address'], x['chain'], x.get('detail') or ''))
    lines += ["", "## 3. Arrêts de lecture", "", table(['Raison', 'Dossier', 'Adresse', 'Chaîne'], [[r, a, short(b), CHAIN.get(c, c)] for r, v in sorted(gaps.items()) for a, b, c, _ in v]) if gaps else "Aucun.", "", READ_LIMITS, ""]
    return '\n'.join(lines)
