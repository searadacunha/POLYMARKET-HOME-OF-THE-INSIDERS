# Contrôles avant gel, 1er novembre 2026

`code/ctl_replay.py` (synthétique, sortie `controles/ctl_replay.json`) : nul muet, moyen en score 1 sans priorité, fort prioritaire à l'heure attendue, marché fermé bloquant, plafond d'analyse effaçant la rupture, synchronie à trois wallets, arrivées tardives, événement sans catalogue, échéance déclenchant une réévaluation, oracle partiel, rotation (statut de résolution absent, littéral isolé), plancher d'historique commun, champs d'identité retirés. Oracle complet à chaque tick des fixtures, sans écart.

`code/ctl_collecte.py` (réel, sortie `data/collecte_controles.json`, sans aucun score) : rappel du recensement sur la famille 184/184, sur les témoins 385/385, contre la production sur trois jours entiers 14 693/14 693 (41 lignes vues par le recensement seul) ; `/trades` borné contre `/v2/trades` 1 722/1 722 ; aucune occurrence multiple ; 604 lignes rejetées par le normaliseur.

Ces contrôles prouvent la mécanique et la collecte. Aucune puissance, aucune précision ni aucun rappel de détection n'en découle.
