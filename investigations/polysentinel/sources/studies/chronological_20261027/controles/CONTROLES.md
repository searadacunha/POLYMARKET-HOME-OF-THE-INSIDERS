# Contrôles synthétiques avant gel

Le module v1.2 copié et les portes documentaires ont été exécutés ensemble. Aucune donnée réelle utilisée.
Sensibilité mécanique des scénarios, pas puissance statistique ni calibration sur marchés réels.

| Graine | Scénario | Wallets injectés | Dossiers émis | Prioritaires | Verdict |
|---|---|---:|---:|---:|---|
| 11 | null | 6 | 0 | 0 | NO_PRIORITY_SIGNAL |
| 11 | medium | 6 | 6 | 3 | DESCRIPTIVE_ONLY |
| 11 | strong | 6 | 6 | 6 | DESCRIPTIVE_ONLY |
| 29 | null | 6 | 0 | 0 | NO_PRIORITY_SIGNAL |
| 29 | medium | 6 | 6 | 3 | DESCRIPTIVE_ONLY |
| 29 | strong | 6 | 6 | 6 | DESCRIPTIVE_ONLY |
| 47 | null | 6 | 0 | 0 | NO_PRIORITY_SIGNAL |
| 47 | medium | 6 | 6 | 3 | DESCRIPTIVE_ONLY |
| 47 | strong | 6 | 6 | 6 | DESCRIPTIVE_ONLY |

Nul : 0/6 à chacune des trois graines ; moyen : 3/6 ; fort : 6/6.
Les labels synthétiques sont construits : leurs taux directionnels ne sont pas des preuves économiques.
11 contrôles adverses PASS, inventaire dans `adversarial.json`. Toutes les rentabilités restent null.
Le verdict ne qualifie jamais un wallet d’initié. Dix lignes synthétiques sont ajoutées par exécution ; les précédentes restent au registre.
