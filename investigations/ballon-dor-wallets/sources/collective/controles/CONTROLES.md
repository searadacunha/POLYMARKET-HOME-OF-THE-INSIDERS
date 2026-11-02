# Contrôles positifs

Exécutés par `code/ctl_synth.py` sur tables synthétiques (3 graines) et une injection dans une vraie unité X.

```json
[
 {
  "seed": 11,
  "table": "nul",
  "alert": false,
  "expected": false,
  "n": null
 },
 {
  "seed": 11,
  "table": "moyen",
  "alert": true,
  "expected": true,
  "n": 3
 },
 {
  "seed": 11,
  "table": "moyen_sous_seuil",
  "alert": false,
  "expected": false,
  "n": null
 },
 {
  "seed": 11,
  "table": "fort",
  "alert": true,
  "expected": true,
  "n": 3
 },
 {
  "seed": 29,
  "table": "nul",
  "alert": false,
  "expected": false,
  "n": null
 },
 {
  "seed": 29,
  "table": "moyen",
  "alert": true,
  "expected": true,
  "n": 3
 },
 {
  "seed": 29,
  "table": "moyen_sous_seuil",
  "alert": false,
  "expected": false,
  "n": null
 },
 {
  "seed": 29,
  "table": "fort",
  "alert": true,
  "expected": true,
  "n": 3
 },
 {
  "seed": 47,
  "table": "nul",
  "alert": false,
  "expected": false,
  "n": null
 },
 {
  "seed": 47,
  "table": "moyen",
  "alert": true,
  "expected": true,
  "n": 3
 },
 {
  "seed": 47,
  "table": "moyen_sous_seuil",
  "alert": false,
  "expected": false,
  "n": null
 },
 {
  "seed": 47,
  "table": "fort",
  "alert": true,
  "expected": true,
  "n": 3
 },
 {
  "table": "injection_reelle",
  "unit": "south-carolina-governor-winner-2026",
  "rows": 34,
  "silent_before": true,
  "found_at": 1792008000
 }
]
```

Le nul reste muet, le moyen à 3 wallets alerte, le moyen sous le seuil de N reste muet, le fort alerte. Table de puissance : sur ces tables, A0 détecte une cohorte d'au moins 3 wallets à 4 000 $ chacun en moins de 72 h, et ne détecte pas 2 wallets. Puissance sur données réelles inconnue : aucun cas vérifié n'existe.
