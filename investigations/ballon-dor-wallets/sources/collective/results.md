# Résultats de l'étude collective

Rapport complet : `../reports/rapport_final.md`, sections 5 et 8. Chaque chiffre y renvoie à `derived/` ou `exploratoire/`.

## Verdict de la partie A, fixé d'avance

`VISIBLE_NON_SPECIFIQUE` au 13 oct. 18:51 UTC et au 23 oct. 15:17:49 UTC. Une seule affaire, n effectif = 1. Conditionnel, sans validation indépendante : l'auteur connaissait l'affaire.

## Registre

```
lignes sur données réelles : 20 (contrôles synthétiques à part : 2)
par phase : apres_gel 20
comparaisons réelles au total (balayages compris) : 140114
par agent : claude 20
non déclarées dans le plan (exploratoires) : 4, dont venues de code non gelé : 4
p non résolus (ne pas citer) : 0
seuil officiel, Bonferroni sur toutes les comparaisons réelles : 0.05/140114 = 3.57e-07
```

Aucun p n'approche ce seuil. Le plus bas de la partie A vaut 0.093.

## Portes du protocole

- Phases 1 à 4 : faites. Phase 7 : reproduction en copie fraîche, E1, E1G, E2, E3 et placebo identiques, E4 non (voir ci-dessous).
- **Phases 5 et 8 non lancées** : ni les quatre audits à l'aveugle, ni les deux audits de conclusions. Sur ta consigne de livrer sans multiplier les expériences. Ce rapport n'a donc pas de relecture indépendante.

## Deviations and data notes

- Amendement 001 : plafond de lecture des âges porté de 2 500 à 3 200, aucun résultat vu.
- Amendement 002 : E4 v2, ordre canonique et graines explicites, décidé par Benjamin après lecture des résultats. `audit/E4_non_reproductibilite.md`.
- `G12` du plan compte 11 wallets : 11 étiquettes publiques sont résolues.
- E5, comparateur `meme_token` : réservoir de 10 wallets pour un groupe de 10, donc un seul groupe possible. Ses centiles ne sont pas cités.
- E6 : le champ `one_withdrawal_or_more_before_ceremony` de `derived/B_E6.json` utilise par erreur le 27 oct. 20:00 UTC au lieu du 26. Il n'est pas cité. Recalcul correct : 0 premier retrait entre l'article et la cérémonie, dans les quatre groupes.
- E6 : code écrit après le sceau de la partie A et après la lecture de E5.
- Analyses hors plan, exploratoires : `exploratoire/combos.json`, `rank_combos.json`, `price_days.json`, `per_wallet_stats.json`, `E4_v2_summary.json`, taux de base dans `../controls/`.
- Âges : `/activity` commence au premier événement de trading, sans les dépôts. L'âge mesure donc la première opération, pas la création du compte.
- Recensement : les wallets écartés par le pré-filtre n'ont pas d'âge lu, comptés à part (`unknown_age_seen`).
