# Recherche d'edge Polymarket : état au 02/10/2026 14 h (coupé par la limite d'usage)

Méthode : skill etude-gelee. Criblage exploratoire sur TRAIN seulement, tout test au registre (`code/registre.py`), plan gelé seulement pour une hypothèse qui survit.
Découpage fixé avant tout résultat : TRAIN 06/2025 à 01/2026, VALID 02 à 05/2026, TEST 06 à 09/2026 (crypto horaire). Univers p8 : split déjà défini par la phase 8.

## Déjà fait, ne pas refaire
- Phase 8 de l'enquête Maduro/Iran : signaux wallets et momentum, rien d'exploitable (`enquete_maduro_iran/phase8/RAPPORT_PHASE8.md`).
- Solana/on-chain : nombreuses études négatives (voir mémoire : post-détection, forensique, entry zone, sniper capital, coordination).
- **C (calibration avant échéance, univers p8, TRAIN)** : `code/ana_c10_calibration.py`, `derived/c10_TRAIN.json`. Prix calibrés, 16 stratégies, aucune ne survit (IC ±5 % par dollar, puissance faible). ABANDONNÉE, VALID/TEST non regardés.

## En cours
- `data/raw/gamma_btc_hourly.jsonl` : 11 779 marchés BTC horaires (série 10114) complets. Bug de pagination corrigé (Gamma plafonne à 100 par page).
- `code/col_30_prices_history.py btc_hourly` : prix minute du jeton Up, reprend seul là où il s'est arrêté (relancer la même commande). ~1 000/11 281 faits à 13 h 42.
- `code/col_20_binance_klines.py BTCUSDT` (puis ETH, SOL, XRP) : bougies 1 min, à relancer si le fichier `.csv.tmp` n'est pas devenu `.csv`.
- Séries de réplication : ETH 10117, SOL 10122, XRP 10123 horaires, BTC 15 min 10192 (le 5 min 10684 se résout sur Chainlink, exclu).

## Faits mesurés
- Frais preneur crypto actifs depuis le 06/03/2026 : frais = parts × 0,07 × p × (1 − p) (doc officielle). 3,5 % de la mise à p = 0,5, 0,35 % à p = 0,95. Makers sans frais.
- Issues BTC horaire : 5 904 hausses, 5 875 baisses.

## Prochaines étapes
1. A : juste prix Φ(ln(S/O)/(σ√τ)) depuis Binance (σ sur le passé seul) contre prix Polymarket à 5, 10… 55 min ; contrôle positif = reconstruire la résolution depuis Binance ; calibration ; stratégie d'écart, surtout aux extrêmes en fin d'heure ; exécution validée ensuite sur les trades réels (data-api) avec frais.
2. B : marchés météo (température) contre METAR (archive IEM) et prévisions Open-Meteo (previous runs).
3. Pour toute survivante : plan gelé, contrôles positifs, VALID puis TEST, audit à l'aveugle.
