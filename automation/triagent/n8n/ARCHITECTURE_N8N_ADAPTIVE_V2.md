# TriAgent × n8n — version événementielle (V2)

**Statut : livrable de conception et d'import ; ni le bridge local ni le workflow n'ont été exécutés sur le Mac de l'utilisateur depuis cette conversation.**

## Différence majeure avec V1

La V1 interrogeait le broker chaque minute et exécutait une réconciliation toutes les deux minutes. Les requêtes HTTP locales ne déclenchaient pas nécessairement de nouveaux appels IA, mais ce design pouvait laisser croire qu'une mission d'une heure devait être interrogée à intervalles fixes.

La V2 se réveille **immédiatement quand un événement arrive** via `POST /webhook/triagent-v2-wake`. Un simple contrôle local, sans LLM, intervient toutes les **15 minutes**, notamment après panne et redémarrage. En cas de résultat Claude/Grok, le broker sauvegarde la preuve, crée une tâche d'audit GPT et publie l'événement ; n8n autorise ensuite une seule exécution du job via un bail atomique. Le broker gère la durée des processus en dehors du workflow n8n.

## Deux boucles indépendantes

1. **Collecte et alerte rapide** : le collecteur TriAgent reste chargé des transactions Polymarket, événements Polygon, pistes de funding, reorg, service labels. Latence de collecte initiale envisagée : 15 à 60 secondes selon limites et lag observés ; déclenche une notification provisoire sans attendre les LLM.
2. **Recherche longue** : n8n orchestre Claude / GPT via Codex CLI / Grok CLI, en sessions neuves. Durée par tâche de quelques minutes à plusieurs heures. Le processus rapporte sa fin par événement ; il n'est pas rappelé chaque minute.

## Prévision des durées

Durées observées par fournisseur et type de tâche, P50/P90 (P99 après échantillon suffisant), estimation avec incertitude. Le temps prévu ne doit pas provoquer de nouvelles requêtes. Le heartbeat est purement local ; un job dépasse sa médiane sans être relancé. Les actions de contrôle automatique sont à idempotence forte.

## La preuve prospective

Les mécanismes historiques (wallets créés ensemble, funding, synchronisation, dépôts d'exchange, basculements directionnels) servent à définir des hypothèses. Pour chaque alerte à l'instant T, n'utiliser que les données effectivement **observées au plus tard à T**. Exemple : une adresse Coinbase identifiée par les retraits postérieurs à la résolution ne peut pas entrer dans un score censé avoir détecté le réseau avant son premier pari. Mesurer couverture, alertes/1 000 wallets, comparateurs, placebos, délai avant première position et délai avant événement public. Ne jamais confondre risque d'anomalie et preuve d'insider trading.

## Connexions nécessaires

Le JSON suppose un broker local authentifié sur `127.0.0.1:8791`, qui doit être développé/validé par Claude Code. Les credentials n8n ne sont pas inclus. Le workflow est désactivé jusqu'à installation. Le GPT directeur est **Codex CLI connecté au compte ChatGPT** : ce n'est **pas** une fenêtre ChatGPT Browser automatisée. Grok CLI nécessite de vérifier l'authentification et les capacités. La collecte de transactions publiques Polymarket ne nécessite pas de clé selon la documentation Data API v2.

## Ce qui est livré

- `TRIAGENT_N8N_ADAPTIVE_V2.json` : workflow n8n de 20 nœuds, routeur événementiel et rattrapage local 15 minutes ; inactif par défaut.
- `PROMPT_CLAUDE_CODE_N8N_ADAPTIVE_V2.txt` : cahier des charges et mission d'implémentation testable.
- `ARCHITECTURE_N8N_ADAPTIVE_V2.md` : document de référence et limites.

Aucun appel aux modèles et aucun test de production n'ont été effectués pour le nouveau workflow dans cette conversation. Vérification actuelle : schéma JSON lisible, liens entre nœuds cohérents, IDs uniques ; la compatibilité finale dépend de la version n8n installée et de la présence du broker.