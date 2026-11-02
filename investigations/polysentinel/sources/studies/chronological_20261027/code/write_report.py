"""Render existing registered results; adds no analysis or selection."""
import gzip,json
from datetime import datetime,timezone
from pathlib import Path

STUDY=Path(__file__).resolve().parents[1]
def utc(x):return 'absent' if x is None else datetime.fromtimestamp(x,timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def main():
    r=json.loads((STUDY/'derived/evaluation.json').read_text())
    d=json.loads(gzip.decompress((STUDY/'data/extraction_v2.json.gz').read_bytes()))
    adverse_count=len(json.loads((STUDY/'controles/adversarial.json').read_text()))
    scope=r['case_key_selection']
    lines=['# Évaluation chronologique documentaire — 27 octobre 2026','',
      f"**Verdict : {r['verdict']}.** {r['direction_evaluable_events']}/{r['selected_events']} événements permettent le calcul directionnel défini ; "
      f"{r['economic_evaluable_events']}/{r['selected_events']} permettent un rendement économique. Aucun taux de détection d’initiés n’est estimé.",'',
      f"L’univers source compte {r['catalogue_events']} événements catalogués au cutoff {utc(r['cutoff'])} (cycle {d['cutoff_cycle_id']}). "
      f"La première activité du service archivée est {utc(r['bot_first_cycle_start'])}. La fenêtre de collecte ne doit pas être transformée en disponibilité historique antérieure.",'',
      '## Population et dénominateurs','',
      'Sélection figée avant lecture des issues : marque terminale explicite, échéance dans les 24 h, ordre date puis identifiant, huit maximum, FOMC exclu. '
      'Les prix extrêmes et les échéances seules ne définissent pas un résultat. Les événements sont conditionnés par le catalogue collecté et par leur terminaison.','',
      '| Raison d’exclusion de population | Événements |','|---|---:|']
    lines.extend(f'| {k} | {v} |' for k,v in sorted(r['population_exclusions'].items()))
    lines+=['',f"Retenus : {r['selected_events']} événements ; dossiers archivés au proxy : {r['archived_cases']} ; "
      f"prioritaires parmi ces dossiers : {r['priority_cases']}. n effectif indépendant inconnu ; borne supérieure par événements : {r['effective_event_upper_bound']}.",'',
      f"Sélection des clés dossiers : {scope['latest_keys_examined']} clés au cutoff, dont {scope['latest_keys_matching_selected_events']} "
      f"associées par leur dernier event_id aux événements retenus et {scope['latest_keys_outside_selected_events']} hors de cet ensemble. "
      'L’appartenance historique antérieure des clés non retenues n’a pas été balayée : alias/remappages peuvent masquer un ancien rattachement. '
      'Aucune réassignation rétrospective ; cette limitation empêche de qualifier la cohorte d’exhaustive.','',
      '## Huit vérifications chronologiques au maximum','',
      '| Événement présent | Échéance UTC | Premier constat terminal par le bot UTC | Cycle proxy UTC | Dossiers / priorités | Première information vérifiée | Verdict |',
      '|---|---|---|---|---:|---|---|']
    for e in r['events']:
        title=e['title'].replace('|','/')
        lines.append(f"| [{title}]({e['url']}) ({e['event_id']}) | {utc(e['scheduled_end'])} | {utc(e['first_terminal_observed_at'])} | "
          f"{utc(e['proxy_cycle_end'])} | {e['archived_cases']} / {e['priority_cases']} | {'oui' if e['first_public_information_verified'] else 'non'} | {e['verdict']} |")
    lines+=['','Le cycle proxy précède le **constat terminal du bot**, pas nécessairement l’information publique. '
      'Il ne devient jamais une décision pré-information par supposition. Les dossiers gardent leur propre instant de calcul et leur version de règle.','',
      '## Preuves disponibles et censures','']
    for e in r['events']:
        cc=e.get('case_key_counts') or {}
        lines+=[f"- **{e['event_id']} — {e['title']}** : première métadonnée observée {utc(e['first_event_observed_at'])} ; "
          f"collecte commencée après l’échéance : {'oui' if e['bot_coverage_started_after_scheduled_end'] else 'non'} ; "
          f"résolutions de conditions observées : {e['official_resolution_observations']} ; "
          f"dossiers avec preuves de features admises : {e['point_in_time_proven_cases']}/{e['archived_cases']} ; "
          f"cohorte complète : {'oui' if e['cohort_complete'] else 'non'} ; cible token vérifiée : {'oui' if e['target_verified'] else 'non'}. "
          f"{e['public_record_note'] or 'Aucune preuve de première annonce publique vérifiée archivée.'} "
          f"Clés dossiers examinées / retenues / écartées : {cc.get('examined')} / {cc.get('retained')} / {cc.get('excluded')} ; motifs : {cc.get('exclusions',{})}."]
        for c in e['cases']:
            a=c['focal'];lines.append(f"  - Dossier `{c['id']}`, wallet `{c['wallet']}`, règle {c['rule_version']}, "
                f"score {c['score']}, calcul {utc(c['calculated_at'])}, raisons d’exclusion : {', '.join(c['feature_reasons']) or 'aucune pour les seules features'}. "
                f"Historique censuré : {c['history_left_censored']}, {c['raw_fills']} fills / {c['trade_groups']} groupes.")
            if a:
                tx=a.get('transaction_hash')
                lines.append(f"    Achat focal : {utc(a['timestamp'])}, {a['size']} parts à {a['price']}, nominal {a['nominal']}, "
                    f"observé {utc(a['observed_at'])}. "+(f"[Transaction](https://polygonscan.com/tx/{tx})." if tx else 'Transaction unique non établie.'))
    matches=[m for e in r['events'] for m in e['controls']]
    assignments=sum(len(m['controls']) for m in matches)
    lines+=['',f"Contrôles : {assignments} affectations admissibles pour {len(matches)} dossiers cibles dont les features passent les contrôles ; "
      'même événement/token/condition, temps, prix, taille et couverture de groupes selon le plan. Aucun élargissement. '
      'Ce dénominateur est celui des dossiers archivés, pas celui de tous les comptes du marché.','',
      'Une résolution officielle est une preuve du statut de résolution au moment où le bot la lit. '
      'Elle ne date pas la première information publique. La cible et la complétude ne sont pas déduites de simples booléens `resolved` ou d’une couverture supposée.','',
      'Les trades archivés peuvent précéder de plusieurs heures leur collecte. Les observations postérieures au calcul ne complètent pas ses features. '
      'Les groupes de fills n’établissent pas des décisions indépendantes ; achats bruts, conversions, split/merge et couverture ne donnent pas un inventaire net. '
      'Expertise, chance, information publique, rumeur, arbitrage, couverture, copie et bots restent des explications possibles. Aucune propriété commune de wallets n’est établie.','',
      '## Ce qui a réellement été exécuté','',
      f"Extraction : {d['counts']['queries_requested']} lectures SQL demandées et {d['counts']['queries_returned']} terminées ; "
      f"{d['counts']['contents_decoded']} contenus décodés avec SHA-256 ; {d['counts'].get('empty_queries',0)} requêtes vides ; "
      'aucune requête réseau, aucune écriture de production, aucun backup complet. Le supplément de portée ajoute une requête SQL de décompte sans décodage. '
      'Références et contrôles de collecte : `data/collection_validation_v2.json` et `data/case_key_scope_v2.json`.','',
      f'Neuf scénarios synthétiques (trois niveaux × graines 11, 29, 47) et {adverse_count} contrôles adverses ont exercé le score v1.2 copié et le verdict. '
      'À chaque graine : nul 0/6 prioritaires, moyen 3/6, fort 6/6. Ce tableau est une sensibilité mécanique, pas une puissance sur les vrais marchés. '
      'Les répétitions de préparation restent toutes au registre ; voir `controles/CONTROLES.md` et `registre.py compter`.','',
      'Le seul balayage réel est enregistré après `derived/evaluation.json`. Les scores historiques sont ceux des émissions conservées ; '
      'aucun replay intégral des 50 000 trades par cycle n’est revendiqué. Les fichiers gelés et deux reproductions sont vérifiables avec les outils du skill. '
      'Les rapports d’audit indépendant et la vérification des deux reproductions doivent être lus séparément avant toute conclusion finale.','',
      '## Suite prospective reviewable','',
      'Le contrat `PROSPECTIVE_REVIEW.md` décrit les preuves à capter avant les prochaines annonces : périmètre scellé, données disponibles au calcul, '
      'cohorte comprenant les non-alertés, publication UTC vérifiée séparée de la résolution et cible token documentée. '
      'Aucun collecteur ni score de production n’est modifié par cette étude.','',
      '## Deviations and data notes','',
      'Aucune réécriture de données anciennes ni modification de seuil après résultat. Les contrôles avant gel ont été relancés après précisions de garde-fous ; '
      'leurs lignes restent conservées. Les compétences nommées `data:validate-data` et `pipeline-reconcile:reconcile` ne sont pas disponibles comme outils ici : '
      '`code/validate_data.py` réalise les vérifications locales explicites ; aucune réconciliation externe supplémentaire n’est revendiquée. '
      'Toute évolution méthodologique exige une nouvelle étude ou un amendement autorisé, jamais une réinterprétation de cette extraction.','']
    (STUDY/'results.md').write_text('\n'.join(lines))

if __name__=='__main__':main()
