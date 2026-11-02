# Conservation prospective — contrôle du 30 octobre 2026

État mesuré à 2026-10-30T14:16:28.558975+00:00. Source: `prospective_snapshot.json`, vérification de toute la chaîne sous le verrou existant, sans interrogation réseau ni modification des données source.

## Conservation constatée

- 56 reçus (activation comprise), 17,878,016 octets comptabilisés sur **20 000 000**, curseur 677661, aucun checkpoint en attente.
- Chaîne de SHA-256, droits lecture seule et drapeaux macOS `uchg` vérifiés. Les 26 empreintes de sources de l'époque correspondent aux fichiers actuels, dont `sidecar.py` et `polysentinel/signals.py`.
- 275 observations distinctes de lignes source, regroupées en 41 dossiers (wallet-événement), 35 wallets et 21 événements. **234 observations sont des répétitions de dossiers déjà conservés.**
- Les 275 empreintes matérielles distinctes indiquent des changements d'état source, pas des alertes indépendantes. Le nombre statistique d'alertes indépendantes n'est pas établi; un même événement, wallet ou financement peut relier plusieurs dossiers.
- 265/275 observations concernent un dossier créé avant l'activation. L'époque conserve les nouvelles observations après activation; elle ne transforme pas ces dossiers en découvertes nouvelles.
- Version déclarée des signaux: `exploratory-1.2`. Chaque lot conserve les empreintes de modèle/configuration dans `next_state`, les scores et raisons dans `source_alert.payload`, les données ciblées disponibles dans `inputs`, les manquants et les compteurs de recherche.
- 275/275 observations ont `first_public_at=null`; 275/275 comportent des entrées manquantes. Aucune performance prédictive ni antériorité à la première annonce publique n'est déduite de ces comptes.

## Horloges et portée de la preuve

`observed_by_sidecar_at` date la lecture; `persisted_at` suit fsync du contenu; `emitted_at` suit publication et fsync du dossier parent; `sealed_at` suit le scellement du fichier de données. `calculated_at` et `source_alert.observed_at` ne sont pas une preuve indépendante d'heure de commit ou d'émission.

L'horloge est locale et non ancrée. Le propriétaire peut retirer `uchg`; l'ensemble de la chaîne peut être remplacé par un propriétaire malveillant. La chaîne protège contre les altérations accidentelles et révèle une altération incohérente; ce n'est pas une immutabilité absolue. Les empreintes des sources sur disque ne prouvent pas la version chargée en mémoire par le service.

Le contexte est copié au moment de la capture, pas intégralement au moment du calcul original. Les comparateurs globaux et certaines réponses brutes restent référencés par hash sans être copiés. Une alerte source créée puis supprimée entre deux polls demeure indétectable. Un calendrier futur ne prouve pas l'absence d'information publique préalable.

## Surveillance de capacité activée

Fichiers nouveaux: `tools/prospective_eval/capacity_monitor.py` et `test_capacity_monitor.py`. Aucun changement de `sidecar.py`, de l'époque, du modèle ni du plafond.

Le monitor indépendant lit l'espace comptabilisé avec la fonction existante et l'état du LaunchAgent source. Il signale 80%, 90%, l'absence de place pour un lot maximal de 1 Mo plus réserve32 768 octets, les refus source, la disparition du service, le statut périmé au-delà de180secondes et les erreurs de lecture. Le statut vide reçoit seulement15secondes de grâce, car le shell du collecteur le tronque pendant l'exécution.

Il écrit hors du spool dans `evidence/prospective_monitor/`, toujours dans le quota du projet: `status.json`, `ATTENTION.txt`, `notification.json` et un verrou. Les fichiers transitoires sont remplacés atomiquement; chaque contenu est limité à16KiB. Le nouveau LaunchAgent tronque `last_run.txt` à chaque passage, sans log cumulatif. Le statut conserve le dernier incident après retour à la normale.

Une notification macOS locale est tentée lors d'un changement de catégorie d'alerte. Un échec est retenté après un délai minimal de900secondes. Un marqueur indépendant déduplique aussi les notifications lorsque le statut principal reste illisible; le refus demeure dans `ATTENTION.txt` et `last_run.txt`. Le code retour est conservé; il ne prouve pas que Benjamin l'a vue. Le monitor est un job séparé à60secondes: le refus ou l'arrêt du sidecar ne supprime pas le monitor.

**Au plafond, le sidecar conserve les preuves existantes et refuse la suite.** Le monitor rend cet arrêt explicite; il n'assure pas une conservation illimitée. Aucune purge, aucune hausse du plafond ni démarrage d'une nouvelle époque ne sont effectués. Le fichier `latest_status.json` du sidecar est déjà hors spool, donc hors du plafond20Mo, mais dans le quota général du projet; le monitor n'a pas modifié ce périmètre.

Activation effectuée à14:21:02UTC après relecture indépendante et corrections demandées. Le dossier de sortie a été créé avant le bootstrap, car la redirection shell précède Python. Preuves: `prospective_monitor_activation.json`, `prospective_monitor_first_run.json`. Premier passage:18 099 456octets, alerte90%, notification locale retournée avec code0; réception humaine non vérifiée. Le code de sortie1 du monitor signifie une alerte active, pas un crash. Deuxième passage réellement observé à14:22:03UTC, même alerte90%, sans nouvelle tentative de notification. Preuve: `prospective_monitor_two_runs.json`; 12288octets alloués au monitor à ce contrôle. Le LaunchAgent distinct `com.benjamin.polysentinel-prospective-monitor` est chargé à60secondes.

## Vérifications

Commande: `.venv/bin/python -m unittest discover -s tools/prospective_eval -p 'test_*.py' -v`.
**36 tests passent**, dont8 tests spécifiques de seuils/réserve, refus/service absent/statut périmé, fenêtre transitoire, notification dédupliquée et incident persistant, chemins dangereux/statut illisible, absence de modification du spool, délai de réessai des notifications et déduplication d'une erreur persistante de lecture du statut. Les28 tests existants du sidecar passent aussi. Les tests n'utilisent ni la base live ni de notification réelle. Sortie exacte: `prospective_monitor_tests.txt`.

Ces tests établissent les comportements logiciels contrôlés; ils ne prouvent aucune capacité prédictive.
