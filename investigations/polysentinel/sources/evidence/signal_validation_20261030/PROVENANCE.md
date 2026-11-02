# Provenance du détecteur et de l'alias — vérification du30octobre2026

Revue ciblée des journaux natifs, archives et sources par agent indépendant signal_provenance, lecture seule. Les dates ci-dessous sont celles des appels et de leurs retours réussis, pas uniquement des mtime.

| UTC,27octobre2026 | Trace | Portée |
|---|---|---|
|14:09:02.606|Session Claude `~/.claude/projects/-Users-benjamindacunha/b8021738-91d9-4454-bab2-56441d617ca4.jsonl`, ligne11 ; texte `docs/MISSION.md`, lignes7 et140–157|Mission déjà informée du Ballon d'Or et de familles de signaux.|
|16:56:03.298–.422|Session Codex root `~/.codex/sessions/2026/10/27/rollout-2026-10-27T16-51-07-01a17e45-d11a-77b0-abe6-457e9f914835.jsonl`, lignes95/98|Écriture réussie des seuils1000,20,2.|
|17:02:05.670 puis17:02:35.552|Session agent `~/.codex/sessions/2026/10/27/rollout-2026-10-27T16-56-37-01a17e4a-d973-7873-ba6b-aa9290817cdc.jsonl`, appels131/136, retours134/139|Première création réussie exploratory-1, concentration0,8, fenêtre24h, taille max(5×médiane,médiane+6×1,4826×MAD,1000). Tentative17:01:29 annulée, non comptée comme création.|
|17:50:22|Même session agent,424/428|Version1.1 : exclusion des marchés fermés/résolus/échus/publics.|
|19:13:01.048–.696|Session root1183/1187|Version1.2 : première activité connue hors plafond50000 ; seuils conservés.|
|22:03:15.391|Session root3932|Ajout de diagnostics/compteurs, sans changement de score ; version nominale1.2 conservée.|

Archives comparées :

- `evidence/releases/pilot-20261027T182643Z-source.zip` : noyau1.1 SHA256 `accda584e59de188c628a4979f8b4b356f4c550011cd462ec0eb05e83adfb1ef`.
- `evidence/releases/polysentinel-review-20261027-source-evidence.zip` et `evidence/continuous_20261027/dossiers/source_v12.zip` : noyau1.2 `cd103f41b9a0c17f313534e40cb9a6bf72edc20c91759efc28e99c7a5596732e`.
- Production et copie du rejeu : `45d1a5c0c109c573c4057269fb1783f768fc41da3973bb73d7e17a29b78ded90`. Diff avec archive1.2 limité aux diagnostics. Les seuils étudiés n'ont pas changé dans ces versions.

Conclusion documentaire : modèle construit après révélation du23octobre et à partir d'une mission mentionnant déjà l'affaire. Aucun réglage spécifique pour Thin n'a été trouvé dans l'historique ciblé ; cette absence ne prouve pas qu'aucune influence rétrospective n'existe. Le gel du30octobre avant exécution du rejeu ne remonte pas le modèle avant l'affaire. Le Ballon d'Or est un cas de développement/exploration, pas un test indépendant.

## Alias

`research_notes/PolySentinel et le Ballon 2026/labels_after/profile_search_0x8d3319c51520518ad01f6744486ceea29f376f5b.json` conserve une recherche Gamma par adresse complète, obtenue le30octobre à10:44:31.842532UTC : `pseudonym=Thin-Disclaimer-Life`, `proxyWallet=0x8d3319c51520518ad01f6744486ceea29f376f5b`. SHA du corps enregistré `2c20397124a15fd37fdd26842691bdc22edd841451feba73cafa06ce95bc7d71`. Requête : https://gamma-api.polymarket.com/public-search?q=0x8d3319c51520518ad01f6744486ceea29f376f5b&search_profiles=true&limit_per_type=10 .

`labels_after/labels.json`, lignes26–39, distingue le nom publié par Upside de cette résolution actuelle et donne `historical_alias_continuity_proven=false`. Recherche par nom approximative non utilisée comme preuve. Cette pièce n'établit ni le pseudonyme au13octobre, ni l'identité civile, ni la continuité du contrôle du wallet.
