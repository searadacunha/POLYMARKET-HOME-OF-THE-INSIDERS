# CASE 05 — Le problème des proxys résolu, sweep complet des 3408 recipients ChangeNOW

Date: 2026-08-31. Débloque le point mort du 23/06 ("on n'arrivait pas à passer les proxys").

## Le bug d'avant
On interrogeait la data-api Polymarket sur l'**EOA** (et une heuristique "rout"), alors que
Polymarket indexe sur le **compte de trading**, pas l'EOA. sig198 ressortait 0 partout.

## Ce qu'on a compris (architecture, vérifié on-chain)
La data-api Polymarket (`/activity`, `/positions`, `/value`) indexe sur le compte de trading,
qui est de DEUX formes selon l'utilisateur :
- **EOA-direct** : l'EOA signe et trade directement sur le CTF Exchange
  `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e`. La data-api renvoie l'activité SUR L'EOA.
- **Deposit wallet (proxy)** : un contrat déterministe déployé par le
  `DepositWalletFactory` = `0x00000000000fb5c9adea0298d729a0cb3823cc07` (source vérifiée
  "DepositWalletFactory", @author Polymarket). La data-api indexe sur le proxy, pas l'EOA.

### Résolveur EOA -> deposit wallet (offline, validé 21/21)
- `_id = bytes32(uint160(owner))` (confirmé : event `WalletDeployed` a owner==id).
- `salt = keccak256(abi.encode(factory, _id))`.
- `initcode = TEMPLATE_CONSTANT + left_pad32(owner)` (l'owner est embarqué dans le bytecode).
- `addr = CREATE2(factory, salt, keccak(initcode))`.
- Validé sur l'ancre opérateur (0x08D409... -> 0x5008c44A...) ET 20/20 déploiements réels
  indépendants (tous shape LEGACY, impl `0x58ca52...`). Code: `proxy_resolver.py`.

## Le sweep complet (pm_sweep.py -> state/pm_sweep.jsonl, 3408/3408, 0 erreur)
Pour chaque recipient : résout le deposit wallet (offline) + teste data-api sur EOA ET proxy,
prend le compte non vide, size l'activité lifetime.

### Résultats
- **158 recipients sur 3408 (4,6%) sont des parieurs Polymarket** : 112 EOA-direct, 46 via
  deposit wallet. Les 46 étaient TOTALEMENT invisibles avant (29% des parieurs).
- **Seulement 46 533 $ des 8 351 690 $ payés par f2020 (0,6%)** vont à des parieurs PM.
- Tailles : 45 avec volume lifetime >= 1000 $, 12 >= 10 000 $, 2 >= 100 000 $. MAIS les gros
  volumes sont des BOTS haute-fréquence "Bitcoin Up or Down" horaires (petites tailles).
- **Position max sur un seul marché, tous recipients confondus : ~3 527 $** (un pari Dota 2,
  0xd484a5133c) puis ~2 040 $ (France vs Spain). Seulement 2 recipients > 1000 $ sur un marché.
  **Zéro whale, zéro grosse position coordonnée.**
- Causal : 66% des parieurs ont reçu leur paiement CN AVANT leur premier trade PM (fundable).

### Audit résiduel (residual_audit.py) — pas de classe cachée
95 non-parieurs à CN >= 2000 $ tracés on-chain : aucun n'a de proxy PM personnel. Les rares
"touches" sont des hubs partagés (routeurs/CEX reçus par plusieurs recipients), pas des comptes
Polymarket. Le sweep EOA+deposit-wallet capture bien tous les vrais parieurs.

## VERDICT
Le lien ChangeNOW -> Polymarket est **réel mais minuscule** : un filet de petit retail
(bots crypto Up/Down horaires + un peu de sport), pas un pipeline d'insiders ni de baleines.
Le problème des proxys est résolu ; le corriger a rendu 46 parieurs visibles mais n'a révélé
aucune baleine cachée. La thèse "wallets Polymarket funded via ChangeNOW" tient sur ~158
comptes, tous petits.

## Fichiers
- `proxy_resolver.py` — résolveur offline validé.
- `pm_sweep.py` -> `state/pm_sweep.jsonl` — sweep complet (checkpointé).
- `pm_report.py` -> `state/pm_traders.csv` — 158 parieurs, sizing, causal.
- `residual_audit.py` — audit anti-classe-cachée.
- Diagnostic archi : `api_probe.py`, `pm_arch.py`, `trace_flow.py`, `factory_logs.py`.
