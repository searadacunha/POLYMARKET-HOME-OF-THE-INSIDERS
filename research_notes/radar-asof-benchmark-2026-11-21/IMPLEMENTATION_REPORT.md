# Implementation, audit scope and reproduction

On 21 November 2026 the base revision `3faf43ae4b7bf8859afe2ab3c1543aa01169608a` contained 9,216 tracked paths, 354 commits reachable from main and 18 investigation directories. We inspected the eleven requested root documents, code and CI entry points, research archives and remote branch/PR history. The full clone exposed 99 remote branch heads. Of these, 57 tips were not ancestors of main. Squash merges make that count different from outstanding work. There were zero open PRs at the initial inspection. PRs 104, 106, 107 and 108 already delivered comparative research, the Nobel replay, the radar and a broader project inventory. Unpublished workstation sessions and private tapes were inaccessible. [Repository rules](../../AGENTS.md) · [Prior implementation review](../competitor-benchmark-2026-11-20/REPORT.md)

## Changes at normal entry points

| Entry point | Change and failure case | Verification |
|---|---|---|
| `python3 -m radar evaluate` | Each mark has its own 0–600 second observation window bounded by the evaluation clock. Ambiguous same-second prices and missing marks stay unknown. Exact binary identity and recorded close time gate settlement. | Sparse 24-hour point, future clock, equal-time conflict, v2 identity, absent close time and fee handling. [Evaluator](../../monitoring/radar/evaluate.py) · [Tests](../../monitoring/tests/test_radar.py) |
| Append-only evaluation journal and dashboard | Versioned re-evaluation supersedes legacy final records while preserving their bytes. Concurrent processes deduplicate under the journal lock. The latest evaluation drives the dashboard. | Original records, subsequent chain integrity and idempotence under concurrent workers. [Command handler](../../monitoring/radar/__main__.py) |
| `python3 -m radar context` | A read-only query joins a sealed financial/statistical alert to the PolySentinel v2 event identity and reviewed evidence available at emission. It verifies the archived response and records publication, receipt and review clocks. | Real store, equal-time conflict, future edits, wrong market, tampered response, ambiguous event and resolution-only evidence. [Implementation](../../monitoring/radar/context.py) · [Tests](../../monitoring/tests/test_radar_context.py) |
| Research replays in the monitor CI suite | Recompute forecast, timing, case accounting and discovery results. Validate sports, RPC and live observations offline. | Existing monitor test discovery runs all new offline checks. [CI test](../../monitoring/tests/test_radar_benchmark.py) · [Source checks](verify_outputs.py) |

Context classification requires an existing reviewed milestone and a directly matching successful source response. The result stays unknown for unreviewed headlines and archives without time-prior evidence. Operational scaling of archive joins and independent case adjudication have not been measured. Existing engine checkpoints, duplicate handling, source retry, journal and supervision provide the operational foundation. [Radar usage](../../monitoring/radar/README.md) · [Existing coverage audit](../../LIVE_DETECTION.md)

## Historical cases re-examined

| Case | Work performed in this session | Evidence status |
|---|---|---|
| Maduro / Venezuela eight-account network | Recomputed eight-account P&L from the components and reran cross-case financial and negative-control verifiers. | **CONFIRMED** archived trading result of USD 509,993.24. The separate external cash-flow figure is USD 509,624.54. Five wins and 66 losses across 71 Railgun-tree child bets demonstrate the weakness of funding alone as evidence of foreknowledge. [Recalculation](cases.json) · [Prior accounting](../../investigations/maduro-iran/results/accounting_audit_2026-11-04.json) |
| Historical Iran 38-proxy cohort | Ran the G38 proof-tier audit and related evidence checks on archived inputs. | **CONFIRMED** 38 proxies, 32 direct Polygon senders, 12 one-to-one matched Relay orders and USD 1,576,522.86 trading-result snapshot. Final beneficiary and common controller **UNRESOLVED**. [G38 audit](../g38-proof-tier-audit-2026-11-08/) |
| Ballon d'Or | Read all 11 compressed account activity exports, counted distinct transactions within activity type and totaled the records. Checked the earlier ranking and its limitations. | **CONFIRMED** 46 deposits, USD 304,137.634730, and 25 withdrawals, USD 493,094.756177. USD 129,367.79 applies to seven settled accounts. The early census rank was 41. Private knowledge remains **UNRESOLVED**. [Accounting](cases.json) · [Historical audit](../../investigations/ballon-dor-audit/) |
| 2025 Nobel | Reran the strict replay (188 checks) and funder-exit audit (52). Tested price-clock contamination on the chart and tape. | **SUPPORTED** early retrospective triage. The first C1 hit on account 6741 at 22:45:07 UTC on 9 October was on Sudan No, fourth of 57 overnight alerts. Machado Yes repriced at 23:00:15. The co-funded alert came at 00:55:11. Historical payer-state correction expanded eight entries on one event to 19 on four. [Nobel replay](../nobel-strict-replay-2026-11-20/REPORT.md) · [Funder audit](../nobel-funder-exit-2026-11-20/) |
| ChangeNOW / exchange outflows | Reran the published-evidence verifier. It checked 66 released files. Another 423 third-party files are listed and unavailable locally. | **SUPPORTED** for specific documented service contacts. Allocation between pooled deposits, subsequent withdrawals and customers remains **UNRESOLVED**. [Evidence package](../../investigations/changenow-proof/) |
| Relay / cross-chain transfers | Reran cross-investigation checks (33), financial-links checks (47) and the archived Ethereum-to-Monad verifier. Rejoined order pairs and read fresh chain records. | **CONFIRMED** three intermediate Arbitrum passages. The separate archived Monad case shows 2,969.568353 mUSD deposited and 2,904.30854 vmUSD minted 29 seconds later. [Order pairs](cases.json) · [Primary capture](arbitrum_receipts.json) · [Monad trace](../relay-followup-2026-11-04/) |
| Collective exposure / unusual timing | Reviewed earlier placebo, power and matching diagnostics. Ran the archival unit suite and the new chronological three-rule benchmark. | Earlier study **UNRESOLVED / underpowered**. Eleven of 16 additional archival tests succeeded. Five require the original local tape and study layout. [Earlier study](../../investigations/collective-exposure-falsification/sources/FALSIFICATION_REPORT.md) · [New results](results.json) |

The exploratory route extension searched all 14,127 successful orders without starting from the named pairs. There were 643 eligible arrivals, 334 eligible departures and three matches before the outer-endpoint exclusion. Zero qualified with an outer endpoint outside the 1,005-address registry. This result is limited to a case-selected archive. [Protocol](DISCOVERY_PROTOCOL.md) · [Discovery output](discovery.json)

## Reproduce offline

From the repository root on Python 3.11 or newer, run the following commands. Offline checks read public inputs already in the repository. Later network retrievals can differ if providers revise history.

```bash
note=research_notes/radar-asof-benchmark-2026-11-21
python3 -I "$note/benchmark.py" --check
python3 -I "$note/case_replay.py" --check
python3 "$note/discovery.py" --check
python3 -I "$note/verify_outputs.py"
python3 "$note/arbitrum.py"
python3 "$note/sports.py" --game-start
(cd monitoring && python3 -W error -m unittest discover -s tests -q)
python3 scripts/run_all_checks.py --keep-going
```

Third-party arithmetic requires Git, network access on first fetch, and a Parquet reader. The audit used PyArrow 24.0.0. The optional command fetches pinned public Git objects into a separate cache, verifies SHA-256 digests and recomputes released aggregates. It executes no downloaded repository code. Separately, tlafargue's original verifier reproduced the all-wallet correlation (p = 0.394) and alphalab's upstream suite passed 33 tests. These checks share the authors' released data. [External results](external_results.json) · [Source inventory](sources.json)

```bash
python3 -m venv /tmp/polymarket-replay
/tmp/polymarket-replay/bin/pip install pyarrow==24.0.0
/tmp/polymarket-replay/bin/python "$note/external_replay.py" /tmp/polymarket-peers --fetch --check
```

To obtain fresh public RPC evidence, pass a new output path to `arbitrum.py --collect`. For the original game-date MLB window, use `sports.py --game-start --collect OUTPUT`. The live-data command `pilot.py OUTPUT` selects the first eligible tennis contract before taking observations. A later date can select a different live market.

Two public RPC providers returned identical normalized records for all six transaction receipts, six block headers and the complete incoming/outgoing transfer queries. The second provider rejected the historical balance and token-decimal calls. The zero balances are supported by the primary archive provider. [Primary RPC](arbitrum_receipts.json) · [Independent provider capture](arbitrum_second_rpc.json)
