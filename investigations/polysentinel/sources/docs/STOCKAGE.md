# Stockage v2 et exploitation bornée — 27/10/2026

La source opérationnelle reste `data/polysentinel.sqlite3`. `contents` partage les contenus exactement identiques, compressés zlib, par SHA-256 des octets non compressés. `object_refs`, `history_refs` et `response_refs` gardent séparément identifiants, sources, paramètres, statuts et dates. A → B → A conserve trois observations. `trade_index` sert la sélection temporelle et l'ancienneté connue.

Les vues `objects`, `history` et `responses` préservent les colonnes v1. Un lecteur SQLite externe doit enregistrer cette fonction, sans dépendre du décodeur de production :

```python
import sqlite3, zlib
cx = sqlite3.connect('file:data/polysentinel.sqlite3?mode=ro', uri=True)
cx.create_function('payload_text', 1, lambda b: zlib.decompress(b).decode('utf-8'), deterministic=True)
```

`immutable=1` est réservé aux copies fermées et immuables. Une base ouverte se sauvegarde par l'[API SQLite backup](https://www.sqlite.org/backup.html). Ne jamais supprimer manuellement WAL/SHM ; suivre la [documentation WAL](https://www.sqlite.org/wal.html).

## Migration et récupération

`tools/migrate_storage.py` exige LaunchAgent arrêté et verrou d'instance. Il exécute `wal_checkpoint(TRUNCATE)`, passe en journal DELETE, construit un candidat distinct, vérifie intégrité/références puis toutes les lignes des cinq tables logiques par SHA-256 ordonné. Aucun échange si les empreintes diffèrent ; source conservée, aucune purge ni VACUUM. Une cible incomplète ne doit jamais être installée. Après un arrêt machine pendant substitution, arrêter la supervision et contrôler fichiers/empreintes avant restauration.

Preuves : `evidence/review_20261027/migration.json`, `continuity.json` et les contrôles transactionnels après migration/reprise. Les sauvegardes sont en `.sqlite3.gz`. `backup_compression.json` donne tailles, SHA-256 décompressés et chemins récupérables des copies brutes dans la Corbeille. **État historique de la revue à20:15 UTC : ces doubles occupaient encore le disque. Contrôle de la poursuite à20:33 UTC : le dossier de Corbeille indiqué est absent, cause inconnue; aucune suppression par cet agent. Les deux gzip restent présents et revérifiés.** Déplacements inscrits dans `~/FILE_INDEX.md`.

Les scripts historiques attendent `baseline.sqlite3` ou `cutover_v1.sqlite3`. Pour les rejouer, décompresser la sauvegarde nécessaire avec suffisamment d'espace libre, puis vérifier son SHA-256. Ne jamais écraser la base vivante. Le code original est dans `evidence/releases/pilot-20261027T182643Z-source.zip`.

## Quota, réserve et pause

Le quota reste **5 000 000 000 octets**, la réserve **10 000 000 000 octets libres**. Le périmètre moteur/réseau/exports comprend tout le projet sauf `.venv` et `.git` : SQLite/index, WAL/SHM, preuves, sauvegardes, rapports, logs, caches, temporaires et métriques. Calcul par fichier : maximum de taille logique et `st_blocks × 512`. Les liens symboliques ne sont pas parcourus.

L'admission réserve trois fois le plafond d'une réponse plus 36 Mo : **60 Mo** dans la configuration courante, pour brut/normalisation/index/WAL et télémétrie. C'est un garde applicatif, pas un quota système : expansion d'une opération et écritures d'autres programmes ne sont pas garanties octet par octet. Aucun plafond n'a été relevé.

En pause, les cycles et heartbeats n'ajoutent plus de lignes SQLite. `metrics/heartbeat.json`, remplacé atomiquement, distingue processus actif et collecte suspendue. Les ressources sont réévaluées et permettent la reprise automatique. Enrichissements réduits près des bornes ; aucune purge automatique des preuves. Logs applicatifs : cinq fichiers de 5 Mo ; métriques : deux fichiers de 5 Mo. Sorties launchd comptées dans le quota, vides à la revue, sans rotation indépendante.

## Collecte et mesures

Les réponses HTTP identiques partagent leur contenu, avec références d'observation distinctes. Les lignes antérieures au cutoff ne sont plus normalisées en `trade` mais restent dans les réponses brutes. Les nouveaux flux gardent un plancher initial durable : un marché dormant ne réadmet pas son historique au deuxième passage. Les parcours existants gardent leur périmètre. L'identité API conserve signature complète et occurrence ; **jamais le seul hash de transaction**.

Rapports quotidiens au plus toutes les cinq minutes, suspendus en pause ; versions distinctes de dossiers conservées. Flux : dernière fenêtre, réussite, retard, pages/plafonds et lacunes. Une réponse sans trade admissible reste différente d'une absence de collecte.

Le processus launchd mesure le stockage toutes les cinq minutes sans session d'agent. Lectures SQLite bornées à dix secondes, erreurs explicites, sortie tournante `metrics/runtime.jsonl`. Tailles logiques, blocs alloués, tables/index et E/S du processus sont séparés. Les E/S ne sont ni la croissance des fichiers ni les écritures physiques exclusives du SSD. `dbstat` et payloads sont déjà dans SQLite : ne pas les additionner à sa taille.

Fenêtres observées et limites : `evidence/review_20261027/REPORT.md`. Aucune stabilité sur 24 heures n'est attestée.

## Enrichissements et politique macOS

La configuration du 27/10 limite les enquêtes automatiques à une par 600 secondes, contre deux par cycle auparavant ; une demande manuelle reste prioritaire. C’est une réduction explicite de la couverture des historiques et enrichissements, sans purge des preuves actives. Les budgets de catalogue et dix marchés par cycle restent inchangés.

Le LaunchAgent passe de `ProcessType=Background` à `Standard`, en gardant `Nice=5`. Le ralentissement a été reproduit sur les mêmes entrées, puis séparé de Nice seul ; voir `evidence/review_20261027/performance/DIAGNOSTIC.md`. Le mécanisme de placement des cœurs et la consommation électrique n’ont pas été mesurés.

## Poursuite de la collecte continue du 27 octobre

Les dossiers ne sont plus enregistrés deux fois pour ajouter leur nom de rapport. Le nom dérivé est exclu du hash de son propre contenu; un export strictement identique est laissé intact. Les preuves et versions existantes ne sont pas purgées. Les nouvelles observations de catalogue restent datées même lorsqu'une valeur ne change pas : leur fraîcheur est une information conservée.

La file réserve au moins la moitié des dix places à l'exploration générale, avec alternance nouveaux/revisites. Les marchés expirés sont exclus explicitement de la surveillance préalable. Le mode réduit borne aussi le catalogue (au plus deux pages configurées, taille25) et deux interrogations individuelles par cycle. Le flux global garde ses filtres. Les enquêtes automatiques se concentrent sur les annonces documentées et gardent le délai minimal600s; un scan tournant prévient la famine derrière les exclusions.

Le tableau de bord affiche les fenêtres autonomes successives en séparant base, WAL, rapports, logs et nouveaux trades. Les mesures d'une reprise, les blocs APFS alloués et les octets logiques ne sont pas des économies imputables au code. Voir `evidence/continuous_20261027/REPORT.md`.

## Complément du 27 octobre, après 21:17 UTC : E/S temporaires

Les fichiers durablement présents n'expliquaient pas les quelque 4 Go d'E/S attribuées au processus sur quinze minutes. Le tri de la sélection courante des trades a été isolé : environ 235,90 Mo écrits par requête, sur une connexion en lecture seule. `CROSS JOIN` place maintenant le parcours temporel avant la décompression des objets, sans nouvel index ni migration. Sur le même instant et 50 000 lignes strictement identiques en ordre et contenu : zéro écriture mesurée dans le test isolé. Les tests d'ex æquo et de dates futures passent ; la branche historique n'a pas changé.

Preuves : `evidence/continuous_20261027/storage/QUERY_REVIEW.md` et `query_benchmark*.json`. Mesure du service réel : `evidence/continuous_20261027/query_live_windows.json`. Le taux de croissance logique, les blocs alloués et les E/S sont trois métriques distinctes. Le correctif ne promet pas zéro écriture du service ni zéro tri temporaire pour toute distribution future de dates.

Le quota de projet ne constitue pas un quota système : un temporaire SQLite hors du dossier peut consommer de l'espace pendant le calcul sans apparaître dans son inventaire final. Ce coût a été réduit sur le chemin courant démontré ; la réserve de 10 Go et la surveillance périodique restent nécessaires. Les plafonds n'ont pas été relevés et aucune preuve n'a été purgée.



## 2026-10-29 13:51 UTC — Budget et suivi par cycle

Voir `evidence/storage_20261029/REPORT.md`. La perte d’environ 3,25 Go du volume a pour cause dominante six vidéos Canelo téléchargées dans un autre projet (3,617 Go, moins les 363,5 Mo économisés auparavant). Nettoyage externe en attente d’autorisation ; aucun seuil abaissé.

Les nouveaux rapports quotidiens portent `-z2` : JSON complet gzip et HTML compact, anciens rapports préservés. `storage_delta` dans chaque cycle/health engine mesure les nouveaux corps compressés, références, réponses et clés de trades, le delta de taille du projet et les marges ; ce ne sont pas des octets physiques SSD. Les nouveaux rowid bornent le travail sans rescanner les anciens contenus. Les écritures finales de métrique et rapport sont hors du compteur des corps, mais incluses dans les fenêtres autonomes des fichiers.

Les ressources partagées du Mac et les preuves qui s’accumulent rendent impossible une surveillance illimitée garantie sur ce seul disque. Conserver quota 5 Go et réserve effective 10,060 Go. Une capacité externe ou une rétention/archivage approuvé sera nécessaire si la croissance persiste. Aucun détecteur modifié.
