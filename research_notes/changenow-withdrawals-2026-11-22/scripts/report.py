"""Write results/REPORT.md and results/interesting_wallets.md from the published tables and the census files.

Offline. Every number in the two pages is read from results/*.csv, results/*.json or data/<week>/withdrawals.json.gz;
the prose around them is fixed text in this file. Run after build.py.
"""
import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = HERE.parent
RES = NOTE / "results"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import build  # noqa: E402

CN = {1: "Ethereum", 137: "Polygon", 8453: "Base"}
EXPL = {"Polygon": "https://polygonscan.com", "Ethereum": "https://etherscan.io", "Base": "https://basescan.org"}

# Earlier work read before this census (2026-11-22), what it holds, and what this note takes from it. Fixed text:
# each line points to the file that supports it.
AUDIT = [
    ("[`investigations/changenow-outflows`](../../../investigations/changenow-outflows/)", "Plan of 2026-11-02 for counting ChangeNOW payouts, public label snapshot, 90-day Etherscan histories of a few service wallets; no report (`STATUS.md`: IN_PROGRESS)",
     "Its label snapshot, through the register of `monitoring/changenow_weekly`"),
    ("[`investigations/changenow-polymarket`](../../../investigations/changenow-polymarket/)", "Funding direction: 3,408 payees of `0xf2020cbf…` (2026-04-14 to 06-22), 158 bettor records, 153 trading accounts; a controlled ChangeNOW order paid from `0xf2020cbf…` ([case file](../../../investigations/changenow-polymarket/sources/case_03_firm_verdict.md)); 42 % of that wallet's inflow from an unlabelled contract",
     "The structural attribution of `0xf2020cbf…`; the 153 accounts, checked forward"),
    ("[`investigations/changenow-proof`](../../../investigations/changenow-proof/)", "Ballon d'Or: one direct ChangeNOW contact corroborated (level 2), label lineages, false positives (a Binance hot wallet paying ChangeNOW 22 is service to service)",
     "Lineage counting and the service-to-service rule"),
    ("Branch `research/global-insider-forensics-20261102` (PR 12), `results/CHANGENOW.md`", "26 known wallets among 431,444 ChangeNOW payout recipients over 90 days (funding)", "Compared only"),
    ("Branch `feature/changenow-weekly-flows-20261114` (unpushed until this note)", "The collector, register (289 addresses), deposit-address rules and backward walker of `monitoring/changenow_weekly`; a provisional 2026-W46 report (46 withdrawal events, 34 accounts) whose second reading failed on 27 Relay deposits, fixed by uncommitted work of 2026-11-16",
     "The engine, published here unchanged apart from two batch-size settings; its 2026-W46 block-window rows, read again"),
    ("[PR 110](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/110)", "Weekly funding from ChangeNOW and Tornado Cash, 31 weeks on Polygon: no verified ChangeNOW funding, `0xf2020cbf…` rows kept at POSSIBLE; the provisional W46 totals above excluded as not reproducible",
     "Not modified; its stricter reading of `0xf2020cbf…` is shown as an alternative"),
    ("[PR 111](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/111)", "Bets of the four f2020-funded wallets of PR 110: per-market accounting with fees, first-buy test, 60 controls", "Not modified; its accounting copied unchanged into `scripts/pnl.py`"),
    ("Working folders of the archived studies, outside the repository (raw caches, knowledge graphs of the funding study)", "Raw histories behind the snapshots above", "Not read: kept on a disk that was not mounted during this census; everything used here is in the repository or read again from the chains"),
]


def table(header, rows, align=None):
    align = align or ["---"] * len(header)
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def money(x):
    try:
        return f"{float(x):,.2f}"
    except (TypeError, ValueError):
        return ""


def short(a):
    return f"{a[:6]}…{a[-4:]}" if a and len(a) == 42 else a


def addr(a, chain="Polygon"):
    return f"[{short(a)}]({EXPL.get(chain, EXPL['Polygon'])}/address/{a})" if a and len(a) == 42 else (a or "")


def txl(chain, tx):
    return f"[{tx[:10]}…]({EXPL.get(chain, EXPL['Polygon'])}/tx/{tx})"


def dur(s):
    try:
        s = int(s)
    except (TypeError, ValueError):
        return ""
    if s < 3600:
        return f"{s // 60} min"
    if s < 86400:
        return f"{s / 3600:.1f} h"
    return f"{s / 86400:.1f} d"


def read_csv(name):
    with open(RES / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def weeks_data():
    out = {}
    for p in sorted((NOTE / "data").glob("20*-W*/withdrawals.json.gz")):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            w = json.load(f)
        out[w["week"]] = w
    return out


def holm(pvals):
    """Holm step-down adjusted p-values, in the input order."""
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, running = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvals) - rank) * pvals[i]))
        adj[i] = running
    return adj


def main(argv=None):
    """report.py [results folder]: read the tables there and write the two pages next to them."""
    global RES
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        RES = Path(argv[0])
    summary = json.loads((RES / "summary.json").read_text())
    out_rows = read_csv("changenow_outflows.csv")
    ranks = read_csv("wallet_rankings.csv")
    weekly = read_csv("weekly_outflows.csv")
    fast = read_csv("fast_withdrawals_after_gains.csv")
    bets = json.loads((RES / "wallet_bets.json").read_text()) if (RES / "wallet_bets.json").exists() else {}
    weeks = weeks_data()
    est = [r for r in out_rows if r["evidence_class"] in build.ESTABLISHED]
    cls = summary["classes"]
    first, last = min(weeks), max(weeks)
    chains_read = Counter()
    for w in weeks.values():
        for c in w["chains"]:
            chains_read[CN.get(c, c)] += 1
    by_wallet = defaultdict(list)
    for r in out_rows:
        by_wallet[r["polymarket_wallet"]].append(r)

    # unusual results: first-buy calibration z over every resolved market, Holm across the wallets tested
    tested = [(w, b) for w, b in sorted(bets.items()) if (b.get("calibration") or {}).get("n", 0) >= 10 and b["calibration"].get("p_two_sided") is not None]
    adj = holm([b["calibration"]["p_two_sided"] for _, b in tested]) if tested else []
    unusual = [(w, b, a) for (w, b), a in zip(tested, adj) if b["calibration"]["z"] > 0 and a < 0.05]

    lines = [f"# Polymarket withdrawals to ChangeNOW, {first} to {last}", ""]
    lines += ["Polymarket trading wallets whose money reached an address attributed to ChangeNOW, read hop by hop on public chains, with what each wallet had won before. "
              "Outflows only. A withdrawal found here is a fact about wallets and transactions: it is not an exchange order, an identity or a sign of inside information.", ""]
    lines += ["## Answer", ""]
    top = [r for r in ranks if float(r["changenow_usd_established"] or 0) > 0][:5]
    lines += [f"- **Wallets.** At least **{summary['established_wallets']}** Polymarket trading wallets sent money to a ChangeNOW deposit address with every hop read on chain: "
              f"{cls['CONFIRMED_DIRECT']['wallets']} directly and {cls['SUPPORTED_INDIRECT']['wallets']} through an intermediate address or a bridge order "
              f"(a wallet can be in both). {cls['POSSIBLE']['wallets']} more wallets are possible only (a key that owns the wallet paid ChangeNOW, continuity of the funds not shown) "
              f"and {cls['UNRESOLVED']['transfers']} deposits stay unresolved. This is a minimum over the weeks and chains read, not a platform total.",
              f"- **Amount.** **{money(summary['established_usd'])} USD** in {cls['CONFIRMED_DIRECT']['transfers'] + cls['SUPPORTED_INDIRECT']['transfers']} transfers established "
              f"({money(cls['CONFIRMED_DIRECT']['usd'])} direct, {money(cls['SUPPORTED_INDIRECT']['usd'])} indirect), valued at the ChangeNOW-side transfer. "
              f"Possible: up to {money(cls['POSSIBLE']['usd'])} USD, an upper bound kept apart. "
              f"By attribution of the ChangeNOW end: {money(summary['by_grade'].get('A', 0))} USD through wallets with a public ChangeNOW label (grade A), "
              f"{money(summary['by_grade'].get('B', 0))} USD through wallets tied to them structurally (grade B).",
              "- **Largest senders.** " + ("; ".join(f"{addr(r['wallet'])} {money(r['changenow_usd_established'])} USD in {r['withdrawals_established']} transfer(s)" for r in top) or "none") + ".",
              ]
    won = [r for r in est if r.get("biggest_gain_24h_market")]
    lines += [f"- **Bets won just before.** {len(won)} of {len(est)} established transfers followed, within a day, a market the wallet closed at a gain; the largest are listed below and in "
              f"[interesting_wallets.md](interesting_wallets.md). A gain closed before a withdrawal is not shown to be the money withdrawn: the wallets' balances mix it with other funds.",
              f"- **Improbable streaks followed by fast withdrawals.** {len(fast)} wallet(s) sent money to ChangeNOW within a day of closing at least {build.FAST_GAIN_USD} USD of gains "
              f"(and at least half the amount sent). Over every resolved market, {len(unusual)} of {len(tested)} wallets tested beat the prices they paid at their first buy by more than chance "
              f"allows after a Holm correction across those wallets (first-buy test of PR 111).", ""]

    lines += ["## Totals by evidence class", ""]
    rows = [(c, cls[c]["wallets"], cls[c]["transfers"], money(cls[c]["usd"])) for c in build.CLASSES]
    lines += [table(["Class", "Wallets", "ChangeNOW-side transfers", "USD"], rows, ["---", "---:", "---:", "---:"]), ""]
    lines += ["- `CONFIRMED_DIRECT`: the wallet's debit and the arrival in the ChangeNOW deposit address are one transaction (a transfer from the wallet, or Polymarket's own unwrap of its collateral in that transaction).",
              "- `SUPPORTED_INDIRECT`: every hop read on chain, through an address that held almost nothing before (only what other money could not cover is attributed), a key that received the wallet's money, or a Relay order whose id is on both sides; or a Relay fill whose origin transaction Relay's own record names and the chain shows as a debit of the wallet (`link_source=relay_api`).",
              "- `POSSIBLE`: a key that owns the trading wallet (read on chain) paid a ChangeNOW deposit address, and no walk proved that the money came from the wallet. Amounts are upper bounds.",
              "- `UNRESOLVED`: the sender received money from a trading wallet, or the deposit came out of Polymarket's collateral ramp, but the walk stopped (mixed funds, asset changed, no inflow in the window).", ""]

    lines += ["## ChangeNOW end", ""]
    grade = defaultdict(lambda: [0, 0.0, set()])
    for r in est:
        g = grade[(r["changenow_chain"], r["changenow_endpoint_grade"], r["changenow_deposit_rule"])]
        g[0] += 1
        g[1] += float(r["usd"] or 0)
        g[2].add(r["polymarket_wallet"])
    lines += [table(["Chain", "Grade of the wallet swept into", "Deposit-address rule", "Established transfers", "Wallets", "USD"],
                    [(a, b, c, v[0], len(v[2]), money(v[1])) for (a, b, c), v in sorted(grade.items())], ["---", "---", "---", "---:", "---:", "---:"]), ""]
    lines += ["A ChangeNOW deposit address is one-time: the customer pays it, and the service sweeps it into a payout wallet. An address counts as one when, in the week, it paid a registered ChangeNOW payout wallet and either received its gas from the service's measured gas funder or is a plain key that signed at most two transactions in its life (rules and register of [`monitoring/changenow_weekly`](../../../monitoring/changenow_weekly/), unchanged). "
              "Each payout wallet is graded in [`inputs/endpoint_grades.csv`](../inputs/endpoint_grades.csv), with its labels, independent label lineages, structural evidence, counter-evidence and sources: "
              "A, a public ChangeNOW label from two independent lineages and service behaviour; B, a structural tie to a labelled ChangeNOW wallet, or a single lineage; C, behaviour only. "
              "A withdrawal is established only when the wallet swept into is graded A or B; a proven path that ends at a grade C wallet stays `POSSIBLE`. "
              "No payout wallet live in these weeks reaches grade A. On Polygon, `0xf2020cbf…` (stablecoins) is B: funded at creation by `ChangeNOW 22` (`0x4958f6c3…`, one label lineage) and the payer of a controlled ChangeNOW order in June 2026 ([case file](../../../investigations/changenow-polymarket/sources/case_03_firm_verdict.md)); "
              "the 42 % of its inflow once read as a sign of a shared hub comes from the Uniswap v3 DAI/USDT pool `0x254aa3a8…`, that is from swaps. `0x6976d802…` (POL) is C: tied to the service only through `ChangeNOW 22` and tagged as phishing by Blockscout on Ethereum. "
              "On Ethereum, `0x3f3ee0a9…` and `0x64cdaa89…` are B (funded at their first transaction by ChangeNOW Hot Wallet 4, service-scale behaviour). "
              "PR 110 keeps its own `0xf2020cbf…` funding rows at `POSSIBLE`; a reader who applies that stricter view here moves every Polygon row to `POSSIBLE` too, and the totals by grade below allow it.", ""]

    lines += ["## Weeks", ""]
    wrows = []
    for r in weekly:
        wrows.append((r["week"], r["wallets_established"], r["transfers_established"], money(r["usd_established"]), r["confirmed_direct_transfers"], r["supported_indirect_transfers"],
                      r["possible_transfers"], r["new_wallets"], r["recurring_wallets"], r.get("polygon_changenow_customer_deposits", ""), "yes" if r["week_closed"] == "True" else "no"))
    lines += [table(["ISO week (UTC)", "Wallets", "Transfers", "USD", "Direct", "Indirect", "Possible", "New wallets", "Recurring", "ChangeNOW customer deposits read on Polygon", "Week closed"],
                    wrows, ["---"] + ["---:"] * 9 + ["---"]), ""]
    lines += ["The reference date is the arrival in the ChangeNOW deposit address; `delay_seconds` in the outflow table gives the time from the Polymarket debit. A wallet counts once a week however many transfers it made. "
              "Possible and unresolved rows are counted apart and never added to the established totals.", ""]

    lines += ["## Largest senders", ""]
    rr = []
    for r in ranks[:20]:
        b = bets.get(r["wallet"], {})
        rr.append((r["rank"], addr(r["wallet"]), r["withdrawals_established"], money(r["changenow_usd_established"]), money(r["changenow_usd_possible_upper_bound"]),
                   money(r["realized_pnl_lifetime_usd"]), (r["biggest_win_market"] or "")[:60], money(r["biggest_win_usd"]), r["last_withdrawal_utc"][:10], r["confidence"],
                   "" if b.get("complete", True) else "capped"))
    lines += [table(["#", "Wallet", "Withdrawals", "ChangeNOW USD (established)", "Possible USD", "Realized PnL (lifetime)", "Largest win", "Win USD", "Last withdrawal", "Confidence", "Activity"],
                    rr, ["---:", "---", "---:", "---:", "---:", "---:", "---", "---:", "---", "---", "---"]), ""]
    lines += ["Three figures are kept apart: the realized result of the wallet over its whole history (closed markets, fees included), the profit realized before each withdrawal (in the outflow table), and the amount sent to ChangeNOW.", ""]

    if fast:
        lines += ["## Withdrawals within a day of a large gain", ""]
        lines += [table(["Wallet", "Such withdrawals", "Largest gains closed in a day before one of them (USD)", "Sent (USD)", "Largest gain market", "Gain USD", "Shortest time from gain"],
                        [(addr(r["wallet"]), r["withdrawals_after_gain"], money(r["gains_24h_before_usd"]), money(r["sent_usd"]), r["largest_gain_market"][:60], money(r["largest_gain_usd"]),
                          dur(r["fastest_seconds_from_gain"])) for r in fast[:25]], ["---", "---:", "---:", "---:", "---", "---:", "---"]), ""]
        lines += [f"Descriptive screen, not a test: a withdrawal is listed when the markets the wallet closed in the 24 hours before its debit gained at least {build.FAST_GAIN_USD} USD and at least {int(build.FAST_GAIN_SHARE * 100)} % of the amount sent.", ""]

    if tested:
        lines += ["## Results against the prices paid", ""]
        tr = sorted(((w, b, a) for (w, b), a in zip(tested, adj)), key=lambda x: x[1]["calibration"]["p_two_sided"])[:15]
        lines += [table(["Wallet", "Resolved markets", "Wins", "Expected at the prices paid", "z", "p", "Holm-adjusted p"],
                        [(addr(w), b["calibration"]["n"], b["calibration"]["wins"], b["calibration"]["expected_wins"], b["calibration"]["z"], b["calibration"]["p_two_sided"], round(a, 4)) for w, b, a in tr],
                        ["---", "---:", "---:", "---:", "---:", "---:", "---:"]), ""]
        lines += [f"One observation per market: the first buy, its price p, and whether that outcome won; under no information beyond the price, wins ≈ Σp (the test PR 111 settled on after its first version gave a biased z of 22 for a control). "
                  f"{len(tested)} wallets with at least 10 resolved markets were tested; the Holm correction runs across them. Short-dated crypto markets dominate several of these histories and their prices are not exactly calibrated, so a z near 2 is weak evidence.", ""]

    lines += ["## Earlier work", ""]
    lines += [table(["Source", "What it holds", "Used here"], AUDIT), ""]

    lines += ["## Coverage and limits", ""]
    cov = []
    for week, w in sorted(weeks.items()):
        for c, b in sorted(w["blocks"].items()):
            t = w.get("totals", {}).get(c, {})
            cov.append((week, CN.get(int(c), c), f"{b['first']}–{b['last']}", "yes" if b.get("closed") else "no", t.get("deposit_addresses", ""), t.get("customer_deposits", ""), money(t.get("usd_hourly_prices"))))
    lines += [table(["Week", "Chain", "Blocks", "Closed", "ChangeNOW deposit addresses", "Customer deposits", "Their USD (hourly prices)"], cov,
                    ["---", "---", "---", "---", "---:", "---:", "---:"]), ""]
    starts = Counter((x["category"], x["status"]) for w in weeks.values() for x in w["walks"])
    lines += [table(["Start of the walk", "Outcome", "Walks"], [(a, b, n) for (a, b), n in sorted(starts.items())], ["---", "---", "---:"]), ""]
    agree_path = NOTE / "data" / "relay_api" / "agreement.json"
    if agree_path.exists():
        ag = json.loads(agree_path.read_text())
        ok = sum(1 for v in ag.values() if v["agree"])
        lines += [f"Relay's public record (`api.relay.link/requests/v2`) was read for a fixed-seed sample of {len(ag)} fills the chain had already tied to an escrow deposit by their order id: it names the same origin transaction for {ok} of them.", ""]
    reasons = Counter(x["detail"].get("reason", "")[:90] for w in weeks.values() for x in w["walks"] if x["status"] == "UNRESOLVED")
    lines += ["Most frequent reasons a walk stopped:", ""]
    lines += [f"- {n} × {r}" for r, n in reasons.most_common(8)] + [""]
    lines += ["- Chains: Polygon is read in every week; Ethereum only in the weeks listed; Base, Arbitrum, Optimism, BNB Chain, Solana, Tron, Bitcoin and Monero are not read. A ChangeNOW deposit on those networks is invisible here.",
              "- ChangeNOW wallets: only the register's addresses (public labels and creation ties). A deposit address swept into an unregistered ChangeNOW wallet is not found.",
              "- Paths: collateral unwraps, Relay orders, single-asset pass-through and keys owning a wallet are followed. A swap on an exchange or a pool, another bridge (Across, deBridge, CCTP, Stargate) or a centralised exchange in between ends the walk.",
              "- Keys on Ethereum: a Polymarket key that bridged by itself and then paid ChangeNOW from Ethereum is found only through a Relay order; ownership is tested on Polygon senders only.",
              "- Senders with more than 2,000 transactions are set aside and counted: their funds are mixed.",
              "- Values are DeFiLlama prices of each token within an hour of the ChangeNOW-side transfer; no stablecoin is set to 1 by rule.",
              "- Bets: Polymarket's public activity feed; a capped read is marked. Fees before 2026-04-28 were taken in shares, which the feed does not show.",
              ""]
    lines += ["## Reproduce", "", "```sh", "python3 -I research_notes/changenow-withdrawals-2026-11-22/tests/test_withdrawals.py",
              "python3 -I research_notes/changenow-withdrawals-2026-11-22/verify.py", "```", "",
              "The collection commands are in the [README](../README.md). Raw block-window rows are not published; every transfer a table uses is in `data/<week>/withdrawals.json.gz`.", ""]
    (RES / "REPORT.md").write_text("\n".join(lines))

    # ------------------------------------------------------------------ interesting wallets
    pick = []
    for r in ranks[:10]:
        if float(r["changenow_usd_established"] or 0) > 0:
            pick.append((r["wallet"], f"rank {r['rank']} by amount sent"))
    for r in fast[:10]:
        pick.append((r["wallet"], f"{r['withdrawals_after_gain']} withdrawal(s) within a day of a large gain"))
    for w, b, a in unusual:
        pick.append((w, f"first-buy z {b['calibration']['z']}, Holm p {round(a, 4)}"))
    seen, chosen = set(), []
    for w, why in pick:
        if w not in seen:
            seen.add(w)
            chosen.append((w, [x for v, x in pick if v == w]))
    lines = ["# Accounts worth a closer look", "",
             "Chosen by rule, not by judgment: the ten largest established senders, the wallets that sent money within a day of a large gain, and the wallets whose first buys beat their prices after correction. "
             "Nothing here says who controls a wallet or why it moved money.", ""]
    for w, why in chosen:
        b = bets.get(w, {})
        rs = sorted(by_wallet.get(w, []), key=lambda r: r["changenow_arrival_utc"])
        lines += [f"## {short(w)}", "", f"Wallet {addr(w)} · why: {'; '.join(why)}", ""]
        if b:
            cal = b.get("calibration") or {}
            best = b.get("best") or {}
            lines += [f"- Activity: {b.get('rows')} rows{' (capped read)' if not b.get('complete') else ''}, {b.get('markets')} markets, first trade {build.utc(b.get('first_trade'))[:10]}, last {build.utc(b.get('last_trade'))[:10]}.",
                      f"- Realized result over closed markets: {money(b.get('realized'))} USD; largest: {best.get('title', '')[:80]} ({money(best.get('realized'))} USD).",
                      f"- First buys of resolved markets: {cal.get('n', 0)}, wins {cal.get('wins', '')} against {cal.get('expected_wins', '')} expected, z {cal.get('z', '')}."]
        lines += ["", table(["Arrival at ChangeNOW (UTC)", "Class", "Chain", "Amount", "USD", "Path", "Profit realized before", "Gain closed in the day before", "Share of collateral sent", "Transactions"],
                            [(r["changenow_arrival_utc"], r["evidence_class"], r["changenow_chain"], f"{r['amount']} {r['token']}", money(r["usd"]), r["path"] or r["link_source"],
                              money(r.get("realized_before_usd")), (f"{money(r.get('biggest_gain_24h_usd'))} on {r.get('biggest_gain_24h_market', '')[:50]}, {dur(r.get('seconds_from_biggest_gain_24h'))} before"
                                                                   if r.get("biggest_gain_24h_market") else ""), r.get("share_of_collateral_withdrawn", ""),
                              " ".join(txl(r["changenow_chain"], t.split(":")[1]) for t in r["underlying_transactions"].split(";")[:3]))
                             for r in rs], ["---", "---", "---", "---:", "---:", "---", "---:", "---", "---:", "---"]), ""]
    (RES / "interesting_wallets.md").write_text("\n".join(lines))
    print(f"REPORT.md and interesting_wallets.md written ({len(chosen)} accounts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
