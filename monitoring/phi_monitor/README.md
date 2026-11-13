# phi_monitor

Code de surveillance non suivi, fourni par le propriétaire le 13 novembre 2026 (archive `early-detection-monitoring-untracked`, SHA-256 `0da66d9bb8baa6d797eca812b66a380de7ac236f904d4880d464ecaba0ec91d8`). Les seuils de `ignition.py` et `tapefeat.py` ne sont pas modifiés.

`collect.py`, `net.py` et `chain.py` savent interroger le réseau. Cette passe ne les appelle pas. `chain.py` ne décode que `OrderFilled` v2, donc pas les exécutions d'avant le 28 avril 2026.

Un résultat de ce module est un motif dans des données publiques. Il ne nomme pas une personne et ne conclut pas à une information non publique.
