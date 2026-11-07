# Polymarket TriAgent — prototype autonome

**Statut : prototype testé localement en `dryrun`, pas déployé et pas testé avec des clés réelles.**

Service de recherche *read-only* pour [`searadacunha/Polymarket-Home-of-the-Insiders`](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders). Aucune modification du README historique, aucun trade, aucun envoi de secrets à une IA, aucun push ou merge automatique. Les résultats restent dans SQLite privée en attendant une contre-vérification.

## Ce que fait le prototype

- Deux workers indépendants : **Claude Code** (`claude --bare -p` sans `--resume`, contexte neuf à chaque tâche) et **Grok** (`xAI API` + X Search, ou le véritable **Grok Bot** via une routine webhook).
- **OpenAI API** reçoit chaque résultat, tente de le réfuter, distingue preuve et hypothèse et n'autorise au maximum que deux nouvelles missions si la nouveauté est réelle. Un `novelty_key` unique, une profondeur maximale et un budget de tâches empêchent les boucles infinies.
- Un planificateur OpenAI réévalue les lacunes documentaires toutes les 12 h (configurable), sans inventer des missions pour occuper les agents.
- Un collecteur de veille interroge l'API publique Polymarket **`/v2/activity`** pour les adresses des 38 comptes Iran déjà publiés dans le dépôt. Il crée des pistes uniquement sur de **nouvelles** positions BUY dépassant un seuil, avec bootstrap sans alerte historique. Les candidates ne sont pas des preuves d'initié.
- SQLite WAL conserve tâches, résultats, évaluations, marqueurs de nouveauté et dédoublonnage après redémarrage.
- Le callback Grok Bot exige un secret distinct et un nonce de mission. Un accusé de réception webhook **ne signifie pas** que l'enquête est terminée.

**Limites déterminantes :** le collecteur actuel surveille une cohorte connue, pas tout Polymarket ; il ne collecte pas encore les financements pré-trade de nouvelles adresses inconnues et ne traverse pas automatiquement les bridges/exchanges. Pour anticiper des comportements avant leurs premiers trades, il faut ensuite ajouter un indexeur Polygon/Ethereum/TRON, un graphe de flux, des références temporelles et un détecteur avec contrôles/mesure de faux positifs. Un address label d'exchange ne donne pas l'identité civile du client.

## Mise en route (serveur Linux toujours allumé)

```bash
# Pré-requis : clone local du repo à l'emplacement REPO_PATH, Python >= 3.11,
# CLI Claude Code installée et accessible avec une clé Anthropic API.
cd /srv/Polymarket-Home-of-the-Insiders/automation/triagent
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
# Modifier .env avec des secrets API réels, mode live et chemins absolus.
set -a; . ./.env; set +a
PYTHONPATH=. python -m unittest discover -s tests -v
uvicorn triagent:app --host 127.0.0.1 --port 8765 --workers 1
```

Pour un mode sans coût, laisser `RUN_MODE=dryrun` : le système enchaîne les trois missions initiales avec des résultats simulés et ne déclenche aucune recherche facturable. Pour un fonctionnement réel, placer `RUN_MODE=live` et configurer `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` et, pour `GROK_MODE=xai_api`, `XAI_API_KEY`. Vérifier l'accès à `OPENAI_MODEL`, `XAI_MODEL` depuis vos comptes. **Les abonnements ChatGPT/Claude/Grok Bot ne remplacent pas automatiquement les crédits API.**

Ne pas utiliser `--reload` ou plusieurs workers, afin de ne pas multiplier les boucles. Déployer avec `systemd`/superviseur et un redémarrage automatique, idéalement sur un VPS. Pour Grok Bot, exposer **uniquement** `/api/grok-complete` en HTTPS via un reverse proxy protégé ; conserver `/health` et les fichiers SQLite derrière le réseau local. Restreindre les droits sur le dossier `private-state`. Installer les seuils de dépenses/rate limits **chez chaque fournisseur** : `MAX_JOBS_DAY` limite les appels, pas les euros totaux de tous les modèles.

## Relier le véritable Grok Bot

1. Dans Grok Bot, créer une routine **déclenchée par webhook**. Elle doit utiliser les intégrations X publiques et GitHub en lecture seule.
2. Copier son URL et sa clé dans `GROK_BOT_WEBHOOK_URL` et `GROK_BOT_WEBHOOK_KEY`, mettre `GROK_MODE=bot`.
3. Donner au Bot l'URL publique `PUBLIC_CALLBACK_URL` et stocker **séparément, dans son gestionnaire de secrets**, `GROK_CALLBACK_SECRET` (également présent dans la configuration du serveur). Ne pas mettre ce secret dans le prompt GitHub, dans la routine en clair ou dans le JSON de déclenchement.
4. Instruction de routine recommandée :

> Lors de chaque webhook, lire `job_id`, `nonce`, `task` et `completion_url`. Effectuer **une seule** enquête historique X par mission ; restituer les sources primaires, URLs exactes, horodatages, hashes, objections et vérifications à mener. Ne publier aucun résultat directement dans main. Terminer par un POST HTTPS JSON vers `completion_url` avec les champs `job_id`, `nonce`, `summary`, `primary_sources` (liste), `transaction_hashes` (liste), `unresolved` (liste), `proposed_tests` (liste) et le header `Authorization: Bearer <secret protégé>` obtenu par le mécanisme de secrets sécurisé. En cas d'échec d'envoi, conserver le fichier de résultat et signaler l'échec ; ne jamais prétendre qu'un POST 200 est une preuve de validation scientifique.

Le webhook de routine confirme seulement le *démarrage*. La synchronisation retour dépend du POST effectué par le Bot ; si son environnement ou ses autorisations ne le permettent pas, utiliser `GROK_MODE=xai_api` pour une orchestration 100 % API. Le véritable Grok Bot conserve par ailleurs son contexte durable : le programme lui fournit une **mission bornée**, mais ne garantit pas une conversation Grok Bot entièrement neuve.

## Méthode et sécurité

- Chaque session Claude Code est **nouvelle**, en mode `--bare` et avec outils **lecture seule** (`Read,Glob,Grep`). La politique `AGENTS.md` et `METHODOLOGY.md` est incluse dans le prompt à partir du dépôt local. Aucun modèle n'a de commande d'écriture Git ou de clé d'échange.
- Toute observation d'un grand BUY est **une piste brute**. Une réconciliation on-chain et des comparateurs représentatifs sont nécessaires avant un constat. Une réutilisation de service ne prouve pas propriété commune.
- Les recherches Grok X doivent fournir des **liens/IDs/timestamps originaux** : la répétition du même tweet ne constitue pas une corroboration indépendante.
- Les données tierces et les profils X ne sont pas recopiés dans le dépôt public ; pas d'auto-publication. Les fichiers sont stockés dans SQLite privée avec sauvegardes chiffrées recommandées.
- Les secrets restent dans les variables d'environnement du serveur / vault Grok. Mettre les accès API en lecture seule ; ne pas accorder de clé privée de wallet.
- Erreurs et tâches interrompues restent auditables. Ne pas relancer automatiquement une tâche incertaine, qui pourrait être facturée deux fois.

## Suite pour une version production

1. Connecteurs Polygon/Ethereum/TRON + index de funding et mouvements de stablecoins, suivi des Relay/deBridge ordres déterministes, services mutualisés et adresses d'exchange ; aucune attribution KYC.
2. Indexeur universel d'événements Polymarket (**Data API v2** et **PolyBolt**, pas ancien RTDS), carnet d'ordres, premiers fills, wallet age et timestamps de market listing ; attention à la distinction order placement/fill.
3. Graphe temporel avec nœuds wallet/proxy/exchange-service et arêtes typées `DIRECT`, `BRIDGE_ORDER`, `SHARED_DEPOSIT`, `SERVICE_ONLY`, `CORRELATION`; évaluation de la rareté par population comparable.
4. Alertes seulement après calibration hors échantillon : précision, FPR par 1 000 comptes, coût de fausse alerte, validation temporelle et tests placebo. Réévaluer après changements de protocole.
5. Publications de **draft PRs** séparées pour les hypothèses vérifiables, replay systématique et CI `scripts/check_publication.py`, sans auto-merge des conclusions non prouvées.

Sources techniques : [Claude headless](https://code.claude.com/docs/en/headless), [OpenAI Responses](https://developers.openai.com/api/docs/guides/structured-outputs), [xAI X Search](https://docs.x.ai/developers/tools/x-search), [Grok Bot routines](https://docs.x.ai/grok-bot/skills-routines-and-automations), [Polymarket Wallet Activity v2](https://docs.polymarket.com/trading/wallet-activity), [Polymarket Real-Time](https://docs.polymarket.com/market-data/realtime-data).
