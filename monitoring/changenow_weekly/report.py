"""Builds every published file of one week from its analysis file, offline and deterministically.

A week that is still open is written as PROVISIONAL and is rewritten by the next run. Once every chain's settled head
has passed the end of the week it is CLOSED, and when its transactions have been read a second time without a mismatch
it is frozen: its files get a SHA-256 list and are never written again.
"""
import csv
import hashlib
import io as _io
import json
import random
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import chainio as io
from . import registry

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "reports/changenow"
LATEST = ("WEEKLY_LEADERBOARD.md", "weekly_leaderboard.csv", "weekly_leaderboard.json", "transactions.csv", "transactions.json", "candidates.csv", "COVERAGE.md", "PATTERNS.md")
NOT_READ = {42161: "Arbitrum", 10: "Optimism", 56: "BNB Chain", 43114: "Avalanche", 480: "World Chain"}
SEED = 20261109


def utc(ts):
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if ts else ""


def money(x):
    return f"{x:,.2f}"


def short(a):
    return f"{a[:6]}…{a[-4:]}"


def tx_url(chain, tx):
    return f"{io.CHAINS[chain]['explorer']}/tx/{tx}"


def table(header, rows, align=None):
    line = "| " + " | ".join(header) + " |"
    sep = "|" + "|".join((" ---: " if align and align[i] == "r" else " --- ") for i in range(len(header))) + "|"
    return "\n".join([line, sep] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def public_name(account):
    """The name the service publishes for the account. Its default name, the wallet address with a number, is no name."""
    p = account.get("profile") or {}
    name = p.get("name") or p.get("pseudonym") or None
    return None if name and re.fullmatch(r"0x[0-9a-fA-F]{40}(-\d+)?", name) else name


def network(chain):
    return {"bsc": "BNB Chain"}.get(io.CHAINS[int(chain)]["name"], io.CHAINS[int(chain)]["name"].title())


def leaderboard(a):
    """One row per account from the confirmed events. A ChangeNOW-side transfer split over several wallet movements
    counts once in the transaction count, and its amount is the sum of the parts, so nothing is counted twice."""
    rows = []
    by = defaultdict(list)
    for e in a["events"]:
        by[e["account"]].append(e)
    for account, events in by.items():
        ins, outs = [e for e in events if e["direction"] == "FUNDING"], [e for e in events if e["direction"] == "WITHDRAWAL"]
        info = a["accounts"][account]
        rows.append(dict(
            account=account, public_name=public_name(info), profile_url=f"https://polymarket.com/profile/{account}", wallet_type=info["type"],
            inflow_transactions=len({(e["cn"]["chain"], e["cn"]["tx"], e["cn"]["log_index"]) for e in ins}), inflow_usd=round(sum(e["usd"] for e in ins), 2),
            outflow_transactions=len({(e["cn"]["chain"], e["cn"]["tx"], e["cn"]["log_index"]) for e in outs}), outflow_usd=round(sum(e["usd"] for e in outs), 2),
            gross_usd=round(sum(e["usd"] for e in events), 2), net_usd=round(sum(e["usd"] for e in ins) - sum(e["usd"] for e in outs), 2),
            first_utc=utc(min(e["cn"]["ts"] for e in events)), last_utc=utc(max(e["cn"]["ts"] for e in events)),
            assets=sorted({f"{e['symbol']} on {network(e['cn']['chain'])}" for e in events}),
            changenow_attribution=sorted({t for e in events for t in e["cn_attribution"]}),
            markets=[m["title"] for m in info["summary"]["markets"][:5] if m.get("title")], week_trades=info["summary"]["week_trades"],
            week_trade_usd=info["summary"]["week_trade_usd"], first_trade_utc=utc(info["summary"]["first_trade_ts"]), last_trade_utc=utc(info["summary"]["last_trade_ts"]),
            confidence="CONFIRMED", verification="every hop read from chain logs; see the account file"))
    rows.sort(key=lambda r: (-r["gross_usd"], r["account"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def label(r):
    return f"[{r['public_name'] or short(r['account'])}](accounts/{r['account']}.md)"


def status_line(a):
    if a["closed"]:
        return f"Week closed. Every chain was read to its last block before {utc(a['end'])} UTC."
    parts = [f"{network(c)} to block {b['last']} ({utc(b['head_ts'])} UTC)" for c, b in sorted(a["blocks"].items(), key=lambda kv: int(kv[0]))]
    return "**Provisional: the week is not over.** Data stop at the last settled block of each chain: " + "; ".join(parts) + ". Later transfers of this week are missing and the figures will change."


def leaderboard_md(a, rows, link="accounts/"):
    fix = lambda text: text.replace("](accounts/", f"]({link}")
    week, start, end = a["week"], a["start"], a["end"]
    ins = sorted([r for r in rows if r["inflow_usd"]], key=lambda r: -r["inflow_usd"])
    outs = sorted([r for r in rows if r["outflow_usd"]], key=lambda r: -r["outflow_usd"])
    probable = [c for c in a["candidates"] if c["level"] == "PROBABLE"]
    lines = [f"# ChangeNOW and Polymarket: weekly money flows, {week}", "",
             f"Window: {utc(start)} UTC to {utc(end)} UTC, end excluded. {status_line(a)}", "",
             "This table lists Polymarket accounts for which a movement of funds from or to an address attributed to ChangeNOW was read, hop by hop, on public chains. "
             "It shows that the service's infrastructure paid or was paid. It does not show an individual exchange order, and using ChangeNOW is neither unlawful nor a sign of inside information. "
             "An account name is a public pseudonym, not a person. Coverage is partial: see [COVERAGE.md](COVERAGE.md).", "",
             "## Confirmed flows, ranked by gross volume", "",
             table(["Rank", "Polymarket account", "Inflows USD", "Outflows USD", "Gross volume USD", "Transactions", "Confidence"],
                   [[r["rank"], fix(label(r)), money(r["inflow_usd"]), money(r["outflow_usd"]), money(r["gross_usd"]), r["inflow_transactions"] + r["outflow_transactions"], r["confidence"]] for r in rows],
                   "llrrrrl") if rows else "No confirmed flow in the blocks read.", "",
             f"Totals: {len(rows)} accounts, {money(sum(r['inflow_usd'] for r in rows))} USD in, {money(sum(r['outflow_usd'] for r in rows))} USD out, "
             f"{sum(r['inflow_transactions'] + r['outflow_transactions'] for r in rows)} ChangeNOW-side transactions. Amounts are lower bounds where funds were mixed.", "",
             "## Detail by account", "",
             table(["Rank", "Account", "In tx", "In USD", "Out tx", "Out USD", "Gross USD", "Net flow USD", "First interaction UTC", "Last interaction UTC", "Assets and networks", "ChangeNOW end"],
                   [[r["rank"], fix(label(r)), r["inflow_transactions"], money(r["inflow_usd"]), r["outflow_transactions"], money(r["outflow_usd"]), money(r["gross_usd"]), money(r["net_usd"]),
                     r["first_utc"], r["last_utc"], ", ".join(r["assets"]), ", ".join(t.replace("_", " ").lower() for t in r["changenow_attribution"])] for r in rows], "llrrrrrrllll") if rows else "", "",
             "Net flow is inflows minus outflows through ChangeNOW over the week. It is not a profit or a loss.", "",
             "## Markets traded during the week by the confirmed accounts", "",
             "From the public activity feed. A funding is not tied to a particular market by this table.", "",
             table(["Rank", "Account", "Trades in the week", "Traded USD", "First trade ever UTC", "Last trade UTC", "Largest markets of the week"],
                   [[r["rank"], fix(label(r)), r["week_trades"], money(r["week_trade_usd"]), r["first_trade_utc"], r["last_trade_utc"], "; ".join(r["markets"]) or "none"] for r in rows], "llrrlll") if rows else "", "",
             "## Ranked by funding (ChangeNOW to Polymarket)", "",
             table(["#", "Account", "Inflow tx", "Inflows USD"], [[i, fix(label(r)), r["inflow_transactions"], money(r["inflow_usd"])] for i, r in enumerate(ins, 1)], "llrr") if ins else "None.", "",
             "## Ranked by withdrawals (Polymarket to ChangeNOW)", "",
             table(["#", "Account", "Outflow tx", "Outflows USD"], [[i, fix(label(r)), r["outflow_transactions"], money(r["outflow_usd"])] for i, r in enumerate(outs, 1)], "llrr") if outs else "None.", "",
             "## Probable flows, not confirmed, kept apart", "",
             "The key that dealt with ChangeNOW owns the wallet (read on-chain), and money moved between that key and its wallet on the relevant side of the ChangeNOW transfer, "
             "but the continuity of the same funds is not shown. The amount is the total of the key's ChangeNOW transfers of the week, an upper bound, and is never added to the confirmed totals.", "",
             table(["#", "Wallet", "Direction", "ChangeNOW transfers", "Upper bound USD", "Missing"],
                   [[i, f"`{c['account']}`", c["direction"], c["changenow_transfers"], money(c["usd_upper_bound"]), c["missing"][0]] for i, c in enumerate(probable[:40], 1)], "lllrrl") if probable else "None.", "",
             f"Hypothetical links (ownership and timing only): {sum(1 for c in a['candidates'] if c['level'] == 'HYPOTHETICAL')}, listed in `candidates.csv`, not ranked.", "",
             "Files of this week: [transactions.csv](transactions.csv), [weekly_leaderboard.csv](weekly_leaderboard.csv), [weekly_leaderboard.json](weekly_leaderboard.json), "
             "[candidates.csv](candidates.csv), [COVERAGE.md](COVERAGE.md), [PATTERNS.md](PATTERNS.md). Method: [METHODOLOGY.md](" + ("METHODOLOGY.md" if link == "accounts/" else "../../METHODOLOGY.md") + ").", ""]
    return "\n".join(lines)


def transaction_rows(a):
    names = {w: public_name(v) for w, v in a["accounts"].items()}
    rows = []
    for e in sorted(a["events"], key=lambda e: (e["cn"]["ts"], e["event_id"])):
        underlying = []
        for h in [dict(chain=e["cn"]["chain"], tx=e["cn"]["tx"]), dict(chain=e["pm"]["chain"], tx=e["pm"]["tx"])] + e["hops"]:
            ref = f"{h['chain']}:{h['tx']}"
            if ref not in underlying:
                underlying.append(ref)
            if h.get("fill_tx") and f"{h['fill_chain']}:{h['fill_tx']}" not in underlying:
                underlying.append(f"{h['fill_chain']}:{h['fill_tx']}")
        rows.append(dict(
            event_id=e["event_id"], week=e["week"], direction=e["direction"], level=e["level"], account=e["account"], account_public_name=names.get(e["account"]) or "",
            changenow_chain=network(e["cn"]["chain"]), changenow_tx=e["cn"]["tx"], changenow_log_index=e["cn"]["log_index"], changenow_block=e["cn"]["block"],
            changenow_utc=utc(e["cn"]["ts"]), changenow_address=e["cn_address"], changenow_role=e["cn_role"], changenow_attribution="|".join(e["cn_attribution"]),
            changenow_service_wallets="|".join(e["cn_service_wallets"]), counterparty=e["cn_counterparty"], token_symbol=e["symbol"],
            token_contract=e["cn"]["token"], decimals=e["decimals"], amount=f"{e['amount']:.{min(e['decimals'], 8)}f}", raw_attributed=e["cn_raw"], raw_transfer_total=e["cn"]["raw"],
            price_usd=e["price_usd"], price_utc=utc(e["price_ts"]), price_source="DeFiLlama coins API, nearest price within one hour", usd=e["usd"],
            polymarket_tx=e["pm"]["tx"], polymarket_log_index=e["pm"]["log_index"], polymarket_block=e["pm"]["block"], polymarket_utc=utc(e["pm"]["ts"]),
            polymarket_token=e["pm"]["token"], polymarket_raw_attributed=e["pm_raw"], path=" > ".join(h["kind"] for h in reversed(e["hops"])),
            underlying_transactions=";".join(underlying), explorer_url=tx_url(e["cn"]["chain"], e["cn"]["tx"])))
    return rows


def csv_text(rows, fields=None):
    out = _io.StringIO()
    fields = fields or (list(rows[0]) if rows else [])
    w = csv.DictWriter(out, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("|".join(str(x) for x in v) if isinstance(v, list) else v) for k, v in r.items()})
    return out.getvalue()


HOP_TEXT = {
    "CHANGENOW_PAYOUT": "A payout wallet attributed to ChangeNOW sends the asset.",
    "POLYMARKET_WALLET_DEBIT": "The Polymarket trading wallet sends the collateral out.",
    "TRANSFER": "A plain transfer between two addresses.",
    "CONVERSION_1_TO_1": "Collateral conversion between USDC.e and pUSD: the same amount on both legs, inside one transaction.",
    "RELAY_ORDER": "Deposit into the Relay escrow. The escrow log and the calldata of the solver's payment carry the same order id.",
}


def path_md(e):
    """The hops of one event in the order the money moved, each with the fact that justifies it."""
    steps = list(reversed(e["hops"]))
    first = e["pm"] if e["direction"] == "WITHDRAWAL" else None
    last = e["pm"] if e["direction"] == "FUNDING" else e["cn"]
    lines = []
    for n, h in enumerate(steps, 1):
        text = HOP_TEXT.get(h["kind"], h["kind"])
        extra = ""
        if h["kind"] == "RELAY_ORDER":
            extra = f" Order `{h['order']}`; solver payment [{short(h['fill_tx'])}]({tx_url(h['fill_chain'], h['fill_tx'])}) on {network(h['fill_chain'])}, {h['fill_raw']} raw units of `{h['fill_token']}`."
        if h.get("attributed_raw"):
            extra += f" Attributed part: {h['attributed_raw']} of {h['raw']} raw units."
        if h.get("note"):
            extra += f" Accepted because it is the {h['note']}."
        lines.append(f"{n}. **{h['kind']}** on {network(h['chain'])}, block {h['block']}, {utc(h['ts'])} UTC: `{h['src']}` to `{h['dst']}`, {h['raw']} raw units of `{h['token']}`, "
                     f"tx [{short(h['tx'])}]({tx_url(h['chain'], h['tx'])}), log {h['log_index']}. {text}{extra}")
    end = f"{len(steps) + 1}. **{'CREDIT_TO_WALLET' if e['direction'] == 'FUNDING' else 'DEPOSIT_INTO_CHANGENOW_ADDRESS'}** on {network(last['chain'])}, block {last['block']}, {utc(last['ts'])} UTC: `{last['src']}` to `{last['dst']}`, {last['raw']} raw units of `{last['token']}`, tx [{short(last['tx'])}]({tx_url(last['chain'], last['tx'])}), log {last['log_index']}."
    if e["direction"] == "WITHDRAWAL":
        swept = ", ".join(f"`{w}`" for w in e["cn_service_wallets"])
        end += f" This address is a one-time ChangeNOW deposit address by structure: it swept into {swept} during the week."
    return "\n".join(lines + [end]) + ("" if first is None else "")


def account_md(account, weeks_events, info, reg):
    name = public_name(info)
    events = sorted([e for ev in weeks_events.values() for e in ev], key=lambda e: e["cn"]["ts"])
    passers = Counter()
    for e in events:
        for h in e["hops"]:
            for side in ("src", "dst"):
                if h[side] not in (account, io.ZERO) and h[side] not in e["cn_service_wallets"] and h[side] != e["cn_address"]:
                    passers[h[side]] += 1
    services = sorted({w for e in events for w in e["cn_service_wallets"]})
    lines = [f"# {name or short(account)}", "",
             f"- Trading wallet: `{account}` ({info['type'].replace('_', ' ').title()}), [public profile](https://polymarket.com/profile/{account})",
             f"- Public name published by Polymarket: {name or 'none'}. A public name is a pseudonym, not a person.",
             f"- Keys read on-chain for this wallet: {', '.join('`' + o + '`' for o in info['owners']) or 'none read'}. {' '.join(info['evidence'])} A key is not a person either.",
             f"- First trade ever: {utc(info['summary']['first_trade_ts']) or 'none'} UTC. Last trade: {utc(info['summary']['last_trade_ts']) or 'none'} UTC.", "",
             "## Totals by week", "",
             table(["Week", "Inflow tx", "Inflows USD", "Outflow tx", "Outflows USD", "Gross USD", "Net flow USD"],
                   [[w, len({(e['cn']['tx'], e['cn']['log_index']) for e in ev if e['direction'] == 'FUNDING'}), money(sum(e['usd'] for e in ev if e['direction'] == 'FUNDING')),
                     len({(e['cn']['tx'], e['cn']['log_index']) for e in ev if e['direction'] == 'WITHDRAWAL'}), money(sum(e['usd'] for e in ev if e['direction'] == 'WITHDRAWAL')),
                     money(sum(e['usd'] for e in ev)), money(sum(e['usd'] * (1 if e['direction'] == 'FUNDING' else -1) for e in ev))] for w, ev in sorted(weeks_events.items())], "lrrrrrr"), "",
             "## Retained transactions", "",
             table(["UTC", "Direction", "Network", "Block", "ChangeNOW-side tx", "From", "To", "Token contract", "Quantity", "USD", "Level"],
                   [[utc(e["cn"]["ts"]), e["direction"], network(e["cn"]["chain"]), e["cn"]["block"], f"[{short(e['cn']['tx'])}]({tx_url(e['cn']['chain'], e['cn']['tx'])})",
                     f"`{e['cn']['src']}`", f"`{e['cn']['dst']}`", f"`{e['cn']['token']}`", f"{e['amount']:,.6f} {e['symbol']}", money(e["usd"]), e["level"]] for e in events], "lllrllllrrl"), "",
             "USD is the quantity times the DeFiLlama price of that token nearest to the transaction, within one hour. Each price and its own timestamp are in `transactions.csv`.", "",
             "## Fund paths, hop by hop", ""]
    for n, e in enumerate(events, 1):
        lines += [f"### {n}. {e['direction']} of {e['amount']:,.6f} {e['symbol']} ({money(e['usd'])} USD), {utc(e['cn']['ts'])} UTC", "", path_md(e), ""]
        if not e["bound"].get("direct"):
            b = e["bound"]
            lines += [f"Attribution bound: outflow of {b['outflow_raw']} raw units; balance held before the first tracked inflow {b['balance_before_first_tracked_inflow']}; other inflows in between {b['other_inflows_between']}; "
                      f"attributed {b['attributed_raw']}. Only the part that other money could not have covered is attributed.", ""]
    lines += ["## Addresses on these paths", "",
              table(["Address", "Role on the paths", "Times seen"], [[f"`{a}`", "pass-through or first counterparty of the ChangeNOW transfer (function only, no owner asserted beyond the keys above)", n] for a, n in passers.most_common()], "llr") if passers else "None besides the wallet and the service addresses.", "",
              "## ChangeNOW attribution of the service wallets involved", "",
              table(["Service wallet", "Tier", "Labels", "Independent label lineages", "Basis"],
                    [[f"`{w}`", reg[w]["tier"], reg[w]["labels"], reg[w]["independent_lineages"], reg[w]["basis"]] for w in services], "lllrl"), "",
              "Tier A is a public explorer label. Tier B has no public label: it was funded at creation by a labelled ChangeNOW wallet and behaved as a service wallet during the week. "
              "Either way, the attribution is to the service's infrastructure, never to one exchange order.", "",
              "## Markets traded during the latest week read", "",
              table(["Market", "Trades", "USD", "First trade UTC", "Last trade UTC"], [[m.get("title") or m.get("slug") or "", m["trades"], money(m["usd"]), utc(m["first_ts"]), utc(m["last_ts"])] for m in info["summary"]["markets"][:15]], "lrrll") if info["summary"]["markets"] else "No trade in the week read.", "",
              "## Limits and other explanations", "",
              "- The path proves that these funds moved between the service's wallets and this trading wallet. It does not prove who gave the instruction, nor that one person controls every address on the path.",
              "- A ChangeNOW payout can be a swap ordered by the account holder, a payment sent by someone else through the service, or a payout of a partner product that uses the same infrastructure. The chain does not tell them apart.",
              "- What entered the service on the other side of a swap (asset, chain, sender) is not public and is not inferred here.",
              "- Amounts are lower bounds where the intermediate address held other money. Transfers outside the blocks read, on chains not read, or in assets not followed are missing.",
              "- Trading after a funding is ordinary behaviour. Nothing here is evidence of inside information or of any offence.", ""]
    return "\n".join(lines)


def reg_label(address):
    row = registry.load().get(address)
    return f"{row['labels']}, {row['tier']}" if row else "not registered"


def coverage_md(a, rows):
    lines = [f"# Coverage of week {a['week']}", "", status_line(a), "",
             "This is a partial census. An account missing from the ranking has not been shown to be unrelated to ChangeNOW: it has only not been found by the reads below.", "",
             "## Networks and blocks read", "",
             table(["Network", "First block", "Last block read", "Blocks", "Settled by", "Week closed", "Registry addresses that signed a transaction", "Native transfers"],
                   [[network(c), b["first"], b["last"], b["last"] - b["first"] + 1, b["rule"], "yes" if b["closed"] else "no", len(a["active"][c]),
                     "from logs" if int(c) == 137 else ("Etherscan lists, count checked against account nonces" if a["stage1"][c].get("native") else "not read")] for c, b in sorted(a["blocks"].items(), key=lambda kv: int(kv[0]))], "lrrrllrl"), "",
             "## What was read on each network", ""]
    for c, st in sorted(a["stage1"].items(), key=lambda kv: int(kv[0])):
        pop = a["population"][c]
        s = pop["stats"]
        lines += [f"### {network(c)}", "",
                  table(["Stream", "Rows", "Log windows", "Other log shapes"], [[k, v["rows"], v.get("windows", ""), v.get("other_shapes", "")] for k, v in st.items() if v], "lrrr"), "",
                  f"- Payout sources used (registered, tier A or B, measured role PAYOUT_HOT): {', '.join('`' + x + '`' for x in pop['sources']) or 'none'}.",
                  f"- Gas funders measured: {', '.join('`' + x + '`' for x in pop['funders']) or 'none'}.",
                  f"- Payouts to outside addresses: {s['payouts']} to {s['payout_recipients']} recipients. Set aside and counted: {s.get('payout_side_internal_to_registry', 0)} transfers between registered addresses, "
                  f"{s.get('payout_side_to_own_deposit_address', 0)} to the service's own deposit addresses, {s['unrecognised_token_rows']} rows in tokens without a trusted price (look-alike tokens included).",
                  f"- One-time deposit addresses found: {s['deposit_addresses_gas_funded']} funded with gas by the service and swept into it, {s['deposit_addresses_single_use']} plain keys that signed one or two transactions in their life. "
                  f"Other senders into the sources, not treated as deposit addresses (treasury, exchanges, unknown): {s['other_senders_into_sources']}.",
                  f"- Customer deposits read into those addresses: {pop['deposits']['customer_deposits']} from {pop['deposits']['senders']} senders. Deposit addresses with no customer transfer read: {pop['deposits']['deposit_addresses_without_customer_row']}. "
                  f"Native deposits {'read from logs' if pop['deposits']['native_read'] else 'NOT read on this network: the senders of native coin into deposit addresses are unknown'}."
                  + (f" Transfers into deposit addresses were read for the {pop['deposits']['token_filter']} tokens these addresses swept into the service during the week: the node that serves a whole week of this network needs the token contracts named."
                     if pop["deposits"].get("token_filter") is not None else ""), ""]
    link = a["linking"]
    dep = a["dependent"]
    lines += ["## Polymarket accounts examined", "",
              f"- Counterparties tested against Polymarket: {link['counterparties']} addresses (payout recipients and deposit senders of every network read).",
              f"- Of these, trading wallets themselves: {link['trading_wallets_among_counterparties']}. Keys that own at least one trading wallet (Deposit Wallet, Safe or legacy proxy, proven on-chain): {link['keys_owning_a_wallet']}.",
              f"- Collateral sent on Polygon by payout recipients of every network: {dep['rcp_out']['rows']} transfers from {dep['rcp_out']['addresses']} addresses, {len(dep['rcp_out']['heavy'])} addresses set aside as too active to read.",
              f"- Credits of wallets owned by a payout recipient: {dep['own_in']['rows']} transfers into {dep['own_in']['addresses']} wallets, {len(dep['own_in']['heavy'])} set aside.",
              f"- Collateral received on Polygon by deposit senders: {dep['snd_in']['rows']} transfers into {dep['snd_in']['addresses']} addresses, {len(dep['snd_in']['heavy'])} set aside.",
              f"- Walks: {', '.join(f'{k} {v}' for k, v in sorted(a['walks']['counts'].items())) or 'none'}.",
              f"- Confirmed accounts: {len(rows)}. Probable: {sum(1 for c in a['candidates'] if c['level'] == 'PROBABLE')}. Hypothetical: {sum(1 for c in a['candidates'] if c['level'] == 'HYPOTHETICAL')}.", "",
              "The Polymarket side is checked in both directions. From ChangeNOW: every payout recipient and deposit sender is tested. From Polymarket: every credit of a wallet owned by a recipient is walked back to its origin, "
              "and every deposit into a ChangeNOW address by a sender fed by a trading wallet is walked back to that wallet. Accounts with no on-chain tie to a counterparty are not examined: the whole population of Polymarket deposits is not scanned.", "",
              "## Size of the ChangeNOW population read", "",
              table(["Network and side", "Transfers", "Addresses", "USD, one price an hour", "Transfers without a price"],
                    [[f"{network(k.split(':')[0])} {k.split(':')[1].replace('_', ' ')}", v["transfers"], v["addresses"], money(v["usd"]), v["unvalued_transfers"]] for k, v in sorted(a["totals"].items())], "lrrrr"), "",
              f"Confirmed Polymarket flows are {money(sum(r['gross_usd'] for r in rows))} USD of this population.", "",
              "## Requests and errors", "",
              table(["Host and status", "Requests"], [[k, v] for k, v in sorted(a["requests"]["io_counts"].items())], "lr"), "",
              "A status other than 200 was retried or raised. No refusal was turned into an empty result. Etherscan pages are read until an empty page, because a short page was served in the middle of a list on 2026-11-14.", "",
              "## Networks probed but not collected", "",
              "For these networks the only question asked was whether a registered address signed a transaction during the week, read from account nonces at the first and last block.", "",
              table(["Network", "Blocks", "Registered addresses ever used there", "Signed this week", "Reading"],
                    [[network(c), f"{v['first']} to {v['last']}", v["ever_used"], len(v["signed_this_week"]),
                      "; ".join(f"`{x}` ({reg_label(x)}): {n} transactions" for x, n in sorted(v["signed_this_week"].items())) or "no registered address signed: nothing known to collect"]
                     if "error" not in v else [network(c), "", "", "", "probe failed, activity unknown: " + v["error"]]
                     for c, v in sorted(a.get("other_chains", {}).items(), key=lambda kv: int(kv[0]))], "llrrl") if a.get("other_chains") else "Not probed in this run.", "",
              "No signature there does not mean no ChangeNOW activity: it means none of the addresses this register knows was used. The service's wallets on those networks are unknown to it.", "",
              "## Not covered", "",
              "- Networks with no registered address seen signing during the week, or with no free source for them: " + ", ".join(NOT_READ.values()) + ". ChangeNOW certainly operates wallets there that this register does not know.",
              "- Solana, Tron, Bitcoin, Monero and every non-EVM asset. A payout or a deposit on those networks is invisible here.",
              "- Native transfers on Base, and native deposits into deposit addresses on Ethereum: no free list serves them.",
              "- Payout wallets that carry no public label and are not tied to a labelled wallet at creation. Their flows are absent, not refuted.",
              "- Paths that change asset outside the collateral conversions and Relay orders followed here (a swap on an exchange or a pool, another bridge). They stop as unresolved and are at best probable.",
              "- Relay orders whose origin is on a network not read (BNB Chain, Solana and others).",
              "- The other side of each swap inside the service. It is not public.", ""]
    return "\n".join(lines)


def close_pairs(times, window=600):
    """Pairs of transfers to two different accounts at most `window` seconds apart. times: [(ts, account)]."""
    times = sorted(times)
    return [(times[i], times[j]) for i in range(len(times)) for j in range(i + 1, len(times)) if times[j][0] - times[i][0] <= window and times[j][1] != times[i][1]]


def patterns_md(a, rows):
    """Descriptive signals on the confirmed flows, each next to a base rate drawn from the service's own population."""
    from . import trace                                      # contract names only: nothing is read from the network here
    ev = a["events"]
    fund = [e for e in ev if e["direction"] == "FUNDING"]
    by_account = {r["account"]: r for r in rows}
    lines = [f"# Patterns in the confirmed flows of week {a['week']}", "",
             "Exploratory and descriptive. Nothing below is a test decided in advance, and several signals were looked at, so an unusual value is a reason to read an account file, not a finding. "
             "A shared service is not a common owner, and simultaneity is not coordination.", ""]
    # fundings close in time, against the service's own payout rhythm
    transfers = sorted({(e["cn"]["ts"], e["account"], e["cn"]["chain"], e["cn"]["tx"], e["cn"]["log_index"]) for e in fund})
    pairs = close_pairs([(t[0], t[1]) for t in transfers])
    lines += ["## Fundings close in time", "",
              f"Pairs of confirmed funding transfers to two different accounts within 10 minutes: {len(pairs)}, among {len(transfers)} funding transfers to {len({t[1] for t in transfers})} accounts.", ""]
    pool = {int(c): v for c, v in a.get("payout_times", {}).items()}
    if len(transfers) >= 2 and all(pool.get(t[2]) for t in transfers):
        rng = random.Random(SEED)
        sims = [len(close_pairs([(rng.choice(pool[t[2]]), t[1]) for t in transfers])) for _ in range(2000)]
        share = sum(1 for n in sims if n >= len(pairs)) / len(sims)
        lines += [f"Control: each transfer is given the time of a payout drawn at random among all the payouts the service made on the same network in the period ({sum(len(v) for v in pool.values())} payouts), "
                  f"2,000 draws, seed {SEED}. Mean {sum(sims) / len(sims):.2f} pairs; share of draws with at least {len(pairs)} pairs: {share:.3f}.", "",
                  ("The observed count is ordinary for the service's rhythm." if share >= 0.05 else
                   "There are more close pairs than the service's rhythm alone produces. That is a lead, not a link: read the pairs below. Accounts funded minutes apart can be one person, two people who talked, or chance."), ""]
    else:
        lines += ["Too few fundings, or no payout times, for a control.", ""]
    if pairs:
        lines += [table(["First transfer UTC", "Account", "Second transfer UTC", "Account", "Seconds apart"],
                        [[utc(x[0]), label(by_account[x[1]]), utc(y[0]), label(by_account[y[1]]), y[0] - x[0]] for x, y in pairs[:40]], "llllr"), ""]
    # identical amounts
    same = defaultdict(set)
    for e in ev:
        same[(e["direction"], e["cn"]["token"], e["cn"]["raw"])].add(e["account"])
    shared = {k: v for k, v in same.items() if len(v) > 1}
    lines += ["## Identical amounts across accounts", "",
              table(["Direction", "Token", "Raw amount", "Accounts"], [[k[0], f"`{k[1]}`", k[2], ", ".join(short(x) for x in sorted(v))] for k, v in sorted(shared.items())], "llrl") if shared
              else "No ChangeNOW-side amount is shared by two confirmed accounts.", "",
              "Round amounts repeat by habit and prove nothing. An odd amount repeated to the unit across accounts would deserve a look.", ""]
    # accounts that start trading after the funding
    fresh = []
    for r in rows:
        info = a["accounts"][r["account"]]
        first_fund = min((e["cn"]["ts"] for e in fund if e["account"] == r["account"]), default=None)
        first_trade = info["summary"]["first_trade_ts"]
        if first_fund and (first_trade is None or first_trade >= first_fund - 86400):
            fresh.append([label(r), utc(first_fund), utc(first_trade) or "no trade", money(r["inflow_usd"]), r["week_trades"], money(r["week_trade_usd"])])
    funded = [r for r in rows if r["inflow_usd"]]
    lines += ["## Accounts whose first trade ever comes after their first confirmed funding of the week, or less than a day before", "",
              table(["Account", "First confirmed funding UTC", "First trade ever UTC", "Inflows USD", "Trades in the week", "Traded USD"], fresh, "lllrrr") if fresh else "None.", "",
              f"{len(fresh)} of {len(funded)} funded accounts. A new account funded through a swap service is the ordinary way to arrive with assets held elsewhere, so this is a description, not a signal by itself.", ""]
    # what the public feed shows next to each movement: trading after a funding, redemptions before a withdrawal
    after, before, measured = [], [], all("around" in a["accounts"][r["account"]] for r in rows)
    for r in rows:
        near = a["accounts"][r["account"]].get("around") or {}
        mine = [e for e in ev if e["account"] == r["account"]]
        for m in near.get("after_funding", []):
            paid = sum(e["usd"] for e in mine if e["direction"] == "FUNDING" and e["pm"].get("ts") == m["ts"])
            wait = "" if m["first_trade_ts"] is None else round((m["first_trade_ts"] - m["ts"]) / 60)
            after.append((-m["usd"], [label(r), utc(m["ts"]), money(paid), wait if wait != "" else "no trade", m["trades"], money(m["usd"]),
                                      (m["largest_market"] + f" ({money(m['largest_market_usd'])} USD)") if m["trades"] else "", "yes" if m["day_over"] else "no"]))
        for m in near.get("before_withdrawal", []):
            left = sum(e["usd"] for e in mine if e["direction"] == "WITHDRAWAL" and e["pm"].get("ts") == m["ts"])
            before.append((-m["usd"], [label(r), utc(m["ts"]), money(left), m["redemptions"], money(m["usd"]), (m["largest_market"] + f" ({money(m['largest_market_usd'])} USD)") if m["redemptions"] else ""]))
    traded = sum(1 for _, row in after if row[4])
    redeemed = sum(1 for _, row in before if row[3])
    lines += ["## Trading in the day after a confirmed funding", ""]
    if not measured:
        lines += ["Not measured for this analysis file.", ""]
    else:
        lines += [(table(["Account", "Funding reached the wallet UTC", "Funding USD", "Minutes to the first trade", "Trades in the next 24 h", "Traded USD in the next 24 h", "Largest market of that day", "Day over"],
                         [row for _, row in sorted(after, key=lambda x: (x[0], x[1][0], x[1][1]))[:40]], "llrrrrll") if after else "No confirmed funding."), "",
                  f"{traded} of {len(after)} fundings were followed by at least one trade within a day. Trades come from the public activity feed, from the second the credit reached the wallet. "
                  "Funding an account and then trading is what a funding is for. A row deserves a look when one market takes most of the money within minutes and the account had not traded before; "
                  "even then it shows a decision made quickly, not what the trader knew.", ""]
    lines += ["## Redemptions in the day before a confirmed withdrawal", ""]
    if not measured:
        lines += ["Not measured for this analysis file.", ""]
    else:
        lines += [(table(["Account", "Withdrawal left the wallet UTC", "Withdrawal USD", "Redemptions in the 24 h before", "Redeemed USD", "Largest redeemed market"],
                         [row for _, row in sorted(before, key=lambda x: (x[0], x[1][0], x[1][1]))[:40]], "llrrrl") if before else "No confirmed withdrawal."), "",
                  f"{redeemed} of {len(before)} withdrawals came within a day after at least one redemption. A redemption is the payout of a resolved market, so this is the closest public trace of cashing out after a resolution. "
                  "Withdrawing winnings is ordinary. Resolution times themselves are not read.", ""]
    # round trips
    both = [r for r in rows if r["inflow_usd"] and r["outflow_usd"]]
    lines += ["## Accounts with both a funding and a withdrawal through ChangeNOW in the week", "",
              table(["Account", "Inflows USD", "Outflows USD", "Net flow USD"], [[label(r), money(r["inflow_usd"]), money(r["outflow_usd"]), money(r["net_usd"])] for r in both], "lrrr") if both else "None.", ""]
    # one key behind several confirmed wallets, and intermediate addresses shared by accounts
    keys = defaultdict(set)
    for account, info in a["accounts"].items():
        for owner in info["owners"]:
            keys[owner].add(account)
    several = {k: v for k, v in keys.items() if len(v) > 1}
    lines += ["## One key behind several confirmed wallets", "",
              table(["Key", "Wallets it controls on-chain"], [[f"`{k}`", ", ".join(label(by_account[x]) for x in sorted(v))] for k, v in sorted(several.items())], "ll") if several
              else "None among the confirmed accounts.", "", "A key that owns two wallets is one key. Who holds it is not on the chain.", ""]
    seen = defaultdict(set)
    for e in ev:
        for h in e["hops"]:
            for side in ("src", "dst"):
                x = h[side]
                plumbing = trace.is_ramp(x) or x in trace.RELAY_SOLVERS or x == trace.DEPOSITORY or trace.ff_flows.label_of(x) or x in e["cn_service_wallets"]
                if not plumbing and x not in a["accounts"]:
                    seen[x].add(e["account"])
    reused = {k: v for k, v in seen.items() if len(v) > 1}
    lines += ["## Intermediate addresses used by more than one confirmed account", "",
              table(["Address", "Accounts"], [[f"`{k}`", ", ".join(label(by_account[x]) for x in sorted(v))] for k, v in sorted(reused.items())], "ll") if reused
              else "None. The service wallets, the collateral contracts and the bridge solver are shared by construction and are not counted.", "",
              "An address that feeds or drains two accounts ties their funds, not their owners: it can be one person's wallet or a third party paying several people.", ""]
    cross = [e for e in ev if any(h["kind"] == "RELAY_ORDER" and h["chain"] != h.get("fill_chain") for h in e["hops"])]
    med = sorted(e["usd"] for e in ev)
    lines += ["## Cross-chain paths", "",
              f"Confirmed events whose path crosses a bridge between two networks: {len(cross)} of {len(ev)}. "
              + ("Their accounts: " + ", ".join(sorted({label(by_account[e['account']]) for e in cross})) + "." if cross else "A Relay order that stays on one network (USDC to USDC.e on Polygon) is a conversion, not a bridge."), "",
              "## Sizes", "",
              table(["Measure", "Value"], [["Confirmed events", len(ev)], ["Largest event USD", money(max(med, default=0))], ["Median event USD", money(med[len(med) // 2]) if med else "0.00"],
                                           ["Events under 100 USD", sum(1 for x in med if x < 100)], ["Events of 1,000 USD or more", sum(1 for x in med if x >= 1000)]], "lr"), "",
              "## Not measured here", "",
              "- Resolution times of the markets. Redemptions before a withdrawal are shown above instead.",
              "- Size of positions relative to each market's volume.",
              "- A control group of Polymarket accounts funded by other routes. The base rates above come from the ChangeNOW population only, so they describe the service's rhythm, not Polymarket's.", "",
              "## Accounts to read first", ""]
    paired = {x[1] for pair in pairs for x in pair}
    order = sorted(rows, key=lambda r: -r["gross_usd"])[:10]
    why = lambda r: "; ".join(w for w in ("funding and withdrawal in the same week" if r["inflow_usd"] and r["outflow_usd"] else "",                                  # noqa: E731
                                          "funded within minutes of another confirmed account" if r["account"] in paired else "", "among the largest confirmed volumes") if w)
    lines += [table(["Account", "Why it comes first", "Gross USD"], [[label(r), why(r), money(r["gross_usd"])] for r in order], "llr") if order else "None.", "",
              "The order is by size. It carries no accusation.", ""]
    return "\n".join(lines)


def write(raw, week):
    a = json.loads((Path(raw) / week / "analysis.json").read_text())
    folder = OUT / "weeks" / week
    if (folder / "SHA256SUMS").exists():
        raise SystemExit(f"{week} is frozen: its report is not rewritten. Run `verify` to check it.")
    reg = registry.load()
    rows = leaderboard(a)
    folder.mkdir(parents=True, exist_ok=True)
    tx = transaction_rows(a)
    board_fields = ["rank", "account", "public_name", "profile_url", "wallet_type", "inflow_transactions", "inflow_usd", "outflow_transactions", "outflow_usd", "gross_usd", "net_usd",
                    "first_utc", "last_utc", "assets", "changenow_attribution", "week_trades", "week_trade_usd", "first_trade_utc", "last_trade_utc", "markets", "confidence", "verification"]
    cand_fields = ["week", "direction", "level", "account", "wallet_kind", "owner", "ownership_proof", "changenow_transfers", "usd_upper_bound", "unpriced_transfers", "chains", "first_utc", "last_utc", "missing"]
    cands = [dict(c, first_utc=utc(c["first_ts"]), last_utc=utc(c["last_ts"])) for c in a["candidates"]]
    roles = [dict(network=network(c), address=addr, tier=reg[addr]["tier"], labels=reg[addr]["labels"], signed_transactions=a["active"][c].get(addr, 0), **v)
             for c, pop in sorted(a["population"].items(), key=lambda kv: int(kv[0])) for addr, v in sorted(pop["roles"].items())]
    status = dict(week=week, state="CLOSED" if a["closed"] else "PROVISIONAL", window_utc=[utc(a["start"]), utc(a["end"])], generated_utc=utc(a["generated_ts"]),
                  blocks={network(c): dict(first=b["first"], last=b["last"], settled_by=b["rule"], closed=b["closed"]) for c, b in a["blocks"].items()},
                  confirmed_accounts=len(rows), confirmed_events=len(a["events"]), inflow_usd=round(sum(r["inflow_usd"] for r in rows), 2), outflow_usd=round(sum(r["outflow_usd"] for r in rows), 2))
    files = {
        "WEEKLY_LEADERBOARD.md": leaderboard_md(a, rows, link="../../accounts/"),
        "weekly_leaderboard.csv": csv_text(rows, board_fields),
        "weekly_leaderboard.json": json.dumps(dict(status=status, accounts=rows), indent=1) + "\n",
        "transactions.csv": csv_text(tx),
        "transactions.json": json.dumps(dict(status=status, events=a["events"]), indent=1) + "\n",
        "candidates.csv": csv_text(cands, cand_fields),
        "COVERAGE.md": coverage_md(a, rows),
        "PATTERNS.md": patterns_md(a, rows).replace("](accounts/", "](../../accounts/"),
        "registry_week.csv": csv_text(roles),
        "STATUS.json": json.dumps(status, indent=1) + "\n",
    }
    for name, text in files.items():
        (folder / name).write_text(text)
    # latest copies at the root, with links that work from there
    (OUT / "WEEKLY_LEADERBOARD.md").write_text(leaderboard_md(a, rows) + archive_index())
    (OUT / "PATTERNS.md").write_text(patterns_md(a, rows))
    for name in LATEST:
        if name not in ("WEEKLY_LEADERBOARD.md", "PATTERNS.md"):
            shutil.copyfile(folder / name, OUT / name)
    # account files are cumulative over every week on disk
    (OUT / "accounts").mkdir(exist_ok=True)
    history, infos = defaultdict(dict), {}
    for wk in sorted(p.name for p in (OUT / "weeks").iterdir() if (p / "transactions.json").exists()):
        data = json.loads((OUT / "weeks" / wk / "transactions.json").read_text())
        for e in data["events"]:
            history[e["account"]].setdefault(wk, []).append(e)
    for account, info in a["accounts"].items():
        infos[account] = info
    for account, weeks_events in history.items():
        if account in infos:                           # an account of an earlier week keeps the file written that week
            (OUT / "accounts" / f"{account}.md").write_text(account_md(account, weeks_events, infos[account], reg))
    print(f"report written: {folder} ({status['state']}), {len(rows)} accounts, {len(a['events'])} events")
    return status


def archive_index():
    weeks = sorted((p.name for p in (OUT / "weeks").iterdir() if (p / "STATUS.json").exists()), reverse=True)
    lines = ["## Archive", "", table(["Week", "State", "Confirmed accounts", "Inflows USD", "Outflows USD", "Files"],
                                      [[w, "FROZEN" if (OUT / "weeks" / w / "SHA256SUMS").exists() else s["state"], s["confirmed_accounts"], money(s["inflow_usd"]), money(s["outflow_usd"]), f"[weeks/{w}](weeks/{w}/WEEKLY_LEADERBOARD.md)"]
                                       for w in weeks for s in [json.loads((OUT / "weeks" / w / "STATUS.json").read_text())]], "llrrrl"), ""]
    return "\n".join(lines)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(week):
    """Seal a closed week whose second reading found no mismatch and no unavailable check. Returns True when sealed."""
    folder = OUT / "weeks" / week
    second = folder / "RECONCILIATION.json"
    if json.loads((folder / "STATUS.json").read_text())["state"] != "CLOSED" or not second.exists():
        return False
    reading = json.loads(second.read_text())
    if reading["mismatches"] or reading.get("unavailable"):
        return False
    names = sorted(p.name for p in folder.iterdir() if p.is_file() and p.name != "SHA256SUMS")
    (folder / "SHA256SUMS").write_text("".join(f"{digest(folder / n)}  {n}\n" for n in names))
    (OUT / "WEEKLY_LEADERBOARD.md").write_text((OUT / "WEEKLY_LEADERBOARD.md").read_text().split("## Archive")[0] + archive_index())
    return True


def verify(out=None):
    """Every frozen week must match its SHA-256 list exactly: no file changed, added or removed. Offline."""
    bad, checked = [], 0
    weeks = (out or OUT) / "weeks"
    for folder in sorted(p for p in weeks.iterdir() if p.is_dir()) if weeks.exists() else []:
        sums = folder / "SHA256SUMS"
        if not sums.exists():
            continue
        listed = dict(line.split("  ", 1)[::-1] for line in sums.read_text().splitlines() if line)
        present = {p.name for p in folder.iterdir() if p.is_file() and p.name != "SHA256SUMS"}
        for name in sorted(set(listed) | present):
            checked += 1
            if name not in listed:
                bad.append(f"{folder.name}/{name}: added after the freeze")
            elif name not in present:
                bad.append(f"{folder.name}/{name}: missing")
            elif digest(folder / name) != listed[name]:
                bad.append(f"{folder.name}/{name}: changed")
    for line in bad:
        print("FAIL", line)
    print(f"{checked} frozen files checked, {len(bad)} problems")
    return 1 if bad else 0
