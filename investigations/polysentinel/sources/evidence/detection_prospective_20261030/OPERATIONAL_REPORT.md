# Évaluation prospective locale, 30 octobre 2026

## Réponse établie

La chaîne producteur → lecture SQLite → copie de preuve → émission locale durable → scellement local a fonctionné sur de vraies nouvelles observations d'alertes. Elle ne démontre pas une capacité de prévision ni une information privilégiée.

Le producteur et ses seuils n'ont pas été modifiés. `tools/prospective_eval/sidecar.py` lit la base en mode lecture seule, sans réseau ni notification externe. SHA-256 de cette version : `ca0e98009fa2a07222885665722014c7aa87b551922716e6d52676e3a2e8bfef`. Les empreintes décrivent les fichiers sur disque, pas les modules déjà chargés dans la mémoire du producteur. Les contrôles techniques et leur audit sont distincts de la preuve live.

## Première preuve live

Époque `b09270a7-9090-4fb8-b67b-09a78ac47b5f`, initialisée le 30 octobre à 12:33:17.644729 UTC, curseur initial 650191. Les observations antérieures au curseur initial sont exclues ; de nouvelles observations de dossiers existants restent admises.

Le lot `../prospective_eval/00000001/data.json` conserve deux observations d'alertes du marché événement 770450, « Fed Decision in December? » :

| Dossier | Score exploratoire | Familles/règles | Lacunes locales conservées |
|---|---:|---|---:|
| 8abe07a6f0137fa807e35804 | 2 | entrées synchronisées et changements de taille habituelle du wallet | 15 |
| a37f3cacc6d8a136c04b5805 | 2 | concentration d'achats et entrées synchronisées | 18 |

Le nombre de règles répétées n'est pas le score : celui-ci compte les familles natives. Ces deux dossiers ne constituent pas deux cas indépendants validés, et leurs wallets ne sont pas qualifiés d'initiés. Copie, automatisation, information publique, arbitrage et censure des historiques restent des explications possibles.

Calcul source :12:33:27.169311 UTC. Lecture sidecar :12:34:36.342786 UTC. Le reçu atteste persistance après fsync à 12:34:37.390794, émission locale après publication/fsync du dossier à 12:34:37.390892, scellement du fichier de données à 12:34:37.390955. Le reçu est achevé ensuite. SHA des données : `588be4e03327187338d636357479f5000e10e664d0b3a3d40bf6d7a0d00b1be1`.

Le calendrier officiel [Federal Reserve](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) prévoit la réunion les 8–9 décembre 2026. La description de l'événement conservée vise cette décision de taux. L'émission précède donc la réunion programmée. **La publication effective future de sa décision n'a pas encore été observée ; le premier instant public pertinent demeure inconnu.** Les données scellées (`captures[].public_knowledge`), et non les reçus, conservent `first_public_at=null` et `UNKNOWN_REQUIRES_SOURCED_REVIEW`. Cela ne prouve pas l'absence d'autres informations déjà publiques. Copie du calendrier : `fomc_calendar.html`, métadonnées dans `fomc_calendar_receipt.json`.

## Fonctionnement périodique et arrêt protecteur

Le LaunchAgent `~/Library/LaunchAgents/com.benjamin.polysentinel-prospective.plist` lance une lecture toutes les 60 secondes, priorité basse. Il réécrit `latest_status.json`, sans log cumulatif. Un passage a effectivement refusé sous le plancher 10,06 Go ; après remontée spontanée de l'espace, des captures automatiques ont repris. Aucune suppression ni modification de seuil n'a servi à les forcer.

La preuve intermédiaire `operational_proof_1300.json` répertorie les reçus, leurs SHA et drapeaux `UF_IMMUTABLE`, les empreintes du code et du lanceur, ainsi que l'état live. Ses 52 captures sont 52 observations d'alertes, pas 52 wallets uniques ni 52 prédictions. Le recompte documentaire des lots 00000000 à 00000006 donne 18 dossiers, 16 wallets et 13 événements ; n effectif statistique indépendant non établi. Une exécution réussie de `sidecar.py verify` est conservée dans `verification_session_receipt.json`. Le refus réel est conservé dans `refusal_session_receipt.json` : extraits exacts du journal natif local, copiés ultérieurement avec ligne et SHA, sans ancrage tiers. `verify_and_launchd_1337.json` conserve également le lancement périodique observé ; son appel simultané de verify a été refusé par le verrou d’exécution, distinctement du contrôle réussi antérieur. Le service source est revenu en mode normal ; les nouveaux trades sont vérifiés séparément.

## Limites et évaluation ultérieure

Les données et reçus sont en 0400 et protégés par `uchg`, avec chaîne de SHA et checkpoint. Le propriétaire peut retirer ces protections ou reconstruire la chaîne ; pas d'horodatage tiers, de sauvegarde indépendante ni d'impossibilité de rollback coordonné. L'horloge est locale.

Les entrées copiées sont celles disponibles au moment de la lecture du sidecar, pas la photographie exhaustive du calcul initial. Certaines réponses brutes restent seulement référencées par SHA dans la base ; leur future disparition limiterait une reproduction. Une alerte créée puis supprimée entre deux lectures peut échapper au sidecar. Les omissions et erreurs sont distinctes ; une erreur de lecture ou capture avant publication n'avance pas le curseur de ce nouveau lot ; la récupération d'un lot déjà scellé peut avancer un checkpoint antérieur.

Plafonds :20 Mo au total,1 Mo pour data.json par lot, reçu et métadonnées en sus, dix observations au plus par lecture ; aucune purge ou extension automatique. Le plancher disque et le quota projet restent appliqués. Le stockage actuel ne permet pas une promesse de fonctionnement continu. Au plafond, le dernier statut indique un refus et les preuves sont préservées.

Pour chaque événement futur retenu, conserver séparément la preuve publique sourcée de la première annonce pertinente, puis comparer son heure à `emitted_at`, pas à `calculated_at`. Les inconnus restent inconnus. La campagne n'a encore ni vérité terrain indépendante, ni horizon terminé, ni précision/rappel/taux de faux positifs estimables.
