"""A tiny repository-shaped tree used by the tests: two investigations, data files, three test-register formats."""
import json
from pathlib import Path

A = "0x" + "a" * 40
B = "0x" + "b" * 40
C = "0x" + "c" * 40
TX = "0x" + "d" * 64  # a transaction hash: its first 40 hex characters must not be read as an address
SHA = "e" * 64


def write(root, rel, text):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def make_tree(root, alpha_state="DONE"):
    status = "---\nid: {id}\ntitle: {title}\nstate: {state}\nupdated_utc: 2026-11-01T00:00:00Z\norigin: ~/x\nversion: v1\n---\n\n" \
             "## Objective\n\nTest {id}.\n\n## Conclusions\n\nNothing yet.\n\n## Limits\n\nSmall sample.\n"
    write(root, "investigations/alpha/STATUS.md", status.format(id="alpha", title="Alpha case", state=alpha_state))
    write(root, "investigations/beta/STATUS.md", status.format(id="beta", title="Beta case", state="IN_PROGRESS"))
    write(root, "investigations/alpha/FINDINGS.md",
          f"# Findings\n\n## F-001 | CONFIRMED | Wallet {A.upper().replace('0X', '0x')} funded the account\n"
          "- Sources: sources/data/a.csv\n- Method: manual replay\n- Limits: none stated\n- Links: none\n\n"
          "## F-002 | REFUTED | Funding shortly before the first purchase is distinctive\n"
          "- Sources: sources/data/a.csv\n- Method: comparison with fresh accounts\n- Limits: small sample\n- Links: beta:F-001\n\n"
          "## Missing to conclude\n\n- first public report not located\n- comparison coverage incomplete\n\n"
          "## Contradictions\n\n- an earlier report said zero links\n")
    write(root, "investigations/beta/FINDINGS.md",
          f"# Findings\n\n## F-001 | HYPOTHESIS | The same operator controls {B} and {A}\n"
          f"- Sources: sources/data/b.json ; tx {TX}\n- Method: none\n- Limits: interpretation only\n- Links: alpha:F-001\n")
    write(root, "investigations/alpha/EVIDENCE.md",
          f"# Evidence\n\n| File | SHA-256 | Role |\n|---|---|---|\n| `sources/data/a.csv` | auto | Funding rows |\n"
          f"| `sources/report.md` | {SHA} | Final report |\n| `sources/big.csv` | local_only | Not archived |\n")
    write(root, "investigations/beta/EVIDENCE.md", "# Evidence\n\n| File | SHA-256 | Role |\n|---|---|---|\n")
    write(root, "investigations/alpha/sources/data/a.csv", f"wallet,amount\n{A},10\n{C},5\n")
    write(root, "investigations/beta/sources/data/b.json", json.dumps({"wallet": B, "peer": A, "tx": TX}))
    write(root, "research_notes/note-2026-11-02/REPORT.md", f"The account {C} appears again.\n")
    write(root, "investigations/alpha/sources/blob.bin", "not scanned: unknown extension " + A)
    # test-register formats: collective-exposure tests.json, early-detection verdict.json, census test_register.jsonl
    write(root, "investigations/alpha/results/tests.json", json.dumps({
        "n_comparisons": 3, "tests": {
            "T1": {"description": "rate vs price", "p_value": 0.01, "n": 50, "excess": 0.2, "bonferroni_alpha": 0.0167},
            "T2": {"description": "diff vs placebo", "p_value": 0.4, "n_s4": 50, "diff": -0.01, "bonferroni_alpha": 0.0167},
            "T3": {"description": "sweep", "p_value": 0.9}}}))
    write(root, "research_notes/study-2026-11-03/derived/verdict.json", json.dumps({
        "verdict": "NOT_SUPPORTED", "alpha_corrected": 0.0028, "comparisons_on_real_data": 18,
        "primary_T1": {"n": 45, "excess": 0.035, "p": 0.33}, "primary_T2": {"n_flag": 45, "diff": 0.02, "p": 0.04}}))
    write(root, "investigations/beta/sources/study/test_register.jsonl",
          json.dumps({"status": "exploratoire", "variant": "no_public_accounts", "test": "T1", "p": 0.08, "effect": 0.09}) + "\n"
          + json.dumps({"status": "confirmatoire", "variant": "all", "test": "T4", "p": 0.0005, "effect": 0.16}) + "\n"
          + json.dumps({"status": "exploratoire", "variant": "ci", "test": "T9", "p": 0.5, "effect": [0.1, 0.2]}) + "\n")
    write(root, "investigations/beta/sources/state/tests.json", json.dumps({"something": "else"}))  # same name, other format
    write(root, "investigations/alpha/sources/state/tests.json", json.dumps([1, 2, 3]))  # same name, not even an object
    return root
