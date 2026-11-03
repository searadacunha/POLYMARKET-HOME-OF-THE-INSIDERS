# Shadow detector: where the delays come from, and a research successor

Read on 2026-11-03. Replay only, on what the signal engine's collector kept. Nothing here is scheduled, sends anything, or changes PolySentinel or any sealed alert. No precision or recall exists: there is no ground truth, and neither engine reads outcomes.

## The delays of shadow-1

Tool: `engine/tools/shadow_latency.py`, output `results/shadow/latency_sources.json`. It reads the collector's state in short read-only pages. The state has grown since the first replay: 203,315 rows over 6.63 days, against 193,344 over 6.25 days in `results/shadow/status.json`. The 283 alerts are those of the first replay.

| Cause of the delay | Alerts | Median delay | 90th percentile |
|---|---:|---:|---:|
| Normal polling: delay under 600 s | 111 | 189 s | 337 s |
| Delay over 600 s, within an hour after a collection gap | 140 | 7.7 h | 40.5 h |
| Delay over 600 s, no recent gap | 32 | 7.7 h | 21.0 h |

The median of about 56 minutes and the 90th percentile of about 32 hours describe a mix. Half the alerts came out of backlogs.

- **Collection, not detection, sets the delay.** Gaps over 600 s add up to 88.5 hours, in 20 gaps, the largest about 34 hours, out of 159 hours of span. The collector was stopped or starved for more than half of the span. The disk pauses of those days are the likely cause, and this file did not establish it gap by gap.
- **Rows arrive late even without a gap.** Over all rows, the median of observation minus trade time is 4.3 hours, and 24% arrive more than a day late. Among rows that can enter the pattern (buys of at least $100 at 0.35 or less), the median is 54 minutes and the 90th percentile 39 hours. The collector samples markets in rotation, so that lag is built in.
- **84 of 283 alerts have all members seen in the same second.** One batch completed them. They could not have fired while the trades were happening.

## A defect found in shadow-1

**100 of 283 alerts group entries spread wider than the window they state.** Rows arrive in observation order, and the window only looks back from the row in hand, so a late row picks up entries that happened long after it. A synthetic case in `tests/test_shadow.py` shows entries spread over 2,100 s reported as a 5-second set. shadow-1's module and outputs are left as they were.

## shadow-2, in isolation

`engine/gf/shadow2.py`, output `results/shadow_v2/`. Each change answers a measure above:

- A set must fit inside its window, whatever the arrival order.
- Entries are kept by observation age, so a late row still meets its neighbours in trade time.
- A late row older than a trigger stays under the cooldown.
- Each alert says `LIVE` or `LATE`, whether one batch completed it, and whether a gap came within the hour. The hash chain covers these labels.
- Rates are counted per hour actually collected.

| Replay | shadow-1, same rows | shadow-2 |
|---|---:|---:|
| Alerts | 283 on 193,344 rows | 241 on 203,315 rows |
| Spread wider than the stated window | 100 | 0 |
| `LIVE`, delay at most 600 s | not labelled | 118 |
| `LATE` | not labelled | 123 |
| Hours collected, outside gaps | not counted | 70.7 |
| Alerts per collected hour | not counted | 3.41, of which 1.67 live |
| Delay of live alerts, median and 90th percentile | not separated | 186 s and 337 s |

The rows differ between the two columns because the collector kept running, so this table is no controlled comparison of the engines.

**What this does not say.** None of this is a prospective validation. An alert is a timing pattern. A rate of 1.67 live alerts per collected hour, about 40 a day if collection never stopped, is far too many to read by hand and gives no sign of being useful. Most tokens are ordinary, and the replay holds sports and esports markets. A real test needs the frozen study and a prospective run, and installing a service is a separate decision.
