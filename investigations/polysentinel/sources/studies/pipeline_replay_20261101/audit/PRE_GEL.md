# Audits d'avant-gel, 1er novembre 2026

Agents `leakage-auditor` et `silent-failure-hunter`, lancés sur le plan et le code avant tout calcul du détecteur. Ni l'un ni l'autre n'a lancé de script de l'étude ni lu `labels_after.json`. `derived/` était vide. Ces rapports ne remplacent pas l'audit à l'aveugle de la phase 5.

| Constat | Gravité | Auteur | Décision |
|---|---|---|---|
| `umaResolutionStatus` actuel présent dans la version ouverte : la famille passe en rotation lente, `part_annonce` fausse | BLOQUANT | les deux | Retiré de `ATTRS_BRUTS` ; test dans `ctl_replay.py` |
| Le littéral « ballon d'or » de `priority.py` décide de la rotation du scénario « réaliste » | BLOQUANT | fuites | Référence S_A neutre, S_L à part ; test |
| M1 : inconnu devenu « ouvert pour toujours », non séparé dans les sorties, `linked_market_rotation` impossible | BLOQUANT | les deux | Clé `cond:` ; drapeau `m1` ; résultats avec et sans ; limite dans chaque dossier |
| Le catalogue local ne connaît que les marchés vivants après T_fin | MAJEUR | fuites | Non utilisé pour le recensement |
| « Borne basse » faux | MAJEUR | les deux | Retiré du plan |
| T_alertes calé sur la date de l'affaire | MAJEUR | fuites | Fenêtres glissantes 24 h et 72 h, taux par jour |
| S_A et S_B ne partaient pas du même historique que S_G | MAJEUR | les deux | Plancher T_debut commun, sauf S_C ; test |
| Horvitz-Thompson sans second degré, unités mélangées | MAJEUR | les deux | Marchés retenus seulement ; chiffres avec et sans M/m |
| Strates D/C mal étiquetées | MAJEUR | les deux | Tirage conservé, limite écrite |
| L'échéance `end_date` ne déclenche aucune réévaluation | MAJEUR | échecs silencieux | Échéances ajoutées aux transitions ; test |
| Deux règles mortes non déclarées (`liquidity_fraction`, `cohort_size`) | MAJEUR | échecs silencieux | Écrites au plan et dans chaque sortie R1 |
| `comportements` retenait le premier score, même 0 | MAJEUR | échecs silencieux | Daté au premier score ≥ 1 |
| Reprise sous une autre grille | MAJEUR | échecs silencieux | Refus explicite |
| S_E appelé « complet » avec 30 jours, réponse vide lue comme une mesure | MAJEUR | échecs silencieux | Sans borne basse ; `estimable` ; vide et tronqué non estimables |
| Oracle absent de S_C | MINEUR | les deux | Oracle partiel haché, fermé par la synchronie ; test |
| `config.json` lu en direct | MINEUR | les deux | Copie `data/config_production.json`, empreinte dans chaque sortie |
| `sceller` écrasable, historiques hors sceau | MINEUR | fuites | Refus de réécriture, historiques scellés |
| `ledger` n'inscrivait pas certaines erreurs de transport | MINEUR | échecs silencieux | Toutes inscrites |
| `announcement` écrasé, faux pour M1 | MINEUR | échecs silencieux | Premier gardé ; `None` si M1 |

Vérifié sans constat par les auditeurs :
- tirage sans fuite (graine = SHA-256 du recensement), `slugs_famille` correct ;
- aucun alias dans les 5 fichiers de trades ;
- ordre de A5 sans connaissance de Thin ;
- identifiants uniques (180 985 lignes), sans doublon de jonction ;
- `_can_signal`, voisinage de synchronie et reprise après SIGTERM corrects.

Écart de ma part, à signaler : j'ai tenté de vider `registre/` pour retirer la ligne de mon premier contrôle synthétique. Le garde-fou de Claude Code l'a refusé, rien n'a été exécuté. Le registre garde donc cette ligne et une seconde, toutes deux synthétiques et antérieures au gel.
