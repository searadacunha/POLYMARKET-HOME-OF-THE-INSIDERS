"""Render the weekly report and a standalone SVG directly from the published rows."""

import csv
from decimal import Decimal
from .common import atomic


def chart(series):
    from html import escape

    weeks = list(series)
    small = [
        ("ChangeNOW · verified", "ChangeNOW", "funded_distinct", "funding_usd", "#176d65"),
        ("Tornado Cash · verified", "Tornado Cash", "funded_distinct", "funding_usd", "#334d85"),
        (
            "ChangeNOW · possible route",
            "ChangeNOW",
            "candidate_exact_pm",
            "candidate_exact_pm_usd",
            "#996320",
        ),
    ]
    base = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 530" role="img" aria-labelledby="title description">',
        '<title id="title">Observed Polymarket funding by ISO week</title>',
        '<desc id="description">Each row displays separate panels for unique wallets and USD. Horizontal small marks at the baseline denote observed zero. A cross denotes missing evidence. Panels have independent scales.</desc>',
        '<rect width="1100" height="530" fill="#faf9f5"/>',
        '<g font-family="system-ui,sans-serif" fill="#1b2528">',
        '<text x="28" y="36" font-size="24" font-weight="700">Weekly receipts at Polymarket trading addresses</text>',
        '<text x="28" y="60" font-size="14">Polygon trading accounts · verified paths and possible source attribution · ISO weeks, UTC</text>',
        '<text x="255" y="93" font-weight="600">Unique wallets</text><text x="682" y="93" font-weight="600">Weekly USD</text>',
    ]
    for i, (title, s, c, v, color) in enumerate(small):
        y = 126 + 124 * i
        base.append(f'<text x="28" y="{y + 25}" font-size="15" font-weight="600">{title}</text>')
        for x, field in ((255, c), (682, v)):
            vals = [
                None if series[w][s][field] == "UNKNOWN" else Decimal(str(series[w][s][field]))
                for w in weeks
            ]
            cap = max([z for z in vals if z is not None] or [Decimal(0)])
            width = 365
            base.append(f'<path d="M{x} {y + 67}h{width}" fill="none" stroke="#bfc7c4"/>')
            base.append(
                f'<text x="{x - 7}" y="{y + 5}" text-anchor="end" font-size="11">{cap:,.0f}</text>'
            )
            for j, val in enumerate(vals):
                xx = x + (j + 0.5) * width / len(vals)
                tooltip = escape(f"{weeks[j]} · {title} · {val if val is not None else 'UNKNOWN'}")
                if val is None:
                    base.append(
                        f'<text x="{xx:.2f}" y="{y + 68}" font-size="11" text-anchor="middle">×<title>{tooltip}</title></text>'
                    )
                else:
                    h = float(val / cap) * 62 if cap else 0.0
                    base.append(
                        f'<rect x="{xx - width / len(vals) * 0.3:.2f}" y="{y + 66 - h:.2f}" width="{width / len(vals) * 0.6:.2f}" height="{max(2.0, h):.2f}" fill="{color}"><title>{tooltip}</title></rect>'
                    )
                if j == 0 or j == len(vals) - 1 or (j % 5 == 0 and j < len(vals) - 2):
                    base.append(
                        f'<text x="{xx:.2f}" y="{y + 82}" text-anchor="middle" font-size="10">{weeks[j][-3:]}</text>'
                    )
    base += [
        '<text x="28" y="499" font-size="13">Each panel has its own scale. Baseline dashes = observed zero. × = unknown. USD uses dated quotes. Population coverage is partial.</text>',
        "</g></svg>",
    ]
    return "\n".join(base) + "\n"


def render(out, p, rows):
    series = p["series"]
    atomic(out / "weekly_funding.svg", chart(series).encode())
    weeks = list(series)
    last = weeks[-8:]
    f = lambda x: f"{Decimal(str(x)):,.2f}" if x != "UNKNOWN" else "UNKNOWN"
    lines = [
        "# Weekly funding intelligence",
        "",
        f"Offline snapshot for **{weeks[0]} through {weeks[-1]}**, ISO weeks in UTC. A case is a distinct Polygon trading address that received a documented credit. Weekly USD values price the final credited leg at the latest eligible daily quote. Global platform totals are **UNKNOWN**.",
        "",
        f"The last {len(last)} weeks contain **{len(set().union(*(set(p['sets'][w]['ChangeNOW']['funded']) for w in last)))} distinct ChangeNOW-funded accounts** and **{len(set().union(*(set(p['sets'][w]['Tornado Cash']['funded']) for w in last)))} distinct Tornado Cash-funded accounts** at the two accepted evidence levels. The table also gives the transfer value from the commingled route to exact trading addresses. A match there remains POSSIBLE.",
        "",
        "![Weekly wallet counts and USD](weekly_funding.svg)",
        "",
        "## Eight latest closed weeks",
        "",
        "| ISO week | ChangeNOW verified wallets | USD | Tornado verified wallets | USD | Possible ChangeNOW route, exact PM wallets | Possible USD | Verified intersection | Active PM addresses sampled |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    with (out / "wallet_funding.csv").open() as f_in:
        candidate = [
            r
            for r in csv.DictReader(f_in)
            if r["week"] in last
            and r["service"] == "ChangeNOW"
            and r["evidence"] == "POSSIBLE"
            and r["relationship"] == "exact_trading_address"
        ]
    candidate_accounts = {r["wallet"] for r in candidate}
    later = {r["wallet"] for r in candidate if r["traded_after"] == "YES"}
    value = (
        "UNKNOWN"
        if any(r["usd_price"] == "UNKNOWN" for r in candidate)
        else f"{sum((Decimal(r['amount']) * Decimal(r['usd_price']) for r in candidate), Decimal(0)):,.2f}"
    )
    location = lines.index("## Eight latest closed weeks")
    lines[location:location] = [
        f"Across that window the possible route supplied **{len(candidate)} transfers to {len(candidate_accounts)} distinct trading addresses, worth USD {value}**. {len(later)} of these addresses executed a later trade within the observation window.",
        "",
    ]
    for w in last:
        c, t = series[w]["ChangeNOW"], series[w]["Tornado Cash"]
        lines.append(
            f"| {w} | {c['funded_distinct']} | {f(c['funding_usd'])} | {t['funded_distinct']} | {f(t['funding_usd'])} | {c['candidate_exact_pm']} | {f(c['candidate_exact_pm_usd'])} | {len(p['sets'][w]['intersection'])} | {c['covered_active_pm']} |"
        )
    lines += [
        "",
        "## Full chronological ledger",
        "",
        "Recipients count observed chain/address pairs. ChangeNOW intake includes its separately classified commingled route and internal destinations. Direct and indirect columns count verified PM trading accounts only. New means first observed since the start of this snapshot. The change column compares observed funded accounts only where the source-window definitions match. Each rate uses the intersection with the independent same-week active sample.",
        "",
        "| Week | Service | Labelled/pool recipients | Mixed-route recipients | Exact PM recipients | Direct | Indirect | New | Traded later | Funding USD | ≥ $1k | ≥ $10k | Change | Funded in sample / sample | Unassigned recipients |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for w, v in series.items():
        for s, r in v.items():
            cells = [
                w,
                s,
                r["labelled_or_official_source_recipients"],
                r["commingled_route_recipients"],
                r["exact_pm_recipients"],
                r["confirmed_direct"],
                r["supported_indirect"],
                r["new_in_observed_history"],
                r["traded_after_observed"],
                f(r["funding_usd"]),
                r["funded_ge_1000_observed"],
                r["funded_ge_10000_observed"],
                r["delta_observed"],
                f"{r['funded_in_frame']} / {r['covered_active_pm']}"
                if r["covered_active_pm"]
                else "UNKNOWN",
                r["unassigned_recipient_pairs"],
            ]
            lines.append("| " + " | ".join(map(str, cells)) + " |")
    lines += [
        "",
        "## Coverage and interpretation",
        "",
        "- Polygon covers three allowlisted stablecoin Transfer streams from two labelled hot wallets, one consolidation address and the commingled f2020 rail, plus Withdrawal logs from four registered native pools. Ethereum covers two tagged hot wallets on USDC/USDT/DAI and six classic pools during the captured Ethereum log weeks. The existing native Ethereum explorer archive covers three tagged sources during its own time window. Every week and stream has an explicit status and block range in the JSON.",
        "- The independent denominator uses order owners observed in three predetermined eight-block windows on Polygon per week. Positive account enrichment uses an exact executed trade, documented historic accounts, and deterministic searches described in the README. Missing activity, same-hex Ethereum receipts and signer-only associations have their own classifications. A wallet address identifies an endpoint. Custody, control of the initial Tornado deposit, and who paid for a bet are separate questions.",
        "- An observed zero describes the searched sources and paths. The all-chain, whole-platform funding count, first-ever status, uncovered native/internal transfers, unregistered pools and general bridge attribution remain UNKNOWN. The current open week is outside this closed-week snapshot. Weekly differences also reflect sample composition, price coverage and left/right censoring.",
        "- USD for a proven native forward is the conservative lower bound after fees. The CSV keeps the receipt units and valuation timestamp. One transfer can finance several later trades or none. Per-wallet economic PnL is an API observation with its own timestamp. It never determines membership or service attribution.",
        "",
        "## Indirect paths",
        "",
    ]
    coverage_table = [
        "",
        "| Source stream | Fully bracketed weeks | Partial or archive-only weeks | No captured week |",
        "|---|---:|---|---|",
    ]
    for key in (
        "137/changenow",
        "137/tornado",
        "1/changenow",
        "1/tornado",
        "1/changenow_native_archive",
    ):
        full = []
        partial = []
        missing = []
        for week, streams in p["coverage"].items():
            state = streams[key]["status"]
            if state == "SCOPED_COMPLETE":
                full.append(week)
            elif state == "UNKNOWN":
                missing.append(week)
            else:
                partial.append(week)

        def show(items):
            if len(items) > 2 and [w for w in weeks if items[0] <= w <= items[-1]] == items:
                return f"{items[0]}–{items[-1]} ({len(items)})"
            return ", ".join(items) or "—"

        coverage_table.append(f"| {key} | {show(full)} | {show(partial)} | {show(missing)} |")
    where = lines.index("## Indirect paths")
    lines[where:where] = coverage_table + [""]
    h = p["historical_f2020_cohort"]
    lines.append(
        f"The archived f2020 sweep has {h['payees']:,} distinct payees, {h['bettor_records']} bettor records and {h['distinct_trading_addresses']} distinct lowercased trading addresses. Its lifetime totals cannot be allocated to individual weeks from that sweep alone."
    )
    lines.append("")
    metrics = p["path_screening"]
    if "polygon_native" in metrics:
        r = metrics["polygon_native"]
        lines.append(
            f"The native EOA screen covered {r['screened_intermediaries']} Polygon withdrawal recipients in {r['from']}–{r['through']}. It examined {r.get('candidate_send', 0)} simple onward-payment candidates. {r.get('terminal_without_indexed_trade', 0)} had no indexed trade at the terminal. {r.get('PAGE_CAP', 0)} address histories hit the page cap and {r.get('unavailable', 0)} lookups were unavailable. A successful proof requires the sender's nonce, code, receipt, fee and ending balance."
        )
    if "ethereum_to_polygon" in metrics:
        r = metrics["ethereum_to_polygon"]
        lines.append(
            f"\nThe historical Relay API screen queried {r['accounts_screened']} Ethereum recipients for onward orders to Polygon. It found {r.get('orders_in_window', 0)} successful orders in the eligible windows and {r.get('backed_routes', 0)} fully backed routes. {r.get('PARTIAL', 0)} histories were unavailable or incomplete, and {r.get('PAGE_CAP', 0)} reached the pagination cap. The v3 endpoint requires an API key, so the scheduled public capture excludes this optional screen."
        )
    if "signer_to_proxy" in metrics:
        r = metrics["signer_to_proxy"]
        lines.append(
            f"\nThe stablecoin screen queried {r['signer_pairs']} documented signer/proxy pairs and found {r['candidate_forwards']} temporally eligible same-asset forwards. The balance and complete intervening token ledger decide which can be counted. The archive supplied {metrics['relay']['exact_origin_transactions_screened']} distinct Relay origin transactions to compare by chain and hash. {len(metrics['relay']['exact_hits_pending_receipt_replay'])} matched and require two-leg verification before admission."
        )
    lines += [
        "",
        "## Statistical results",
        "",
        "| Endpoint | ChangeNOW | Tornado Cash | Required observations |",
        "|---|---|---|---|",
    ]
    for a, b in zip(p["statistics"][:5], p["statistics"][5:]):
        lines.append(
            f"| {a['endpoint']} | {a['status']} ({a['eligible_pairs']} pairs) | {b['status']} ({b['eligible_pairs']} pairs) | {a.get('reason', 'See JSON')} |"
        )
    lines += [
        "",
        "The frozen plan specifies ten comparisons, holdout purging and Holm adjustment. A NOT_TESTABLE endpoint has no observed p-value.",
        "",
        "[Weekly CSV](weekly_funding.csv) · [Wallet ledger](wallet_funding.csv) · [Coverage, sets, input hashes and statistics](weekly_funding.json) · [Method, scope and reproduction](../README.md) · [Audit](../AUDIT.md) · [Frozen protocol](../PROTOCOL.md)",
        "",
    ]
    atomic(out / "REPORT.md", "\n".join(lines).encode())
