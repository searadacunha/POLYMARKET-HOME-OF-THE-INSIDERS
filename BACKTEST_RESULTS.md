# Backtest results

What the monitor would have said on the cases already in this repository, replayed in the order things happened, and
what it says on markets nobody had looked at. Rule and statistics: [PATTERN_RESEARCH.md](PATTERN_RESEARCH.md). Monitor:
[monitoring](monitoring/README.md).

**In short.** The monitor raises its strongest alert on two documented cases, hours before anything was public, and
each time on an account the case file names. It raises nothing on the other documented cases. On 570 unselected
ignitions the same alert names the winning side no more often than the price does. So it detects one kind of trading
early; it does not tell an informed trader from a lucky or reckless one.

## The documented cases

Times are UTC. "Public" is the first public information the repository holds for the case; where the repository marks
that time as approximate, so is the lead.

| Case | Alert | When | On which account | Lead over the public event | Was the account already in the case file |
|---|---|---|---|---|---|
| Nobel Peace Prize 2025, Machado | `LONELY_THIN` | 9 Oct 2025, 23:00:15 | `0xa430506774f9efaf39903ee7e0db1351f66891ca` ("6741") | 10 h 00 before the announcement of about 09:00 | yes |
| same, group of the funder | cluster | 10 Oct 2025, 00:50 to 03:30 | the seven other accounts of `followup-20261113`, exactly | 8 h 10 to 5 h 30 | yes, all seven |
| same, second group | group | 10 Oct 2025, 07:50 | two accounts opened that morning (NB-2 of [NEW_LEADS.md](NEW_LEADS.md)) | 1 h 10 | no: new |
| Maduro, "out by February 28, 2026?" | `LONELY_THIN` | 3 Jan 2026, 04:03:21 | `0x6baf05d193692bb208d616709e27442c910a94c5` ("SBet365" in the Maduro file) | 2 h 12 before the market repriced (06:15:41); 5 h 18 before the announcement of about 09:21 | yes |
| Maduro, "out by January 31, 2026?" | none | | | | the same account bought 10,000 USD there at 03:42:01 without moving the price |
| Iran, "Will US or Israel strike Iran by February 28, 2026?" | `LONELY_THIN` | 27 Feb 2026, 12:40:21 | `0x3b0e78922dc33eb903968c00c6a12580f0bb50c1` | 17 h 43 before the Israeli announcement (28 Feb, 06:23) | no; 1,495 USD, a small position |
| Iran, "US strikes Iran by February 28, 2026?" | `LONELY` | 27 Feb 2026, 10:50:16 | `0x37d10ffb61998561c5f9fb941c42c952d8fb4e28`, an established account | 19 h 33 | no |
| Iran, the 38 accounts of 27 February | none | | | | they bought as a crowd that evening; no single account moved the price |
| Israel and Iran, June 2025 | none | | | | the move of 12 June at 23:43 was bought by 38 wallets |
| Ballon d'Or 2026 | none | | | | 14 markets in the population, no price ignition in any |
| Biden pardons | none | | | | no price ignition |
| Google Year in Search 2025 | none | | | | 46 markets, 2 price moves, neither confirmed by trades |
| KPMG earnings | none | | | | 2 of 21 markets large enough to be in the population |

**What each alert knew at its time.** Every alert is computed from prices and trades dated before it and from the
account's history before its first buy. For the Nobel alert: a six-hour median price of 0.016 and a price of 0.39 at
23:00; one account with no trade before, funded less than three minutes before its first buy by a key that had made one
transaction, supplying 97 % of 14,705 USD in fifteen minutes and paying from 0.048 up to 0.30. For the Maduro alert:
one account with a single trade before, first seen four days earlier, supplying 96.7 % of the buying, 15,090 USD.

**Early detection or reconstruction.** The rule was written from the Nobel night, so that alert is a reconstruction
of its own source, even though each step uses only what was known at the time. The Maduro and Iran alerts are not:
the rule was fixed before those markets were read, and it was applied to them as written. The cluster and the second
group of the Nobel night come from the funding follow-up, which was written after the first Nobel analysis and has
been run on that night only.

**What it missed, and why.** The largest documented Maduro position was built over three days in a deep market
without moving its price. The 38 Iran accounts bought together within three hours. Neither is a single wallet
lifting a quiet price, and neither raises anything. The monitor sees one mechanism.

## Markets never examined before

From the frozen study: every Yes/No market of the population closed between January 2025 and October 2026, 34,413
markets, documented cases set aside.

| | |
|---|---|
| Alerts of the tested class | 45 in 96 weeks: one every two weeks |
| Named the winning side | 13 of 45: 28.9 % (17.7 to 43.4) |
| Mean price at the alert | 25.4 % |
| Excess over the price | +3.5 points, p = 0.33: none shown |
| Alerts whose side lost | 32 of 45 |
| From first buy to alert | 15 minutes at the median, 65 minutes at the 90th percentile |
| For the 13 winners, from the alert to a price of 0.95 | 1.3 h to 212 h, median about 23 h |

**Without its most important variable.** Drop "thin" and keep "one wallet did most of the buying": 362 alerts
instead of 45, almost four a week, winning 35.9 % against a price of 33.9 %. On the documented events the same
change adds seven alerts, four of them on the losing side. Drop "lonely" and keep "thin": 49 alerts, 32.7 % against
25.4 %. Neither variable alone, nor both together, separates winners from losers in the validation.

**By kind of market.** Of the 45 alerts, 21 are on politics, 13 on geopolitics, 9 on technology. The numbers per
category are too small to compare.

**Calibration.** The alert carries no probability. What can be said of an alert of the tested class is the table
above: in two years of markets it named the winning side 29 % of the time, when the price said 25 %.

## What was not possible

- **Precision and recall on insiders.** There is no list of informed accounts. Two alerts landing on accounts that
  case files already name is a check that the monitor sees what those files saw, not a precision.
- **False positives per day** cannot be counted without that list. What can be counted is load: 0.47 alerts a week,
  of which seven in ten name the side that lost.
- **Market makers and bots.** The "thin" condition removes accounts with a history by construction. Among the 362
  alerts on any account, how many are market makers was not measured.
- **Lead over public information, in general.** A sourced time of first public information exists for three cases
  and is approximate for two of them.
- **A live alert.** None has been raised in the short live runs; see [LIVE_DETECTION.md](LIVE_DETECTION.md).

## Reproduce

```sh
cd monitoring
python3 -m unittest discover -s tests -v          # replays the Nobel evening offline from a fixture
python3 -m phi_monitor backtest --db /tmp/nobel.sqlite \
    --token 75406677405586796507165996816755205915219135539748390183994296030461533919844 \
    --start "2025-10-09 12:00" --end "2025-10-10 09:00"
python3 -I ../research_notes/early-detection-2026-11-13/verify.py
```

The Nobel timeline is in [bt_nobel_result.json](research_notes/early-detection-2026-11-13/data/bt_nobel_result.json).
The Maduro and Iran rows come from the analytic table of the study
([analytic_table.jsonl](research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl), rows marked
`DISCOVERY`), which applies the same rule with the same code.
