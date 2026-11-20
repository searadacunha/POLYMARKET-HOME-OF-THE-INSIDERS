"""Four-state registry of the external work this repository cites, read, adapted or integrated.

A project sits in the LOWEST state its evidence fully supports:
  S1_LISTED                catalogued or cited only
  S2_CODE_EXAMINED         code read: our documents hold a pinned commit and describe at least one named source file
  S3_METHOD_ADAPTED        a method adapted or re-implemented in this tree, provenance stated
  S4_INTEGRATED_VALIDATED  wired into our code, with a check that passes and a recorded run on real data

usage: python3 external_registry.py --check    validate the data and that the Markdown is the rendered data
       python3 external_registry.py --write    rewrite the Markdown from the data
Standard library only.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "external_registry.json"
DOC = HERE / "EXTERNAL_INTEGRATION_REGISTRY.md"
STATES = {
    "S4_INTEGRATED_VALIDATED": "integrated, checked and run on real data",
    "S3_METHOD_ADAPTED": "method adapted or re-implemented here",
    "S2_CODE_EXAMINED": "code read at a pinned commit",
    "S1_LISTED": "listed or cited only",
}
VALUES = ("HIGH", "MEDIUM", "LOW", "NONE")


def load(path=DATA):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate(reg, root=ROOT):
    """Every reason the registry cannot be trusted as written; an empty list means it holds."""
    errors = []
    seen = Counter(e["project"] for e in reg["entries"])
    errors += [f"duplicate project: {p}" for p, n in seen.items() if n > 1]
    for e in reg["entries"]:
        name, state = e["project"], e["state"]
        if state not in STATES:
            errors.append(f"{name}: unknown state {state}")
        if e["integration_value"] not in VALUES:
            errors.append(f"{name}: unknown integration_value {e['integration_value']}")
        files = e.get("our_files") or []
        errors += [f"{name}: cited file is absent: {f}" for f in files if not (root / f).exists()]
        if state in ("S3_METHOD_ADAPTED", "S4_INTEGRATED_VALIDATED") and not files:
            errors.append(f"{name}: {state} without a file of ours")
        if state == "S4_INTEGRATED_VALIDATED" and (e.get("check") or "none").strip().lower() == "none":
            errors.append(f"{name}: S4 without a passing check")
    return errors


def _cell(text):
    return " ".join(str(text or "").split()).replace("|", "\\|")


def _table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return out + ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]


def render(reg):
    entries = sorted(reg["entries"], key=lambda e: e["project"].lower())
    by_state = {s: [e for e in entries if e["state"] == s] for s in STATES}
    files = lambda e: ", ".join(f"`{f}`" for f in e.get("our_files") or [])
    lines = [
        "# External integration registry",
        "",
        f"Generated from `external_registry.json` by `external_registry.py --write`. Do not edit by hand: "
        f"`tests/test_external_registry.py` fails when this file and the data differ, or when a cited file is gone.",
        "",
        f"State of the repository read: commit `{reg['repo_commit'][:7]}`, {reg['generated_utc']}. "
        f"Each entry sits in the lowest state its evidence fully supports. A document saying that something is "
        f"integrated is not evidence; a file of ours, a check that passes and a recorded run are.",
        "",
        "How far this registry was itself checked: for every S3 and S4 entry the cited files exist (enforced by the "
        "test) and the cited checks were run again on the commit above. S1 and S2 entries were classified by reading "
        "the documents of this repository; they were not re-verified one by one against the external projects.",
        "",
        "## Counts",
        "",
        *_table(["State", "Meaning", "Entries"], [[s, STATES[s], len(by_state[s])] for s in STATES]),
        "",
        "## Integrated and validated (S4)",
        "",
        *_table(["Project", "Kind", "Licence", "Our files", "Check that passes", "Evidence"],
                [[e["project"], e["kind"], e.get("licence"), files(e), e.get("check"), e["evidence"]] for e in by_state["S4_INTEGRATED_VALIDATED"]]),
        "",
        "## Method adapted or re-implemented (S3)",
        "",
        *_table(["Project", "Licence", "Our files", "Evidence"],
                [[e["project"], e.get("licence"), files(e), e["evidence"]] for e in by_state["S3_METHOD_ADAPTED"]]),
        "",
        "## Studied but not integrated: capabilities of high value",
        "",
        *_table(["Project", "State", "Licence", "Capability we do not have"],
                [[e["project"], e["state"], e.get("licence"), e["not_integrated"]]
                 for e in entries if e["integration_value"] == "HIGH" and e["state"] in ("S1_LISTED", "S2_CODE_EXAMINED")]),
        "",
        "## Where documents of this repository say more than the code supports",
        "",
        *[f"- {' '.join(s.split())}" for s in reg["overstated_in_repo"]],
        "",
        "## All entries",
        "",
        *_table(["Project", "Kind", "State", "Value of integrating", "Licence"],
                [[e["project"], e["kind"], e["state"], e["integration_value"], e.get("licence")] for e in entries]),
        "",
    ]
    return "\n".join(lines)


def main(argv):
    reg = load()
    errors = validate(reg)
    if argv == ["--write"] and not errors:
        DOC.write_text(render(reg), encoding="utf-8")
    elif argv == ["--check"]:
        if not DOC.exists() or DOC.read_text(encoding="utf-8") != render(reg):
            errors.append(f"{DOC.name} is not the rendering of {DATA.name}: run --write")
    elif argv != ["--write"]:
        sys.exit(__doc__)
    print("\n".join(errors) or f"OK: {len(reg['entries'])} entries, {dict(Counter(e['state'] for e in reg['entries']))}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
