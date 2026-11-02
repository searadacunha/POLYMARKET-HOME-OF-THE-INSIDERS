# Phase 14 : README

**Question :** le 2e achat du même wallet SIG_HIST fournit-il une fenêtre d'exécution exploitable ?

**Réponse :** non. Conclusion **B. SIGNAL PRÉDICTIF MAIS NON EXÉCUTABLE**. Voir `RAPPORT_PHASE14.md`.

## Rejouer

**Depuis le dossier de données historiques** (contient `p8/`, `p9/`, `p10/`) :

```bash
cd /private/tmp/claude-501/-Users-benjamindacunha-Downloads/b2d4e943-355c-4fe5-9c72-2438aead8117/scratchpad/mad
python3 ~/Documents/Crypto/enquete_maduro_iran/scripts/p14_second_buy.py
python3 ~/Documents/Crypto/enquete_maduro_iran/scripts/p14_execution.py --simuler
python3 ~/Documents/Crypto/enquete_maduro_iran/scripts/p14_execution.py --analyser
python3 ~/Documents/Crypto/enquete_maduro_iran/scripts/p14_execution.py --cas
python3 ~/Documents/Crypto/enquete_maduro_iran/scripts/p14_execution.py --direct
```

| Commande | Rôle | Durée |
|---|---|---|
| `p14_second_buy.py` | reconstruit les 2e achats ; **s'arrête** si le résultat diffère de la phase 13 | environ 40 s |
| `--simuler` | entrée et sortie sur les flux de la phase 10 | environ 30 s |
| `--analyser` | tables et conclusion | environ 20 s |
| `--cas` | 8 comptes, Maduro, Iran, nouveaux wallets | |
| `--direct` | 2e achats des alertes live, sur le carnet de la phase 11 | |

**Attention :** le dossier de données est dans `/private/tmp`. Il disparaît au redémarrage du Mac. Les CSV de `phase14/` restent.

## Journal papier en direct (PAPER ONLY)

**Lancer**, depuis `scripts/` :

```bash
nohup ./p14_run.sh >/dev/null 2>&1 &
```

**Arrêter** :
1. créer le fichier `donnees/brut_p14/STOP` ;
2. lancer `pkill -f "Python p14_paper.py"`.

**Fonctionnement :**
- il lit seulement les alertes des phases 11 (`brut_p11/live/alerts.jsonl`) et 13 (`brut_p13/paper_alerts.jsonl`) ;
- il ne modifie aucun autre processus ;
- il s'arrête au redémarrage du Mac, comme les autres.

**Sorties :**
- `phase14/paper_second_buy.csv` : une ligne par 2e achat, écrite 300 s après la détection ;
- `donnees/brut_p14/` : `paper_second_buy.jsonl` (détail, toutes les tailles), `paper_fenetres.jsonl` (toutes les fenêtres d'une heure, avec ou sans 2e achat), `paper_etat.jsonl`, `run_paper.log`.

## Fichiers

| Fichier | Contenu |
|---|---|
| `PROTOCOLE_P14.md` | protocole écrit avant les résultats |
| `phase14_second_buy_events.csv` | les 662 2e achats (SIG_HIST et contrôles) |
| `phase14_execution.csv` | groupe × split × estimateur × latence × taille × horizon |
| `phase14_controls.csv` | SECOND_BUY contre MATCHED_CONTROL, IC bootstrap groupés par marché |
| `phase14_capacity.csv` | exécutable entier, partiel, impossible ; glissement ; net |
| `phase14_latency.csv` | T_trade, T_wallet (supposé), T_book (observé) |
| `phase14_tables.csv` | population, catégories, représentativité, timing, carnet, prix avant et après, segments |
| `phase14_cas.csv` | 8 comptes, Maduro, Iran, nouveaux wallets |
| `phase14_live_second_buy.csv` | alertes live et leur 2e achat éventuel (carnet de la phase 11) |
| `phase14_conclusion.json` | sortie de l'arbre de décision |
