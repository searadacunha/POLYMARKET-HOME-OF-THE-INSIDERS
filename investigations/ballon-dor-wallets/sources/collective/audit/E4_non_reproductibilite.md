# E4 : non-reproductibilité documentée

**Constat, 2 nov. 00:52 UTC.** La reproduction de la partie A en copie fraîche donne des empreintes identiques au sceau pour E1, E1G, E2, E3 et le placebo. E4 diffère : 12 puis 12 paires à D2, 34 puis 33 à T_FIN, 25 paires communes sur le haut de liste à T_FIN (`audit/REPRODUCTION.json`).

**Cause.** `ana_overlap_core.py` parcourt des ensembles de chaînes. Leur ordre dépend du hachage aléatoire de Python, donc le tirage Curveball change d'une exécution à l'autre pour une même graine.

**Correctif.** Amendement 002, décidé par Benjamin le 2 nov. : `ana_overlap_core_v2.py`, ordre canonique partout, graine passée explicitement, trois graines (20261101, 20261102, 20261103), sortie `derived/A_E4_v2.json`.

**Vérification.** Sortie identique à l'octet sous PYTHONHASHSEED 1, 2 et 3 (`audit/REPRO_E4V2.json`).

**Ce qui reste.** Le nombre de paires au-dessus du nul varie avec la graine : 11, 11, 12 à D2, 31, 25, 34 à T_FIN. Le maximum du nul sur 200 tirages est bruité : il ne faut donc pas lire ce chiffre au point près. La lecture stable est ailleurs : aucune paire n'implique un compte nommé, pour aucune graine ni date (`exploratoire/E4_v2_summary.json`).

**Conservé sans modification.** `derived/A_E4.json`, le sceau `derived/A_seal.json`, le code d'origine. E4 v2 est écrit après lecture des résultats : il n'a aucune valeur d'aveuglement et n'entre pas dans le verdict de la partie A.
