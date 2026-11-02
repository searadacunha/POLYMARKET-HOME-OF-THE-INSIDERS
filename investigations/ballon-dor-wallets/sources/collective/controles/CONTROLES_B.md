# Contrôles, partie B

`ana_30_retro.py` réutilise `signals.decisions` (contrôlée dans `CONTROLES.md`). `group_stats` est contrôlée par un test ad hoc sur une petite table au moment de son ajout : 3 wallets achetant le même token à 60 s d'écart donnent 3 paires à 5 min, 1 token partagé, et une part de 24 h égale à 1. `ana_11_seal.py` refuse de sceller deux fois.
