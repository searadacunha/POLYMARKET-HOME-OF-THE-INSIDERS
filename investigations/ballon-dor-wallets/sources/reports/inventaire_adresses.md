# Inventaire des adresses, 1er novembre 2026

Une correspondance relie une étiquette de presse à un wallet Polymarket. Elle ne dit rien de la personne qui le contrôle. Aucune identité civile n'est recherchée ni enregistrée. Onze étiquettes n'impliquent ni onze personnes, ni une seule.

## Méthode

La capture publiée par Upside le 23 octobre montre les 15 premiers détenteurs de « Mbappé » sur le marché « Kylian Mbappé or Lamine Yamal to finish higher? » (événement 1105364, condition `0xa3cf5e6b…3af4`), avec leur nombre de parts. Fichier conservé : `evidence/public/upside_holders_HVUwQxmXQAAHlDQ.jpg`, sha256 `af72ce2c…a1d9`.

J'ai recalculé le net de parts de chaque wallet à partir du tape public de ce marché, makers compris : 11 583 lignes de `data-api /trades`.

**Résultat : les 15 lignes sur 15 sont reproduites, dans le même ordre, avec moins d'une demi-part d'écart.** Cet accord n'existe qu'entre le 23 octobre 14:11:39 et 14:18:08 UTC, ce qui date la capture à moins de sept minutes près, environ une heure avant le post. Les 11 lignes dont le nom est encore lisible sur le tape servent de contrôle positif : toutes tombent sur le bon wallet. Les 4 autres (0x86544e4dfde, BriardxO, Zoomman17, kraben006) sont les lignes résolues par les seules parts. Détail et rapprochements : `evidence/screenshot_reconstruction.json`.

Rapprochement fortuit attendu à une demi-part d'un chiffre imprimé, d'après la densité locale des positions : au plus 0,22 % par ligne (0,09 % pour Zoomman17, 0,02 % pour 0x86544e4dfde, 0,22 % pour kraben006). Cette estimation ignore que l'ordre complet est aussi reproduit : elle est donc prudente.

## Les onze étiquettes

| Étiquette publique | Wallet | Niveau de la correspondance | Propriétaire lu sur la chaîne | Nom affiché par l'API aujourd'hui |
|---|---|---|---|---|
| Thin-Disclaimer-Life | `0x8d3319c51520518ad01f6744486ceea29f376f5b` | alias exact et parts | `0x1bf0b469…6028` | Thin-Disclaimer-Life |
| VidenteRibeira | `0x5f8b30fde56bd2d2f3853769602330aeb9f1866a` | alias exact et parts | `0x3cb3f4f6…0f5e` | VidenteRibeira |
| cookedrice | `0x4060509c8c70cece529be4a089d6d66ad865b4d0` | alias exact sur le tape et parts, **nouveau** | `0x6ec29005…876f` | cookedrice |
| WenZhuanBuPei | `0x8832319d9c25df311e37511f0aa5b214abc16500` | alias exact et parts | `0x6697f72f…4405` | WenZhuanBuPei |
| 0x86544e4dfde | `0x3ed2c452f141c291adecb97ddfc72b1650acff3d` | parts seulement, **nouveau** | `0x69837228…0ded` | 0z8hlf..mmhofrzs |
| brace227 | `0x873848cd27784900e193611845fc3fd2c4716d03` | alias exact et parts | `0xc852b093…af26` | brace227 |
| walletwallet8424 | `0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40` | alias exact et parts | `0x82775eb8…a3a1` | walletwallet8424 |
| Zoomman17 | `0x92a8eec13a691af81a1a196b7594c1eccfa0eebc` | parts seulement, **nouveau** | `0xd90d0013…f444` | Atlfalcons7 |
| kraben006 | `0x84212ee459d1edaf35983bbec342b0806282d8ec` | parts seulement, **nouveau** | `0x101b5f4d…fb65` | Edgarblade |
| OuldLm3alem | `0x71ae923f12eb947c58365287691cf5a10bc3e5bf` | alias exact | `0x1b500b6c…5f2c` | OuldLm3alem |
| 0xdd97e6 | `0xdd97e6ad12ca4dd18a88804fb5ed7ed429849464` | préfixe de presse, unique dans la recherche officielle et le corpus, **nouveau** | `0xcf7b90de…19ad` | nom par défaut daté du 20 oct. 08:57:48 UTC |

Le dossier public en résolvait 6 sur 11. Il y en a maintenant 11 sur 11, à ces niveaux inégaux.

## Prudence sur ces résultats

- Un changement de nom n'est pas un indice en soi. Il touche aussi un compte non surligné de la capture : BriardxO s'appelle aujourd'hui Kallipso. Sa date reste inconnue.
- « Parts seulement » veut dire que le lien entre le nom imprimé et le wallet repose sur la position, pas sur un nom encore visible.
- kraben006 a une confirmation indépendante : ce wallet vend bien du Kane pour acheter Yamal 3e, comme le note la capture.
- `0x86544e4dfde` n'est ni le début du wallet, ni celui de son propriétaire : le nom imprimé reste inexpliqué.
- Le lien de `0xdd97e6` n'est pas certifié : la presse ne donne que six caractères.
- Les six comptes non surlignés de la capture (Cypyo, BriardxO, Cypya, pup1, mr.ozi, enginesinmyfactory) ne sont pas des suspects. Ils servent uniquement de comparateurs.
- La liste complète des douze comptes allégués par la presse n'est toujours pas publiée.

## Ce que cela ne touche pas

Ces correspondances restent dans cet espace de travail. Les labels gelés de `pipeline_replay_20261101` n'ont pas été lus ni modifiés. Faire entrer ces cinq adresses dans le R3 final serait un amendement daté, décidé par Benjamin.
