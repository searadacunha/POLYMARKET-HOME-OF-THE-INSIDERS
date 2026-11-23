"""Render results/REPORT.md from the objects reconstruct.py computes. Numbers come from those objects, not typed by hand."""
from decimal import Decimal

PS = "https://polygonscan.com/tx/"
PA = "https://polygonscan.com/address/"
F2020 = "0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423"
REPO = "https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/blob/"
PR110 = REPO + "8b633048290e7174945bc811b16cf0b11b4d8ceb/investigations/weekly-funding-intelligence/"


def usd(x, nd=2):
    v = Decimal(str(x))
    return ("-" if v < 0 else "+" if v > 0 else "") + f"{abs(v):,.{nd}f}"


def plain(x, nd=6):
    return f"{Decimal(str(x)):.{nd}f}"


def pct(x, nd=1):
    return f"{float(x):.{nd}%}"


def short(a):
    return f"`{a[:6]}…{a[-4:]}`"


def tx(h, label="tx"):
    return f"[{label}]({PS}{h})"


def dur(s):
    s = int(s)
    d, r = divmod(s, 86400)
    h, r = divmod(r, 3600)
    m, r = divmod(r, 60)
    return (f"{d} d " if d else "") + (f"{h} h " if h or d else "") + f"{m} min {r:02d} s"


def level_a(w):
    return w["score_A"]


def level(flags):
    n = sum(flags.values())
    return "Low" if n == 0 else "Medium" if n == 1 else "High"


RANK = {"Low": 0, "Medium": 1, "High": 2}


def ranking(W):
    return sorted(W, key=lambda k: (-RANK[level(W[k]["score_C_flags"])], -RANK[level(W[k]["score_B_flags"])],
                                    -RANK[level_a(W[k])], -(W[k]["calibration_after"].get("z") or 0), k))


def flags_text(flags):
    on = [n.replace("_", " ") for n, v in flags.items() if v]
    return ", ".join(on) if on else "no flag"


def render(payload, focus_rows, ctx):
    W, M = payload["wallets"], payload["meta"]
    F = {r["wallet_id"]: r for r in focus_rows}
    L = []
    a = L.append
    a("# Funded bets of four f2020 payees: positions, outcomes and profit")
    a("")
    a("Follow-up of [PR 110](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/110). That PR lists four "
      "Polymarket trading addresses that bought shortly after a credit from the commingled `0xf2020c…c423` route, where "
      "ChangeNOW provenance is only `POSSIBLE`. This note reconstructs what each bet bought, at what price, how the position "
      "ended and what it earned after fees. It then rebuilds every later position of the same addresses. "
      f"Captures ran from {M['first_capture_utc']} to {M['last_capture_utc']}. Chain reads stop at Polygon block "
      f"{M['chain_last_block']:,} ({M['chain_last_block_utc']}). PR 110's files and conclusions are not modified.")
    a("")
    a("## Results")
    a("")
    a("| Wallet | Market | Exact position | Stake | Result | Net gain/loss | Delay after funding | Anomaly impression |")
    a("|---|---|---|---:|---|---:|---|---|")
    for r in focus_rows:
        w = W[r["wallet_id"]]
        res = f"{r['result']}: bought {r['outcome_bought']}, {r['outcome_won']} won"
        if r["sold_before_resolution"] == "YES":
            res += "; closed before resolution" if Decimal(r["redemptions"]) == 0 else "; first lot sold early, re-bought, redeemed"
        lb, lc = level(w["score_B_flags"]), level(w["score_C_flags"])
        overall = max(lb, lc, key=lambda x: RANK[x])
        net = f"{usd(r['net_pnl'], 6)} on the market; first lot alone {usd(r['first_lot_pnl'], 6)}"
        if Decimal(w["focus_third_party_payments"]) > 0:
            net += f"; {plain(w['focus_third_party_payments'])} more paid to a third party"
        a(f"| {r['wallet_id']} {short(r['wallet'])} | [{r['market']}]({r['event_url']}) | {r['exact_position']} | "
          f"{plain(r['first_stake_total'])} pUSD, fee {plain(r['first_fee'])} included | {res} | {net} | {r['delay_after_funding']} | "
          f"{overall} (A {level_a(w).lower()}, B {lb.lower()}, C {lc.lower()}) |")
    a("")
    a("Stake: the mission's transaction, price plus fee, in pUSD (Polymarket's USD collateral). Net: every cash flow of the "
      "address on that market, fees included, once it resolved. Result: whether the outcome bought in that transaction won. "
      "Delay: block time of the f2020 credit to block time of the first buy. The impression is the higher of B and C. The "
      "three scores are explained below. None of them is an accusation.")
    a("")
    a("### Ranking, most to least noticeable")
    a("")
    w1, w3, w4 = W["W1"], W["W3"], W["W4"]
    reasons = {
        "W3": (f"its only flag is statistical. After the funding its first buys won {w3['calibration_after']['wins']} of "
               f"{w3['calibration_after']['n']} 5-minute BTC markets, against {w3['calibration_after']['expected_wins']} implied "
               f"by the prices paid (z {w3['calibration_after']['z']}, p {w3['calibration_after']['p_two_sided']}). That is above "
               f"all {w3['controls']['with_z']} of its own controls and at the {pct(w3['controls']['z_percentile_pooled'], 0)} point of "
               f"the {payload['controls_pooled']['n']} pooled controls, without being significant. It enters "
               f"{pct(w3['updown_elapsed_at_first_buy_s']['share_within_30s'])} of windows within 30 s of the open, so it buys "
               f"before the window carries information. Net {usd(w3['after_funding']['net_pnl'])} on "
               f"{usd(w3['after_funding']['capital_engaged']).lstrip('+')} engaged. The credit was its only new money in the window."),
        "W1": (f"its bet used {pct(F['W1']['stake_share_of_balance'])} of its balance {F['W1']['delay_after_funding']} after a "
               f"credit worth {pct(F['W1']['funding_share_of_balance'])} of that balance, which ended a "
               f"{dur(w1['pause_before_funding_s'])} pause. Afterwards it bet at the same sizes as before (largest market "
               f"{usd(w1['max_stake_after']).lstrip('+')} against {usd(w1['max_stake_before']).lstrip('+')} before). Later it received "
               f"{usd(w1['external_inflow_by_counterparty'].get('0xba4eee20f434bc3908a0b18da496348657133a7e', 0)).lstrip('+')} USDC from an "
               f"unlabelled contract and {usd(w1['external_inflow_by_counterparty'].get('0x37f28b2bce699325795f05988bda358c40dab371', 0)).lstrip('+')} "
               f"pUSD from a key. Net {usd(w1['after_funding']['net_pnl'])}, z {w1['calibration_after']['z']}."),
        "W4": (f"a key-signed account (nonce {w4['account']['nonce']:,}) that received {w4['score_A_inputs']['f2020_receipts_W16_W46']} "
               f"f2020 credits from W16 to W46. The studied order was a 0.03 resting bid on the outsider, which lost. Later its first "
               f"buys did worse than their prices implied (z {w4['calibration_after']['z']}; first 30 days "
               f"{w4['calibration_first_30_days']['z']})."),
        "W2": (f"stakes of about a dollar, {W['W2']['after_funding']['sold_before_resolution']} of {W['W2']['after_funding']['markets']} later "
               f"positions with a sale before resolution, {W['W2']['third_party_fee_payments'][0]['small_payments']} small payments to a "
               f"third party, net {usd(W['W2']['after_funding']['net_pnl'])}, z {W['W2']['calibration_after']['z']}."),
    }
    for i, k in enumerate(ranking(W), 1):
        a(f"{i}. **{k}** {short(W[k]['wallet'])}: {reasons[k]}")
    a("")
    a("Not found for any of the four: a statistically supported edge, a run of long-shot wins, or a bet that preceded "
      "information the market did not already show.")
    a("")

    # ------------------------------------------------------------ per wallet
    a("## The four bets")
    for r in focus_rows:
        k = r["wallet_id"]
        w, c = W[k], ctx[k]
        acc = w["account"]
        a("")
        a(f"### {k} · [{r['wallet']}]({PA}{r['wallet']}) · [Polymarket profile](https://polymarket.com/profile/{r['wallet']})")
        a("")
        owner = f", owner `{acc['owners'][0]}`" if acc["owners"] else ""
        a(f"- **Account:** {acc['kind']}{owner}, nonce {acc['nonce']:,} at block {acc['block']:,}.")
        a(f"- **Funding:** {tx(r['funding_tx'])} at {r['funding_time']}: {plain(r['funding_amount'])} {r['funding_token']} "
          f"from `{F2020}`. The last activity before it was {dur(w['pause_before_funding_s'])} earlier. Balance just before the "
          f"first trade: {plain(r['balance_before_first_trade'])} pUSD, {pct(r['funding_share_of_balance'])} of it from the credit.")
        a(f"- **Market:** [{r['market']}]({r['event_url']}). Condition `{r['condition_id']}` "
          f"([Gamma](https://gamma-api.polymarket.com/markets?closed=true&condition_ids={r['condition_id']})).")
        a(f"- **Bought:** {r['outcome_bought']}, token `{r['token_id']}`, in {tx(r['bet_tx'])} at {r['bet_time']}: "
          f"{plain(r['first_shares'])} shares at {plain(r['first_price'], 4)}, fee {plain(r['first_fee'])}, filled as "
          f"{r['role_first_fill']}. The token id was recomputed on chain from the condition and outcome slot. It equals Gamma's "
          "`clobTokenIds` entry for that outcome.")
        a(f"- **Resolution:** {r['outcome_won']} won. The payout vector was read from the Conditional Tokens contract. "
          f"ConditionResolution {tx(r['resolution_tx'])} by oracle `{r['oracle']}`. Its question id equals Gamma's.")
        if "chainlink_price_to_beat" in c:
            a(f"- **Rule and prices:** Up if the Chainlink BTC/USD 60-second TWAP stream ends at or above its value at the window "
              f"start. Published start {plain(c['chainlink_price_to_beat'], 2)}, final {plain(c['chainlink_final_price'], 2)}, "
              f"margin {usd(c['chainlink_margin'])}. Binance BTCUSDT 1-second candles, an independent spot proxy and not the "
              f"resolution source, had moved {usd(c['binance_move_at_buy'])} when the order filled {c['elapsed_s']} s into the "
              f"window, and {usd(c['binance_move_at_end'])} at the end.")
            a(f"- **Same market:** {c['market_buyers']} buying addresses, {pct(c['buyers_main_side_won_share'])} of them with "
              f"their larger side on the winner. {c['same_outcome_wallets_within_30s']} other addresses bought {r['outcome_bought']} "
              f"within 30 s of this order, at {'–'.join(dict.fromkeys(c['same_outcome_price_range_30s']))}. "
              f"By notional this address ranks {c['wallet_notional_rank']} of {c['market_buyers']} (median buyer "
              f"{plain(c['median_buyer_notional'], 2)}).")
        else:
            a(f"- **Rule and readings:** the highest NOAA reading at Gimhae Intl Airport (RKPK) on the local day, in whole °C "
              f"([resolution source](https://www.weather.gov/wrh/timeseries?site=rkpk)). The Iowa Environmental Mesonet METAR "
              f"archive has {c['observations']} reports for {c['local_day']}. The day's maximum, {plain(c['day_max'], 0)} °C, "
              f"appears only in the {c['first_report_kst']} KST report. Without it the maximum is "
              f"{plain(c['max_without_first_report'], 0)} °C. When the order filled at {c['fill_kst']} KST, the last report was "
              f"{c['last_obs_before_buy']}. YES had traded at {c['other_outcome_min_price_10min_before']} or more in the previous "
              f"10 minutes. NO needed a later reading of at least one degree more than the maximum, or a resolution that left "
              "out the midnight report.")
            a(f"- **Same market:** {c['market_buyers']} buying addresses. {c['same_outcome_wallets_within_30s']} other addresses "
              f"bought NO within 30 s, at {'–'.join(dict.fromkeys(c['same_outcome_price_range_30s']))}. This "
              "address had a resting bid that sellers hit. When the bid was placed is off chain and unknown.")
        a(f"- **Whole position:** {plain(r['capital_engaged'])} pUSD engaged for {plain(r['shares_bought'])} shares, average "
          f"{plain(r['average_price_incl_fees'], 4)} with fees, fees {plain(r['fees'])}, sales {plain(r['sales'])}, redemptions "
          f"{plain(r['redemptions'])}, still held {plain(r['unredeemed_value'])}. Net {usd(r['net_pnl'], 6)} pUSD. Every operation "
          "is in [focus_operations.csv](focus_operations.csv).")
        secs = w["ops_seconds"]
        if k == "W1":
            a(f"- The first lot was sold {secs[1]} s later at 0.67. After two fees it lost "
              f"{plain(-Decimal(r['first_lot_pnl']))}. A new buy {secs[2]} s after the first was redeemed at 1.00 and carried "
              "the profit.")
        if k == "W2":
            a(f"- The direction was right. Holding the 3 shares would have paid 3.000000; the sale {secs[1]} s later returned "
              f"{plain(r['sales'])}. Around the two orders, small transfers to `0xdc9c35bf585fba2a39bcd17bdfe343277b595cad` add "
              f"{plain(w['focus_third_party_payments'])}. That address is a key, not a Polymarket contract, and not this deposit "
              "wallet's owner.")
        if k == "W4":
            a(f"- The second fill came {secs[1]} s after the first, at the same price. The NO shares were redeemed for 0, "
              f"{dur(secs[2])} later.")
    a("")

    # ------------------------------------------------------------ later bets
    a("## Every later position")
    a("")
    a("A position is a market whose first buy came at or after the funding. Data run to the last activity captured. Rows come "
      "from the complete paginated Polymarket v2 activity. Outcomes come from payout vectors read on chain: "
      + ", ".join(f"{k} {W[k]['chain_gamma_compared']} markets" for k in W)
      + " are also resolved in Gamma, and every one agrees. Shares still held are valued with their on-chain balance.")
    a("")
    a("| | W1 | W2 | W3 | W4 |")
    a("|---|---:|---:|---:|---:|")

    def ext(w, d):
        return sum(Decimal(e["amount"]) for e in w["external_transfers"] if e["direction"] == d and (d == "out" or e["counterparty"] != F2020))
    rows = [
        ("Markets (trades)", lambda w: f"{w['after_funding']['markets']} ({w['after_funding']['trades']})"),
        ("Still open at capture", lambda w: str(w["after_funding"]["open"])),
        ("First buy won / lost (market; weather event once)", lambda w: f"{w['calibration_after']['wins']} / {w['calibration_after']['n'] - w['calibration_after']['wins']}"),
        ("Profitable / unprofitable markets", lambda w: f"{w['after_funding']['profitable']} / {w['after_funding']['unprofitable']}"),
        ("With a sale before resolution", lambda w: str(w["after_funding"]["sold_before_resolution"])),
        ("Capital engaged (buys + fees)", lambda w: usd(w["after_funding"]["capital_engaged"]).lstrip("+")),
        ("Polymarket fees", lambda w: usd(w["after_funding"]["fees"]).lstrip("+")),
        ("Net PnL of the positions", lambda w: usd(w["after_funding"]["net_pnl"])),
        ("Rewards and rebates", lambda w: usd(w["rewards_and_rebates_after"])),
        ("Small payments to a third party", lambda w: usd(-sum(Decimal(x["small_total"]) for x in w["third_party_fee_payments"])) if w["third_party_fee_payments"] else "0.00"),
        ("Return on capital", lambda w: pct(w["after_funding"]["return_on_capital"])),
        ("Largest gain / loss", lambda w: f"{usd(w['after_funding']['largest_gain']['pnl'])} / {usd(w['after_funding']['largest_loss']['pnl'])}"),
        ("Top-3 markets, share of gains", lambda w: pct(w["after_funding"]["top3_share_of_gains"])),
        ("Main side at ≤ 0.20 (won)", lambda w: f"{w['after_funding']['longshot_bets']} ({w['after_funding']['longshot_wins']})"),
        ("Median / largest stake per market, before", lambda w: f"{float(w['median_stake_before']):.2f} / {float(w['max_stake_before']):.2f}"),
        ("Median / largest stake per market, after", lambda w: f"{float(w['median_stake_after']):.2f} / {float(w['max_stake_after']):.2f}"),
        ("Up/down entries: median s into window", lambda w: str(w["updown_elapsed_at_first_buy_s"]["median"])),
        ("Collateral at funding → peak → end", lambda w: f"{float(w['capital']['at_funding_block']):.2f} → {float(w['capital']['peak']):.2f} → {float(w['capital']['closing']):.2f}"),
        ("Other money in / out", lambda w: f"{ext(w, 'in'):.2f} / {ext(w, 'out'):.2f}"),
    ]
    for name, fn in rows:
        a(f"| {name} | " + " | ".join(fn(W[k]) for k in ("W1", "W2", "W3", "W4")) + " |")
    a("")
    for k in ("W1", "W2", "W3", "W4"):
        g, b = W[k]["after_funding"]["largest_gain"], W[k]["after_funding"]["largest_loss"]
        a(f"- {k}: largest gain {usd(g['pnl'])} on {g['title']} (`{g['condition_id']}`); largest loss {usd(b['pnl'])} on "
          f"{b['title']} (`{b['condition_id']}`).")
    a("")
    a("Net PnL adds sales, redemptions, merges and the payout value of shares still held, then subtracts buys and fees. "
      "Rewards, rebates and third-party payments are on their own lines. Every position is in "
      "[positions_after_funding.csv](positions_after_funding.csv).")
    a("")

    # ------------------------------------------------------------ apparent anticipation
    cp = payload["controls_pooled"]
    a("## Does any of it look like anticipation?")
    a("")
    a("The test uses one observation per market: the first buy, its price p and whether that outcome won. Brackets of one "
      "weather city-day count once. If the bettor knows nothing beyond the price, Σp is the expected number of wins and "
      "z = (wins − Σp) / √Σp(1−p). Later buys and sales do not enter, so averaging up after a move cannot inflate the score. "
      "Controls are 15 buyers per focus market with USD 0.5–20 there, taken in SHA-256 order of market and address without "
      "reading their results. Each gets the same test over the 30 days after the funding date.")
    a("")
    a("| | n | wins | expected | z | two-sided p | percentile among its controls | among all controls | z before funding |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k in ("W1", "W2", "W3", "W4"):
        c30, cb, ct = W[k]["calibration_first_30_days"], W[k]["calibration_before"], W[k]["controls"]
        a(f"| {k}, first 30 days | {c30['n']} | {c30['wins']} | {c30['expected_wins']} | {c30['z']} | {c30['p_two_sided']} | "
          f"{pct(ct['z_percentile'], 0)} of {ct['with_z']} | {pct(ct['z_percentile_pooled'], 0)} of {cp['n']} | {cb.get('z')} |")
    a("")
    a(f"Over the whole later period z is {W['W1']['calibration_after']['z']} (W1), {W['W2']['calibration_after']['z']} (W2), "
      f"{W['W3']['calibration_after']['z']} (W3) and {W['W4']['calibration_after']['z']} (W4). The smallest first-30-day p among "
      f"the four wallets is {min(W[k]['calibration_first_30_days']['p_two_sided'] for k in W)}, against 0.05/4 = 0.0125 after a "
      f"correction for four tests. Control z values run from {cp['min']} to {cp['max']} (median {cp['median']}), and "
      f"{pct(cp['share_abs_z_ge_2'])} of controls have |z| ≥ 2. Ordinary small traders of the same markets therefore spread "
      "more widely than a normal curve.")
    a("")
    a("Timing points the same way. W3 enters within 30 s of the window opening in "
      f"{pct(W['W3']['updown_elapsed_at_first_buy_s']['share_within_30s'])} of its {W['W3']['updown_elapsed_at_first_buy_s']['n']} "
      "up/down markets, when the window has produced no information. On BTC 5-minute markets with a measurable Binance move "
      f"at entry, W1 followed the move in {W['W1']['btc5m_with_visible_move']['with_move']} of "
      f"{W['W1']['btc5m_with_visible_move']['bets']} and W2 in {W['W2']['btc5m_with_visible_move']['with_move']} of "
      f"{W['W2']['btc5m_with_visible_move']['bets']}. Base rate for the delay: PR 110 has {payload['delay_base_rate']['receipts']} "
      f"f2020 receipts followed by a buy. 10% were followed within {payload['delay_base_rate']['quantiles_s']['0.1']} s and half "
      f"within {payload['delay_base_rate']['quantiles_s']['0.5']} s. W1's delay sits at the "
      f"{pct(W['W1']['focus']['delay_percentile_vs_f2020_receipts'], 0)} point.")
    a("")

    # ------------------------------------------------------------ scores
    a("## Three separate scores")
    a("")
    a("| Wallet | A. Provenance opacity | B. Behavioural anomaly | C. Apparent informational advantage |")
    a("|---|---|---|---|")
    for k in ranking(W):
        w = W[k]
        ai = w["score_A_inputs"]
        share = ai["f2020_share_of_inflow"]
        n = ai["f2020_receipts_W16_W46"]
        a(f"| {k} | {level_a(w)}: one hop from the commingled rail, originator not visible on chain; {n} f2020 "
          f"credit{'s' if n != 1 else ''} W16–W46; f2020 = {'n/a' if share in (None, 'None') else pct(share)} of new money in the "
          f"window | {level(w['score_B_flags'])}: {flags_text(w['score_B_flags'])} | {level(w['score_C_flags'])}: "
          f"{flags_text(w['score_C_flags'])} |")
    a("")
    a("**A** is High when the rail recurs (at least 10 credits) or brings at least half of the new money in the window. "
      "Otherwise it is Medium. Low would need an attributable originator, which f2020 never gives. **B** counts four flags: "
      "delay at or below the 10th percentile of the f2020 base rate; median stake after funding at least 3 times, or at most a "
      "third of, the median before; top three markets ≥ 50% of gains; focus stake ≥ 50% of the balance. **C** counts four: "
      "the focus bet won while buying against the visible move; first-30-day z ≥ 2; z ≥ 3; z above 95% of its own controls. "
      "0 flags = Low, 1 = Medium, 2 or more = High. These rules were written in this session after the first descriptive "
      "numbers had been seen, not preregistered. One wallet's score says nothing about the other axes.")
    a("")

    # ------------------------------------------------------------ uncertain observations
    big = W["W2"]["third_party_fee_payments"][0]
    a("## Observations kept with their uncertainty")
    a("")
    a(f"- The mission gives wallet 4 as `{payload['mission_wallet4_as_given']}`, 39 hex digits, so not a valid address. Its "
      "first 29 hex digits are those of `0xadd9ab62…8df9`. Its last 10 are those of `0xe129d1e0…cc9361`, another f2020 payee in "
      "W39–W46 for which PR 110 observed no later trade. The mission's amount, time, block and bet transaction all belong to "
      "`0xadd9ab62b2c22151c661b99821cbb7433df98df9`, which is the address studied here.")
    a("- Chainlink's TWAP stream is off chain. The start and final values are Polymarket's published `eventMetadata`, not "
      "recomputed. Binance spot moved the same way in all three BTC markets, but it is only a proxy.")
    a("- The Busan readings come from the IEM METAR archive, not a capture of the NOAA page. The official outcome, YES at "
      "22 °C, can only be reproduced if the 00:00 KST report counts in the local day.")
    a("- W1's later USDC arrives from `0xba4eee20f434bc3908a0b18da496348657133a7e`, an unlabelled contract. In "
      "[an earlier funding graph](../../investigations/edge-polymarket/sources/funding/data/graphe/0xf54dae096aaf3d18c417ecfb454512191902b546.json) "
      "of this repository it pays 49,987.45 USDT twice on 16 November 2024. W1's pUSD outflows go to "
      f"{W['W1']['external_outflow_counterparties']} contracts with no Polymarket activity. Whether they are bridge deposit "
      "addresses, exchanges or something else is not established.")
    a(f"- W2's recipient `0xdc9c35bf…5cad` took {big['small_payments']} payments of at most {plain(big['small_max'])} "
      f"({plain(big['small_total'])} in total) and {big['larger_transfers']} larger transfers "
      f"({plain(big['larger_total'])}). It also sent W2 "
      f"{plain(W['W2']['external_inflow_by_counterparty']['0xdc9c35bf585fba2a39bcd17bdfe343277b595cad'])} once. Reading the "
      "small ones as an app or bot fee comes from their pattern only.")
    lv = {k: W[k]["lifetime_vs_user_pnl"] for k in W}
    diffs = ", ".join(f"{k} {usd(v['difference'], 6)}" for k, v in lv.items())
    a("- Lifetime PnL rebuilt from the rows, compared with Polymarket's `user-pnl` point that PR 110 recorded at "
      f"{lv['W1']['at']}: differences {diffs}. W4's gap is of the "
      f"order of the {plain(lv['W4']['reconstructed_unredeemed_value'], 2)} this method assigns to shares the API still shows as "
      f"held, {plain(lv['W4']['of_which_opened_before_2026_04_28'], 2)} of it from positions opened before 28 April 2026, when "
      "fees were taken in shares and API share counts run high. Those older balances were not read on chain, so the gap "
      f"stays unresolved, and so does W1's {usd(lv['W1']['difference'], 6)}. After the funding no such gap exists: API cash "
      "equals the on-chain transfers (see Method).")
    a(f"- {M['controls_capped']} of the {M['controls_total']} control histories hit the 10,000-row capture cap. Their "
      "positions stop one day before the cap.")
    a("- First version of the test: it used each market's side with the larger buy and that side's average price. One control "
      "scored z = 22 that way by buying a side after it had moved, so the test was switched to the first buy. The first version "
      "gives, over the first 30 days, " + ", ".join(f"{k} {W[k]['calibration_main_side_first_30_days']['z']}" for k in W)
      + ". In neither version does any wallet reach z = +2.")
    a("")

    # ------------------------------------------------------------ method
    a("## Method")
    a("")
    a("1. **Activity:** `data-api.polymarket.com/v2/activity` returns every type in ascending order, read with its cursor until "
      "`has_more` is false. Profile fields are dropped on read. PR 110's sampled buys are all present: "
      + ", ".join(f"{k} {W[k]['pr110_sampled_buys_found']}/{W[k]['pr110_sampled_buys']}" for k in W) + ".")
    a("2. **Receipts:** the funding and every transaction on the four focus markets are decoded from Polygon receipts "
      "(`OrderFilled`, ERC-1155 and ERC-20 transfers). Each running position equals `balanceOf` at the same block. Each API "
      "amount on those markets equals the decoded receipt.")
    a(f"3. **Outcomes:** `payoutNumerators` and `payoutDenominator` are read at block {M['payout_block']:,} for the "
      f"{M['payout_conditions']:,} markets touched after the funding. Position ids are recomputed with `getCollectionId` and "
      "`getPositionId`.")
    a(f"4. **Ledger:** every USDC, USDC.e and pUSD transfer of each wallet, from 2,000 blocks before its funding to block "
      f"{M['chain_last_block']:,}. Opening balance plus replayed transfers equals the closing `balanceOf` for all four. In the "
      "transactions the API lists, on-chain cash equals API cash, with gaps of "
      + ", ".join(f"{k} {W[k]['ledger']['api_gap']}" for k in W) + ".")
    a("5. **PnL:** per market, sales + redemptions + merges + payout value of shares still held − buys (fees included). A "
      "redemption zeroes the redeemed token, because `redeemPositions` burns the whole balance.")
    a("6. **Controls, base rate and scores:** as above.")
    a("")
    a("Reproduce offline from the repository root: `python3 -I research_notes/f2020-bet-reconstruction-2026-11-22/verify.py`. It "
      "blocks network sockets, rebuilds every file in `results/` in a temporary folder and compares the bytes. To recapture, "
      "run `python3 -I scripts/collect.py <step>` from the note folder. That step uses the network.")
    a("")
    a("## Limits")
    a("")
    a("- Funding is traced one hop back. The ChangeNOW order, the depositor and the people behind the addresses are not "
      "identified.")
    a("- The test looks for a persistent edge. It cannot rule out one informed bet among many uninformed ones, and four "
      "wallets give little power.")
    a("- Order placement times are off chain. For a maker fill such as W4's, the moment of decision is unknown.")
    a("- Controls come from the same focus markets. They stand for small traders of those markets, not the whole platform.")
    a("")
    a(f"PR 110 inputs, pinned at its head: [wallet_funding.csv]({PR110}results/wallet_funding.csv) · "
      f"[weekly_funding.csv]({PR110}results/weekly_funding.csv) · [weekly_funding.json]({PR110}results/weekly_funding.json) · "
      f"[accounts snapshot]({PR110}snapshot/accounts.json.gz)")
    a("")
    return "\n".join(L)
