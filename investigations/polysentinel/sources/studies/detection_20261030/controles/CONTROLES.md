# Contrôles avant gel

Les seuils et le noyau de production restent inchangés. Dernières sorties replay_synthetic_controls_v3.json et replay_fast_controls_v3.json : PASS. Les multiples passes et benchmarks ne sont pas un échantillon indépendant ; leur inventaire complet figure dans replay_execution_ledger.json et le registre.

Nul : un wallet avec petit achat, aucun signal/priorité. Moyen : un wallet avec grand premier achat, signal exposition et aucune priorité (score1). Fort : trois wallets synchronisés, trois comportements/priorités conditionnelles, pour chaque délai0/60/300/900. Les tests de calendrier utilisent plusieurs graines ; le cache a été comparé au noyau complet sur24graines et4délais, avec limites, fills à plusieurs dates, arrivées/expirations et classement. Les dates futures et doublons contradictoires sont refusés ; observed_at source inchangé.

Les six contrôles finaux de features_synthetic.json conservent zéros et inconnus, vérifient les références internes, la conjonction, le prixnul, les identités absentes et le label non résolu. La première passe avait cinq groupes, avant ajout du cas prixnul.

Aucune puissance empirique, précision ou rappel n'est mesuré par ces contrôles. Les timings de benchmark servent uniquement à prévoir CPU, jamais à valider la détection. Les comptes synthétiques ne sont liés à aucune adresse réelle.

Dernière passe avant gel : input_controls_v4.json sept contrôles PASS (scellement vide/partiel refusé, sorties existantes préservées) ; features_synthetic_v3.json sept contrôles PASS (sans pair, fréquences inconnues). La tentative input_controls_v2.json vide correspond au refus stockage documenté dans input_controls_v2_refusal.json, pas à un succès. Les passes V3/V4 et le contrôle adverse indépendant256 comparaisons sont dans le registre. Aucun rejeu réel exécuté avant ce gel.
