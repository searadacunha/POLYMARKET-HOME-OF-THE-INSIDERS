#!/usr/bin/env python3
"""Generate MASTER_REPORT.md, INVENTORY.md and datasets/manifests/local_only.json.

Only reads investigations/*/{STATUS,FINDINGS}.md and data_manifest.json. Never edit the outputs
by hand: fix the investigation file and run this again. --check fails if the outputs are stale.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phi_lib as lib  # noqa: E402

STATE_LABEL = {"DONE": "Terminée", "IN_PROGRESS": "En cours", "PAUSED": "En pause", "ABANDONED": "Abandonnée"}
LEVEL_TITLE = {
    "CONFIRMED": "Démontré (CONFIRMED)",
    "SUPPORTED": "Soutenu, preuve incomplète (SUPPORTED)",
    "HYPOTHESIS": "Hypothèses non démontrées (HYPOTHESIS)",
    "REFUTED": "Réfuté, résultats négatifs (REFUTED)",
    "UNRESOLVED": "Non résolu, données insuffisantes (UNRESOLVED)",
}
HEADER = "<!-- Fichier généré par scripts/build_master_report.py. Ne pas le modifier à la main. -->\n"


def load():
    investigations = []
    for inv_dir in lib.investigation_dirs():
        status_path, findings_path = inv_dir / "STATUS.md", inv_dir / "FINDINGS.md"
        if not status_path.exists() or not findings_path.exists():
            continue
        fields, body = lib.parse_status(status_path.read_text())
        findings, sections = lib.parse_findings(findings_path.read_text())
        investigations.append({"id": inv_dir.name, "fields": fields or {}, "body": body.strip(), "findings": findings,
                               "sections": sections, "manifest": lib.load_manifest(inv_dir) or {"files": [], "counts": {}}})
    return investigations


def status_section(body, title):
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return " ".join(match.group(1).split()) if match else ""


def mb(n):
    return f"{n / 1e6:,.1f} Mo".replace(",", " ")


def local_only_rows(manifest):
    rows = [e for e in manifest["files"] if e.get("status") == "local_only"]
    return sum(e.get("files", 1) for e in rows), sum(e.get("size", 0) for e in rows), rows


def report(investigations):
    out = [HEADER, "# Rapport central\n"]
    total_findings = sum(len(i["findings"]) for i in investigations)
    out.append(f"{len(investigations)} enquêtes, {total_findings} conclusions classées. Chaque ligne renvoie au fichier "
               "`FINDINGS.md` de son enquête, qui cite ses sources. Une conclusion n'engage que son niveau de preuve.\n")
    out.append("Trois lectures à ne jamais franchir : un wallet étiqueté ChangeNOW ne prouve pas que son propriétaire est "
               "identifié ; une entrée dans ChangeNOW et une sortie ultérieure ne prouvent pas un transfert entre les mêmes "
               "personnes ; des paris suspects ne prouvent pas à eux seuls un délit d'initié.\n")
    out.append("## Toutes les enquêtes\n")
    out.append("| Enquête | État | Version | Mise à jour | Conclusions |\n|---|---|---|---|---|")
    for inv in investigations:
        f = inv["fields"]
        counts = " ".join(f"{level[:4]}:{n}" for level in lib.LEVELS
                          if (n := sum(1 for x in inv["findings"] if x["level"] == level)))
        out.append(f"| [{f.get('title', inv['id'])}](investigations/{inv['id']}/README.md) | "
                   f"{STATE_LABEL.get(f.get('state'), f.get('state'))} | {f.get('version', '')} | "
                   f"{f.get('updated_utc', '')[:10]} | {counts or 'aucune'} |")
    out.append("")
    for state in lib.STATES:
        names = [i["id"] for i in investigations if i["fields"].get("state") == state]
        if names:
            out.append(f"- **{STATE_LABEL[state]}** : " + ", ".join(f"`{n}`" for n in names))
    out.append("")
    for level in lib.LEVELS:
        out.append(f"## {LEVEL_TITLE[level]}\n")
        rows = [(i, x) for i in investigations for x in i["findings"] if x["level"] == level]
        if not rows:
            out.append("Rien à ce niveau.\n")
        for inv, finding in rows:
            state = inv["fields"].get("state")
            note = " *(enquête en cours : provisoire)*" if state == "IN_PROGRESS" else ""
            out.append(f"- **{inv['id']}:{finding['id']}** {finding['claim']}{note}")
            out.append(f"  - Limites : {finding.get('Limits', '')}")
        out.append("")
    out.append("## Liens vérifiés entre enquêtes\n")
    links = [(i["id"], x["id"], x["Links"]) for i in investigations for x in i["findings"]
             if x.get("Links", "").strip().lower() not in ("", "aucun")]
    if not links:
        out.append("Aucun.\n")
    for inv_id, finding_id, text in links:
        out.append(f"- `{inv_id}:{finding_id}` : {text}")
    out.append("")
    for title, heading in (("Contradictions", "Découvertes contradictoires"), ("Manque pour conclure", "Ce qui manque pour conclure"),
                           ("Surveillance prospective", "Possibilités de surveillance prospective")):
        out.append(f"## {heading}\n")
        rows = [(i["id"], line) for i in investigations for line in i["sections"].get(title, [])]
        if not rows:
            out.append("Rien de signalé.\n")
        for inv_id, line in rows:
            out.append(f"- `{inv_id}` : {line}")
        out.append("")
    out.append("## Données non archivées\n")
    out.append("Ces fichiers ne sont PAS dans ce dépôt. Ils n'existent que sur le Mac d'origine, avec leur empreinte au "
               "manifeste. Détail : [datasets/manifests/local_only.json](datasets/manifests/local_only.json).\n")
    out.append("| Enquête | Fichiers | Taille | Refusés par le contrôle |\n|---|---:|---:|---:|")
    for inv in investigations:
        count, size, _ = local_only_rows(inv["manifest"])
        refused = sum(1 for e in inv["manifest"]["files"] if e.get("status") == "refused")
        out.append(f"| `{inv['id']}` | {count} | {mb(size)} | {refused} |")
    out.append("")
    return "\n".join(out)


def inventory(investigations, extra):
    out = [HEADER, "# Inventaire des enquêtes\n"]
    out.append("Généré depuis les `STATUS.md` et les manifestes. Identifiant = dossier `investigations/<id>/` = branche `investigation/<id>`.\n")
    for inv in investigations:
        f, m = inv["fields"], inv["manifest"]
        count, size, _ = local_only_rows(m)
        c = m.get("counts", {})
        out.append(f"## {inv['id']}\n")
        out.append(f"- **Titre** : {f.get('title', '')}")
        out.append(f"- **Emplacement d'origine** : `{f.get('origin', '')}`")
        out.append(f"- **Statut réel** : {STATE_LABEL.get(f.get('state'), f.get('state'))}")
        out.append(f"- **Dernier commit et version** : {f.get('version', '')}")
        out.append(f"- **Instantané** : {m.get('snapshot_utc', 'aucun')}")
        for label, title in (("Objectif", "Objectif"), ("Conclusions", "Conclusions"), ("Limites", "Limites"), ("Liens", "Liens avec les autres enquêtes")):
            text = status_section(inv["body"], label)
            if text:
                out.append(f"- **{title}** : {text}")
        out.append(f"- **Données** : {c.get('imported', 0)} fichiers publiés ({mb(m.get('imported_bytes', 0))}), "
                   f"{c.get('duplicate', 0)} doublons renvoyés vers une autre enquête, "
                   f"{count} fichiers NON archivés ({mb(size)}), {c.get('refused', 0)} refusés par le contrôle.")
        out.append("")
    if extra.exists():
        out.append(extra.read_text())
    return "\n".join(out)


def local_only_index(investigations):
    rows = []
    for inv in investigations:
        for entry in local_only_rows(inv["manifest"])[2]:
            rows.append({"investigation": inv["id"], "origin": inv["manifest"].get("origin"), **entry})
    return json.dumps({"note": "Fichiers NON archivés dans ce dépôt.", "entries": rows}, indent=1, ensure_ascii=False) + "\n"


def main():
    investigations = load()
    outputs = {
        lib.REPO / "MASTER_REPORT.md": report(investigations),
        lib.REPO / "INVENTORY.md": inventory(investigations, lib.REPO / "datasets" / "HORS_ENQUETES.md"),
        lib.REPO / "datasets" / "manifests" / "local_only.json": local_only_index(investigations),
    }
    if "--check" in sys.argv:
        stale = [str(p.relative_to(lib.REPO)) for p, text in outputs.items() if not p.exists() or p.read_text() != text]
        print("à régénérer : " + ", ".join(stale) if stale else "rapports à jour")
        return 1 if stale else 0
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    print(f"{len(investigations)} enquêtes, {sum(len(i['findings']) for i in investigations)} conclusions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
