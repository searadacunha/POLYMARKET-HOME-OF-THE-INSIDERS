# Ruptures de traçabilité

Lu le 2 novembre 2026. Une rupture n'est pas une preuve de passage par Monero ni par un mixeur : elle dit seulement où la lecture publique s'arrête.

## 1. Où la trace s'arrête

| Point d'arrêt | Dossiers | Montant | Pourquoi | Ce qu'il faudrait |
|---|---|---|---|---|
| Comptes KuCoin, Binance, Revolut, BloFin | Thin-Disclaimer-Life, VidenteRibeira, cookedrice, WenZhuanBuPei, Zoomman17, OuldLm3alem, 0xdd97e6, brace227 | 168 589,66 $ pour KuCoin et Binance, plus Revolut et BloFin | Registre interne d'une plateforme | Réquisition légale auprès de la plateforme |
| SwftSwap | brace227, kraben006 | 15 285,26 $ | Le contrat paie par `withdraw`, sans identifiant d'ordre sur la chaîne | Registre de SWFT |
| `0x0ce9bdf3…f06d` | 0x86544e4dfde, walletwallet8424 | 47 972,01 $ | Compte Circle, même code que `0xee7ae85f…4055` (Binance), expéditeur sans étiquette : la ressemblance de code ne prouve pas l'opérateur | Identification de l'opérateur, puis son registre |
| `0x58f298e3…0214` et trois autres | kraben006, Zoomman17 | Dépôts de kraben006 et 867,98 $ | Portefeuilles de paiement non attribués | Identification de l'opérateur |
| `0xa3222357…59b3` | OuldLm3alem | 23 386,26 $ | Contrat non vérifié, 721 destinataires en 20 h | Identification de l'opérateur |
| `0x6bf18baf…7e95` | 0xdd97e6 | 19 760,16 $ | Portefeuille BSC à nonce 966 093, sans étiquette, BSC sans historique gratuit | Explorateur BSC payant, puis identification |
| `0xcc0f311e…23f7` | walletwallet8424 | 16 808,96 $ | 672 contreparties, sans étiquette | Identification, ou enquête sur Stake.com et CoinsPaid en amont |
| Chainflip | Zoomman17 | 5 439,33 $ | Actif source non lu | Explorateur Chainflip : pas d'accès public testé qui ait répondu |
| `GxjcMTWW…nvBW` | VidenteRibeira, cookedrice | 90 647,00 $ en aval | Service non identifié, mélange ses clients | Registre du service |
| `0x51cf2d9f…4999` | WenZhuanBuPei | 27 446,76 $ en aval | Service non identifié | Registre du service |
| `0xf7c8da79…d921` (Revolut 5) | Zoomman17 | 6 893,00 $ en aval | Registre interne, étiquette à source unique | Réquisition auprès de Revolut |
| `0x3f3ee0a9…207b` (ChangeNOW Dep) | kraben006 | 0,00241 ETH en aval | Registre de ChangeNOW | Faible valeur : gaz seulement |
| ChangeNOW, en amont | kraben006, brace227 (financeur ancien) | 834,85 $ et 291,32 $ | Actif source de l'ordre non public | Registre de ChangeNOW |
| Entrées sur BSC et Base | brace227 surtout | Inconnu | Pas d'historique gratuit, contrôle anti-robot sur `base.blockscout.com` non contourné | Plan payant, ou un explorateur sans contrôle |

## 2. Segments comptables non résolus

Parties de dépôts que le PEPS en stablecoins ne couvre pas : financement en natif, échange, ou jeton hors liste. Elles sont racontées dans le dossier du compte quand le chemin est lu autrement.

| Dossier | Chemin | Adresse | Chaîne | Raison | $ |
|---|---|---|---|---|---|
| Zoomman17 | zoomman17-D5 | `0xd90d0013…f444` | ethereum | origin outflow not matched in its stablecoin ledger (native or swap funded) | 258,54 |

## 3. Arrêts de lecture

| Raison | Dossier | Adresse | Chaîne |
|---|---|---|---|
| CHAIN_NOT_READABLE | OuldLm3alem | `0xae232f78…c026` | bsc |
| HIGH_VOLUME_AT_READ | walletwallet8424 | `0xcc0f311e…23f7` | ethereum |

`HIGH_VOLUME_AT_READ` : adresse à au moins 400 contreparties réelles, traitée en hub. `CHAIN_NOT_READABLE` : chaîne sans historique gratuit. Aucun `READ_FAILED`, `NODE_BUDGET` ni `DEPTH_BUDGET` n'apparaît s'ils ne sont pas listés ici.
