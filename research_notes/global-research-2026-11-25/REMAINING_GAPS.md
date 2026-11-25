# Écarts qui restent

## Non résolus avec les données publiques de cette session

- Le déposant réel derrière `0xf2020…c423`. La route est mélangée. Un journal de transfert ne nomme pas le client de ChangeNOW.
- Les 39 portefeuilles Inca de juillet 2026 et les 152 portefeuilles de l'article Reuters. Sans adresses, prix d'entrée et population de contrôle, il n'y a rien à rejouer. Aller inventer des adresses serait une fabrication.
- Le contrôle même marché, même jour et même côté sur les 45 alertes. La table n'a aucun pair. Les carnets historiques au moment de l'alerte ne sont pas dans le dépôt. Le benchmark du 20 novembre disait déjà que la profondeur au moment de l'alerte ne se reconstitue pas après coup.
- Split, merge et conversion dans les ledgers de cas. L'identité de rachat testée ici est synthétique. Elle ne rapproche aucun solde réel nouveau.
- L'archive native Ethereum de W47, les ponts non enregistrés, et tout financement qui n'emprunte pas les adresses du registre. Le zéro vérifié ne couvre pas ces chemins.
- Une prévision qui battrait le prix après frais, glissement et liquidité. Aucun test de cette session n'en produit. Les familles déjà négatives dans `EDGE_VERDICT.md` ne sont pas relancées sur des carnets neufs.
- Le seau sportif 0,55–0,60 à sept jours cité comme prochaine mesure le 16 novembre. Le papier de 588 millions de transactions ne le teste pas. Cette session ne le teste pas non plus. Le laisser ouvert est plus juste que de le déclarer réfuté par une autre définition.

## Infrastructures privées

Chainalysis, TRM Labs, Elliptic, Arkham, Nansen et le rapport Inca complet ne sont pas des dépôts que l'on peut noter. Leur avance éventuelle sur le regroupement d'adresses et la couverture multi-plateforme n'est pas mesurable d'ici. Le billet Chainalysis du 7 mai 2026 ne donne pas un algorithme reproductible.

## Choix assumés

- Ne pas promouvoir W47 dans `investigations/weekly-funding-intelligence`. Ce dossier a son propre vérificateur et sa série figée. Le snapshot vit à côté, avec le hash du rapport dont il est la suite.
- Ne pas exécuter les détecteurs concurrents. Plusieurs exigent une clé, une base privée, ou un long collecteur. Les noter comme « non exécutés » vaut mieux qu'un rang fondé sur un README.
- Ne pas ajouter l'Isolation Forest ni le null à 0,5 au moteur d'alerte. Les deux répondent mal à la question du prix.
- Ne pas modifier `README.md`, `EDGE_VERDICT.md`, ni la ligne de base de publication.

## Défaut de forme que cette note aggrave

`CONTRIBUTING.md` demande l'anglais hors de `sources/`. Les neuf rapports sont en français parce que le mandat de cette session le demande. Le benchmark du 20 novembre comptait déjà les fichiers français hors `sources/` comme une faiblesse documentaire. Ce compte augmente. Le code, les tests et le README de la note restent en anglais pour que la reproduction ne dépende pas de la prose.
