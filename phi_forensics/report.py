"""A wallet report in Markdown: what is established, with which transactions, what is not, and how to check it.

The report restates the facts of `investigate.wallet_overview` and adds nothing to them. It never grades a wallet
and never names a person.
"""
import re

from . import __version__

MARKUP = re.compile(r"[\\`*_\[\]<>|#!~&]")


def _cell(value):
    return str(value if value is not None else "not valued").replace("|", "\\|").replace("\n", " ")


def _text(value):
    """Third-party text as inert Markdown: one line, every character that could open markup escaped."""
    return MARKUP.sub(lambda found: "\\" + found.group(), " ".join(str(value).splitlines()))


def _code(value):
    """Third-party text inside a code span, which no escape reaches: one line and no backtick."""
    return " ".join(str(value).splitlines()).replace("`", "'")


def wallet_markdown(overview):
    wallet, trading, flows = overview["wallet"], overview["trading"], overview["funding"]
    profile = overview.get("profile")
    lines = [f"# Wallet report: `{wallet}`", "",
             f"Read-only reconstruction from public data by phi-forensics {__version__}. {overview['reading']}", "",
             "## What is established", ""]
    lines.append(f"- Public profile: name `{_code(profile['name'])}`, created {_text(profile['created_at'])}." if profile
                 else "- Public profile: none found.")
    owners = overview.get("owner_keys")
    lines.append("- Smart-wallet owner keys: " + (", ".join(f"`{key}`" for key in owners) if owners else "not a Safe that lists its owners, or none read") + ".")
    lines.append(f"- Trading history: {trading['activity_rows']} rows over {trading['markets']} markets, first trade {trading['first_trade_utc']}"
                 + ("." if trading["history_complete"] else " (history cut: figures below are partial)."))
    if trading["net_is_complete"]:
        lines.append(f"- Net trading result: **{trading['net_trading_result']}** (cash {trading['trading_cash']}, remaining inventory "
                     f"{trading['inventory_value_known']}; realised {trading['realised']}, unrealised {trading['unrealised_on_valued_inventory']}).")
    else:
        lines.append(f"- Trading cash: **{trading['trading_cash']}**. The net result is not stated: {trading['markets_not_valued']} markets hold "
                     "an inventory that could not be valued.")
    if trading["other_income"]:
        lines.append("- Other income, not counted as trading: " + ", ".join(f"{kind} {value}" for kind, value in trading["other_income"].items()) + ".")
    for name, key in (("Deposits", "deposited"), ("Withdrawals", "withdrawn")):
        totals = ", ".join(f"{value} of token `{token}`" for token, value in flows["totals"][key].items()) or "none"
        lines.append(f"- {name}: {flows[name.lower()]} transfers, {totals}.")
    if flows["deposited_by_counterparty_kind"]:
        lines.append("- Deposits by kind of sender: " + ", ".join(f"{kind} {value}" for kind, value in flows["deposited_by_counterparty_kind"].items()) + ".")
    first = flows.get("first_deposit")
    if first:
        delay = flows.get("seconds_from_first_deposit_to_first_trade")
        lines.append(f"- First deposit: {first['amount']} from `{first['counterparty']}` ({first['counterparty_label'] or first['counterparty_kind']}), "
                     f"transaction `{first['tx']}`, log {first['log_index']}, block {first['block']}"
                     + (f"; first trade {delay} seconds later." if delay is not None else "."))
    for relay in flows.get("relayed", [])[:5]:
        lines.append(f"- Relayed unchanged: {relay['amount']} received in `{relay['received']}` and sent {relay['seconds_between']} seconds later "
                     f"in `{relay['sent']}` to `{relay['to']}`.")
    lines += ["", "## Largest markets", "", "| Market | Result | Cash | State | Flags |", "|---|---:|---:|---|---|"]
    for market in overview["largest_markets"]:
        lines.append(f"| {_text(market['title'])} | {_cell(market['net'])} | {market['cash']} | {market['status']} | {_cell(', '.join(market['flags']))} |")
    lines += ["", "## What is not established", "",
              "- Who controls the wallet. An owner key, a funding address or a withdrawal address is an address, not a person.",
              "- Why the wallet traded. Nothing above shows access to information that was not public.",
              "- Any relation through an exchange, a bridge or another chain: money that passes through a service cannot be followed here.",
              "", "## Limits", ""]
    lines += [f"- {limit[0].upper()}{limit[1:]}." if not limit.endswith(".") else f"- {limit[0].upper()}{limit[1:]}" for limit in overview["limits"]]
    lines += ["", "## How to check", "", "```bash", f"python3 -m phi_forensics reconstruct_positions --wallet {wallet} --exact",
              f"python3 -m phi_forensics trace_funding --wallet {wallet}"]
    if first:
        lines.append(f"python3 -m phi_forensics verify_transfer --transaction {first['tx']} --recipient {wallet} --log_index {first['log_index']}")
    lines += ["```", ""]
    return "\n".join(lines)
