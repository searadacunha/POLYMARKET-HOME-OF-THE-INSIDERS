# Step 6: executable edge, not paper alpha. Limits and verdict

Study: `collective-exposure-shifts` (Polymarket). Step 6 of 7. Written 2026-11-17 by Claude Code (Opus 5.5).
Grid fixed before any execution figure: `prereg/GRID.json`, sha256 `6a99a1a1e8b756b8d46426fa6703e7be5bac05a7db1b7782d0eb1b1d64d05e2c`,
written 2026-11-17T09:25:53Z. After an independent audit of the first run, amendment
`prereg/amendements/001-2026-11-17-post-audit.md` (sha256 `78e05905…f9bf1`) corrected six implementation defects
and added two descriptive readings; nothing in it changes the grid, the stop rule or the verdict. Figures below
are from the corrected run (`out/`); the first run is kept unchanged in `out_v1/` with its code.

## Verdict: `NO_DEMONSTRATED_EDGE`

- **Stop rule triggered.** No declared test of the input statistics passes Bonferroni and BH
  (`replication_tests.json`, sha256 `4fcffe96…c4c3`, verdict `NOT_SUPPORTED`; T1 to T7 all false). The signal is
  not statistically valid, so no strategy was optimised; the replay below was run once, on the grid fixed in
  advance, as a descriptive record.
- **Historical execution: `UNVERIFIABLE`.** No order book exists for the alert times (see below). Every
  number in `TRADE_REPLAY.csv` is a HYPOTHETICAL simulation from the trade tape, never a verified execution.
- **The hypothetical replay does not contradict the stop rule.** Headline cell fixed in advance (causal
  trigger, 300 s latency, 100 USD, "politics" costs, TEST): −17.50 USD on 2,160.15 USD spent, −0.8 % per USD,
  event-clustered 95 % CI [−21.8 %, +19.3 %], 26 of 48 TEST alerts executable. 0 of the 54 TEST cells has a CI
  excluding zero; 16 of 54 TEST cells and 13 of 54 all-split cells are net positive.

This verdict says the edge is **not demonstrated**. It does not say an edge of a few points is excluded: the CIs
are about ±20 points wide.

## Which statistical results were read

Mission 5/7 (falsification, session 74b0b42c) was launched at the same time as this step, on 17/11 around 09:10,
and had written no `STATISTICAL_RESULTS.json` when this step started. The only frozen statistical results
available are those of the 16/11 study (`PROTOCOL.lock` frozen 2026-11-16T22:40:18Z, replication of amendment
002: 1,579 markets, 266 primary S4 alerts in 197 events, 48 in TEST). `code/replay.py --stats <file>` reruns
everything on another statistics file; if step 5 later declares a valid signal, the stop rule no longer applies
and the verdict must be recomputed (the code then returns `NO_DEMONSTRATED_EDGE` if the hypothetical headline
is not positive with a CI above zero, otherwise `UNVERIFIABLE`; never `NET_EDGE_SUPPORTED`, because no execution
can be verified historically). The statistics gate refuses a file whose schema it does not know instead of
reading it as "no significant test", so `STATISTICAL_RESULTS.json` will need an explicit mapping.

## Per alert: what was reconstructed and how

| Required item | What this step does | Status |
|---|---|---|
| First instant all detection data is available | Alert at grid time `t` uses fills ≤ `t`; they are usable once the data-api has indexed them. Availability = trigger + latency. | Indexing lag NOT measured in this repository: assumption |
| Trigger time | **Causal**: first S4 candidate of the (market, side), from the frozen `evaluate_market` without its suppression step; its own price is the reference. **Frozen**: the frozen alert time and price. | 117 of 266 frozen times are later than the first candidate (all 266 reproduced) |
| Earliest live emission by the frozen code | The frozen detector evaluates a grid time only once a later fill exists (`t ≤ last_ts`). Delay from the causal grid time to that fill: median 100 s; ≥ 60 s for 162, ≥ 300 s for 74, ≥ 900 s for 39 of 266 alerts | The 60 s latency is unreachable for most alerts with the frozen code as written |
| Latency | 60 s (automated), 300 s (conservative automated or fast human), 900 s (next grid evaluation) | Fixed grid |
| Best purchasable price after availability | Ask levels revealed by the tape: maker SELL legs of the token, maker BUY legs of the complement (1 − p), in transactions whose taker is identified | Proxy, not the book |
| Spread and depth | NOT observable historically. Observed ask notional in the 15-min window, on windows with at least one identified taker, is a lower bound of what was offered: median 231 USD all splits, 80 USD in TEST (headline latency) | Partial |
| Fees, slippage, costs | 3 scenarios: 0 / 0.04 + 0.001 / 0.07 + 0.002 per share, `fee_rate·p·(1−p)` on entry, gas 0 | Scenarios, not charged fees |
| Executable size and net PnL | 10, 100, 1,000 USD; unfilled remainder is not executed | Hypothetical |
| Price-only control | Same market and side, 5 seeded times where the side's last price is within ±0.05 of the trigger price, ≥ 6 h from any S4 candidate of that market and side, same fill model; draws and fills counted | Hypothetical; only 117 of 1,071 draws find ask evidence (headline cell) |

Never used: a midpoint, a price before the trigger, or an invented fill for a missing ask.

## Historical order book: not available

Checked on 17/11/2026 (sources in `evidence/BOOK_AND_FEES_SOURCES.md`):

- Polymarket: `/book` and `/books` take a token id only and return the current book; no history endpoint.
  `/prices-history` returns one "observed price" per point (no bid, ask or size). The orderbook subgraph stores
  fills (`OrderFilled`, `OrdersMatched`), never resting orders.
- Third-party archives, all recorded live: Telonex from 11/10/2025, Dome from 14/10/2025, PredictionData from
  11/2025, TickFoundry and PMXT from 02/2026, Marketlens from 03/2026. All paid except PMXT (free, hourly, from
  2026-02-21T16:00Z; its host refused or timed out from this machine). One vendor claims history "from each
  market's creation date" without a method or start date: unverified.
- Local: the repository's live collector (`~/phi-live`) holds full books since 14/11/2026 for 20 tokens; the
  alerts end on 31/10/2026, so there is no overlap.

So for the TRAIN split (2025) the book cannot be rebuilt by anyone in public; for VALID and TEST only paid
archives (or PMXT, unreachable here) might cover part of it. Not done here: no paid service, no account.

## Fees actually in force (2025-01 → 2026-10)

- Before 2026-03-30: no trading fee on politics, geopolitics, culture or business markets (Polymarket docs,
  archived June 2025 and January 2026). The "optimistic" scenario is therefore the historical one for TRAIN and
  for VALID up to 29/03/2026.
- From 2026-03-30 (Fee Structure V2), taker only: politics 0.04, culture and economics 0.05, geopolitics 0,
  formula `C·feeRate·p·(1−p)` from 01/04/2026. The "politics" scenario matches politics markets; culture markets
  sit between "politics" and "stress".
- Not verified: whether markets created before 30/03/2026 became fee-bearing, and when (docs said "pre-existing
  markets are unaffected" until at least 14/04, then "determined per market at match time"). The charged fee of
  each fill is on-chain (`OrderFilled.fee`, `FeeCharged`), not in the data-api tape: it was not read here.
- The grid was not changed after this check; the scenarios bracket the documented rates.

## Execution model: known biases

- **Coverage.** 75 % of transactions are one-to-one matches (64,586 of 86,327 in 40 sampled markets) whose
  taker cannot be identified, so they are never used as ask evidence. Half the alerts get no ask evidence in
  15 minutes (133 of 266 at the headline latency): 58 with no transaction at all, 36 with ambiguous transactions
  only, 39 with identified takers on the other side only. Capacity is understated.
- **Selection (missing not at random).** An alert is executed only if a multi-maker sweep of its side follows the
  trigger, which may correlate with the outcome. At the trigger price, executed alerts gross +3.5 cents per share
  (n = 133, win rate 71.4 %, mean price 0.679) against −2.0 cents for non-executed ones (n = 133, 72.2 %, 0.742);
  in TEST +6.4 against −5.0 cents (26 and 22 alerts). The executed PnL is therefore, if anything, optimistic.
- **Same-second order.** Transactions of the same second are walked in hash order (the tape has no log index);
  the independent recomputation found this changes one alert's fill in the audited cell (net −165.84 vs −165.72 USD).
- **Population.** Inherited from 13/11: markets resolved to 1/0 with final volume between 10 k and 1 M USD, both
  known only after the fact. The paper trader applies the volume rule to current volume and cannot apply the
  resolution rule, so replay and prospective populations differ by construction.
- **Identification check.** In the 21,714 multi-maker transactions sampled, the identified taker's price equals
  the size-weighted price of its makers in 100 % of cases (to 0.001) and every maker leg is on the opposite side.
- **Competition.** The simulated order takes liquidity that a real taker took; a real order would have moved the
  book. Fills are therefore optimistic on availability and pessimistic on price (the evidence comes from sweeps).
- **Fills only.** Splits, merges and redemptions are not in the tape; neg-risk conversions are invisible.
- **1,000 USD cells.** Mostly partial (≈ 390 USD filled per executed alert); their positive point estimates
  (+4 % to +11 % in TEST) rest on 26 to 29 alerts with drawdowns of 1,500 to 1,900 USD and CIs from about −25 % to
  +39 %. They are not a result.

## Comparison asked by the mission (headline latency 300 s, 100 USD, "politics")

| Split | Alerts | Executed | Net PnL USD | Net per USD [95 % CI] | Price-only control per USD | S4 − control [95 % CI] | Max drawdown USD | Alerts per month |
|---|---|---|---|---|---|---|---|---|
| TRAIN | 90 | 39 | −251.28 | −6.6 % [−20.8, +8.3] | +22.4 % (29 of 371 draws) | −29.0 [−65.7, −0.4] | 425.54 | 7.5 |
| VALID | 128 | 68 | +105.51 | +1.7 % [−11.9, +17.3] | +16.2 % (68 of 505) | −14.6 [−34.6, +3.8] | 356.47 | 21.3 |
| TEST | 48 | 26 | −17.50 | −0.8 % [−21.8, +19.3] | −17.3 % (20 of 195) | +16.5 [−20.5, +59.2] | 373.12 | 12.0 |
| All | 266 | 133 | −163.28 | −1.3 % [−10.6, +8.9] | +12.3 % (117 of 1,071) | −13.6 [−29.0, +1.1] | 521.32 | 12.1 |

- **Frequency:** about 12 alerts a month in a 1,579-market sample (4.6 % of the population).
- **Capacity:** where takers are identified, a median 231 USD of asks is seen in the 15 minutes after the
  trigger (80 USD in TEST); at 1,000 USD most fills are partial. Half the alerts show no usable ask at all.
- **Execution cost:** median entry minus the trigger price is +1.0 cent overall, +2.1 cents in TEST, before fees.
- **Incremental advantage over price alone:** not demonstrated. Pooled, S4 does worse than the control
  (−13.6 points, CI [−29.0, +1.1]); TRAIN is the only split whose CI excludes zero, on the negative side, among
  many cells and with no correction: descriptive only. The control itself rests on few fills (11 % of draws).
- **Frozen vs causal timing:** with the frozen (non-causal) time, the all-split result is −10.0 % per USD
  [−18.8 %, −0.4 %] at the headline latency: the suppression step chooses later, worse entries.

## Prospective paper trading (prepared, not started)

`code/paper_trade.py`: no key, no order, public endpoints only. Every 15 minutes it updates the tapes of the
open markets that satisfy the frozen population filters and hash rule (170 markets on 17/11), runs the frozen
detector, logs the first S4 candidate of each (market, side) when it falls on or after the previous cycle's newest
grid bucket (older first candidates are logged `stale_first_candidate`, never read as "no alert"), takes a full
snapshot of the public book of the alerted token, and simulates a taker buy walking the displayed asks for each
size and cost scenario. One price-only control snapshot per cycle. The journal is append-only and hash-chained
(last hash kept in `journal.last_sha256`; a partial last line stops the run). `detected_at` is taken after the
market's tape top-up; the top-up replaces the fetched time range, so identical maker fills are kept.
A simulated fill is not an execution: the book can change before a real order, and displayed size is not
guaranteed capacity.

Smoke test on 17/11 after the fixes (4 markets, three cycles, state on VERBATIM HD): collection, detector,
stale handling, book snapshot, simulation and hash chain worked; a re-run top-up left the tape unchanged
(5,108 fills). No live alert occurred in those cycles. To run it continuously (Benjamin's decision; a launchd service must be installed by him):

```sh
cd ~/Projects/Polymarket-collective-exposure-execution-20261117/code
S=~/Projects/PHI-collective-exposure-shifts/investigations/collective-exposure-shifts
P="/Volumes/VERBATIM HD/phi-x/paper_trade_cxs_20261117"
while true; do python3 -B paper_trade.py --study "$S" --state "$P" --once; sleep 900; done
```

## Reproduce

```sh
cd ~/Projects/Polymarket-collective-exposure-execution-20261117/code
python3 -B test_replay.py
S=~/Projects/PHI-collective-exposure-shifts/investigations/collective-exposure-shifts
python3 -B replay.py --study "$S" --tapes "/Volumes/VERBATIM HD/phi-x/tapes_all.sqlite" \
  --stats "$S/results/replication_tests.json" --scored "$S/results/replication_scored.jsonl" --out ../out
```

Inputs are read only. The tapes (`tapes_all.sqlite`, 1,579 markets) are local to VERBATIM HD and not archived in
the repository; all 266 frozen alert times are reproduced as S4 candidates by the frozen detector.
