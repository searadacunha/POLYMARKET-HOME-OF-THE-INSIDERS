# Monero : ce qui est visible

Lu le 2 novembre 2026. Aucune transaction Monero n'a été recherchée ni reconstruite à partir de montants ou de dates.

## Résultat

| Catégorie | Nombre | Contenu |
|---|---|---|
| **CONFIRMÉ** | **0** | Aucune preuve explicite de l'actif XMR dans une opération déterminée |
| **POSSIBLE** | 3 chemins sur 2 comptes, plus 1 lointain | Passage par un service proposant XMR, sans aucune preuve de la conversion |
| **NON ÉTABLI** | Tout le reste | Aucun élément spécifique |

**« POSSIBLE » est une catégorie de visibilité, pas un indice.** Ces chemins passent par ChangeNOW, et on ne voit pas l'autre côté : XMR, BTC, ETH, ou un autre des 1 260 actifs listés aujourd'hui donnent exactement le même dossier.

## Chemins POSSIBLES

| Compte | Chemin | Montant | Côté invisible | Élément propre à XMR |
|---|---|---|---|---|
| kraben006 | Entrée inconnue → ChangeNOW → clé, 2026-02-23 | 834,848793 USDC | Actif source | **Aucun** |
| kraben006 | Clé → `0x7e67df45…` → ChangeNOW, 2026-10-04. Dépend de la lecture du relais par son empreinte | 0,00247406 ETH | Actif de sortie | **Aucun** |
| brace227 | Entrée inconnue → ChangeNOW → `0x3eaef6d5…` → clé, 2025-01-04 | 291,317423 USDT | Actif source | **Aucun.** Intermédiaire non attribué, 21 mois avant les paris |
| walletwallet8424 | ChangeNOW → `0xcc0f311e…`, 2025-09-30 | 0,00476548 ETH, sur une adresse mutualisée | Actif source | **Aucun, sans portée** |

**Aucun de ces chemins n'a de lien documenté avec les paris.** Les fonds de kraben006 et brace227 quittent la clé bien avant les dépôts Polymarket (`reports/PAYOUT_MATCHES.md`).

## Tableau des 11 comptes

| Compte | Statut |
|---|---|
| kraben006 | POSSIBLE, sans élément propre à XMR |
| brace227 | POSSIBLE, indirect |
| walletwallet8424 | POSSIBLE au sens strict, sans portée |
| thin, vidente, cookedrice, wen, 0x86544e4dfde, zoomman17, ouldlm3alem, 0xdd97e6 | NON ÉTABLI |

**Pour ces 8 comptes,** aucun passage par une adresse attribuée à ChangeNOW n'est lu. Leurs fonds entrent par des plateformes et des services non attribués : ce qui s'y passe reste invisible, et une rupture de trace n'est pas un indice de Monero. Cette remarque vaut pour les autres services que flow-trace a recensés, pas seulement ChangeNOW.

## Ce qui a été cherché

- **Dans les dossiers locaux :** `payinHash`, `payoutHash`, `payinAddress`, `payoutAddress`, lien de suivi. **Rien** (`state/figures.json`). Texte `changenow` : 5 fichiers sur 26 451 en cache au moment du comptage, tous des tags d'adresses de service.
- **Sur la chaîne :** les 49 transactions relues sur nœud ont une calldata standard, sans mémo ni identifiant.
- **Sur le web :** deux recherches sur les adresses complètes. Aucun résultat pertinent (`evidence/docs/web_searches.md`, résumés seulement).
- **Documentation ChangeNOW :** les actifs d'un ordre ne figurent que dans la réponse de `GET /v2/exchange/by-id`, sous clé partenaire.
- **Liste des devises :** XMR y figure (`evidence/docs/changenow_currencies.json` chez flow-trace, lue le 2 nov. 2026). **Cette liste date de sa lecture, pas des transactions.** Je n'ai rien demandé à l'API de ChangeNOW.

## Ce que je n'ai pas fait

- **Aucune recherche sur la chaîne Monero.** Un rapprochement montant et date n'y aurait aucune valeur.
- **Aucun rapprochement du type « ce montant correspond à tant de XMR ».** Le taux, les frais et le délai laissent passer presque n'importe quel chiffre.

## Ce qu'il faudrait

Le registre de ChangeNOW pour les ordres liés à `0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219`, `0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80`, `0x1a39308b89cc7d9de6e38fbf0c62aa5d0bdd777863079cd151fe12a6b135dd71` et `0xd0df7496375ecc9bb5dfb7e5aa8831053986a2a600734181afcf94f255ecd2d5`. Le champ `fromCurrency` ou `toCurrency` tranche. Sans lui, la question reste ouverte, dans un sens comme dans l'autre.

## Décision réservée à Benjamin

L'amendement de l'enquête laisse ouverte la pose du statut `XMR_VISIBILITY_BOUNDARY` pour le passage par l'adresse étiquetée ChangeNOW. **Je n'ai rien posé ni modifié.** Ce rapport fournit les faits : passage par un service proposant XMR établi pour kraben006, aucune preuve de XMR, et aucun chemin documenté entre les fonds concernés et les paris.

<!-- adresses -->
## Adresses citées en forme courte

| Adresse complète | Étiquette publique lue |
|---|---|
| `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | Aucune, relais |
| `0xcc0f311eb2c688f30bc9aadb42781e46899723f7` | Voir `data/changenow_candidates.csv` ou aucune |
<!-- fin adresses -->
