"""Build the example viewer page from evidence this repository already publishes; it adds no claim.

The 14 transfers are those of finding F-001 of investigations/followup-20261113 (level read from its FINDINGS.md). Their
log indexes and token contracts come from the Polygon logs published with research_notes/nobel-strict-replay-2026-11-20,
matched on transaction, sender, recipient and amount; the script stops if one transfer does not match exactly one log.

    python3 docs/examples/build_nobel_funding_example.py           # write the input and the page
    python3 docs/examples/build_nobel_funding_example.py --check   # fail if the committed files differ
"""
import csv
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phi_forensics import sources as src, viz  # noqa: E402

FINDINGS = "investigations/followup-20261113/FINDINGS.md"
TRANSFERS = "investigations/followup-20261113/sources/data/nobel_funding_transfers.csv"
ACCOUNTS = "investigations/followup-20261113/sources/data/nobel_accounts.csv"
LOGS = "research_notes/nobel-strict-replay-2026-11-20/data/accounts_inflows.csv"
FINDING = "F-001"
HERE = Path(__file__).resolve().parent
INPUT, PAGE = HERE / "nobel-funding.input.json", HERE / "nobel-funding.html"
TITLE = "Example: one key paid eight Polymarket accounts, 9 and 10 October 2025 (published evidence)"


def table(path):
    with open(ROOT / path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def units(text):
    value = Decimal(text) * 1_000_000
    if value != value.to_integral_value():
        raise SystemExit(f"amount {text} is not a whole number of 1e-6 units")
    return int(value)


def level():
    """The level FINDINGS.md records for the finding, and a check that the finding cites the transfer table."""
    text = (ROOT / FINDINGS).read_text(encoding="utf-8")
    block = re.search(rf"^## {FINDING} \| ([A-Z]+) \|.*?(?=^## )", text, re.M | re.S)
    if not block or TRANSFERS.split("/sources/", 1)[1] not in block.group(0):
        raise SystemExit(f"{FINDINGS} {FINDING} does not cite {TRANSFERS}")
    return block.group(1)


def answers():
    grade, proxies = level(), {row["proxy"].lower() for row in table(ACCOUNTS)}
    handle_of = {row["handle"]: row["proxy"].lower() for row in table(ACCOUNTS)}
    logs = [{**row, "to": handle_of[row["handle"]]} for row in table(LOGS)]
    deposits = {}
    for row in table(TRANSFERS):
        sender, receiver, raw = row["from"].lower(), row["to"].lower(), units(row["usdc"])
        found = [log for log in logs if log["tx"].lower() == row["tx"].lower() and log["from"].lower() == sender
                 and log["to"] == receiver and units(log["amount"]) == raw]
        if len(found) != 1 or receiver not in proxies or int(found[0]["block"]) != int(row["block"]):
            raise SystemExit(f"{row['tx']}: {len(found)} matching logs in {LOGS}")
        ts = int(found[0]["t"])
        if src.utc(ts) != row["utc"][:19] + "Z":
            raise SystemExit(f"{row['tx']}: time {row['utc']} differs from the log time {src.utc(ts)}")
        deposits.setdefault(receiver, []).append({
            "tx": row["tx"].lower(), "log_index": int(found[0]["log_index"]), "block": int(row["block"]), "ts": ts,
            "from": sender, "to": receiver, "token": found[0]["token"].lower(), "amount_raw": raw, "evidence_level": grade})
    limits = [f"Only the {sum(map(len, deposits.values()))} transfers of finding {FINDING} ({grade}) are drawn.",
              "The withdrawals of finding F-002 went through Relay orders: they are not drawn, so no withdrawal destination is shown.",
              f"Log indexes and token contracts come from {LOGS}.",
              "They were matched on transaction, sender, recipient and amount.",
              "No graded link is drawn: the source records transfers, and a grade computed here would be a new reading.",
              "Finding F-007 of the same investigation (one person controls the eight accounts) is UNRESOLVED.",
              "The source tables do not record the kind of each address: every address is shown as 'kind not established'."]
    out = [{"wallet": wallet, "deposits": rows} for wallet, rows in sorted(deposits.items())]
    out[0]["limits"] = limits  # stated once: they apply to the whole example
    return out


def build():
    data = {"answers": answers(), "sources": [f"{FINDINGS} ({FINDING})", TRANSFERS, LOGS, ACCOUNTS]}
    text = json.dumps(data, indent=1, sort_keys=True) + "\n"
    return text, viz.render_html(viz.graph_document(*data["answers"], sources=data["sources"]), TITLE)


def main(argv):
    text, page = build()
    if "--check" in argv:
        stale = [p.name for p, body in ((INPUT, text), (PAGE, page)) if not p.exists() or p.read_text(encoding="utf-8") != body]
        print("stale: " + ", ".join(stale) if stale else "example is up to date")
        return 1 if stale else 0
    INPUT.write_text(text, encoding="utf-8")
    PAGE.write_text(page, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
