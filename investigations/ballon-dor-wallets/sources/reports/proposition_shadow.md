# Proposition d'intégration en shadow mode

Rien n'est intégré. PolySentinel n'a pas été modifié, aucun scénario gelé n'est touché. À toi de décider.

## Ne pas intégrer comme détecteur

La cohorte fraîche A0 n'est **pas** une méthode de détection prometteuse sur ces données. Verdict gelé `VISIBLE_NON_SPECIFIQUE`, rang 41 du recensement, placebo non significatif. Elle pourrait au mieux servir de contexte dans un dossier, sans score.

## Ce qui mérite une intégration en shadow, côté flux

| Élément | Gain constaté | Fichier | Test à exiger |
|---|---|---|---|
| Preuve Relay en sortie par le mémo Solana ou la fin de calldata | Corrige la limite écrite dans `docs/FUND_FLOWS.md` : sur Solana, le lien se prouve par la chaîne | `tools/case_chain.py` | Cas réels de Thin, plus un faux identifiant copié |
| Retrait suivi après le burn de pUSD | Évite l'adresse zéro comme destination | `tools/test_case_chain.py` | Déjà écrit |
| Payeur d'une adresse de pont trouvé par dichotomie du solde | Une douzaine d'appels au lieu de milliers | `tools/case_chain.py` | Contrôle positif sur un log connu |
| Historique Solana vérifié contre une signature connue | Écarte le faux zéro observé sur un nœud public | `tools/sol.py` | Déjà intégré à la lecture |
| Classe « service mesuré » par trafic et nonce | Fait tomber les paires naïves de financeur commun | `tools/classify_links.py` | Sur marchés témoins, taux de paires avant et après |

## Conditions

- Mode shadow, sans effet sur les catégories, scores, seuils ni scénarios historiques.
- Évaluation sur des marchés témoins tirés d'avance, jamais seulement sur cette affaire.
- **Échéance :** la route publique `requests/v2` de Relay disparaît le 24 novembre 2026, et la v3 exige une clé. Sans clé, seule la preuve par la chaîne restera disponible, et il faudra un autre moyen de trouver le paiement.
