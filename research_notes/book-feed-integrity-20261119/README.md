# Polymarket market-feed integrity: archived status-record replay

**Date:** 19 November 2026. **Status:** direct recount of a published project archive; no new wallet identification or economic edge claimed.

**Input:** [edge_research/data/book_status.jsonl](../../edge_research/data/book_status.jsonl), Git blob `46bcd70f19ca53f663d9a95d53f3d7b413837b1f`. This note uses no third-party dataset or source code. It is an original, independent consistency check on existing repository data.

## What the archive actually proves

The file contains **1,327 status records** for **40 distinct asset IDs**, timestamped between **2026-11-14 09:31:44 UTC** and **2026-11-16 13:55:26 UTC**. These are **status events, not 1,327 unique trades, markets or independent book snapshots**.

| Observed status property | Records |
| --- | ---: |
| All status records | 1,327 |
| `status == "desynchronized"` | **1,327** |
| `synchronized == true` | **0** |
| `best_bid == true` | 1,326 |
| `best_ask == true` | 1,326 |
| Both best-quote flags true | 1,325 |
| `depth == true` | 368 |
| Both best-quote flags and depth true | 368 |
| `hash_match == true` | **0** |
| `hash_match == false` | 247 |
| `hash_match == null` (unknown) | 1,080 |
| Strict synchronized + bid + ask + depth + valid-hash gate | **0** |

**Operational conclusion:** none of these archived *status records* establishes a trustworthy, complete order-book state for an execution-quality backtest. Having a best bid and best ask is **not** sufficient: the same records explicitly say the book is desynchronized, and no hash is confirmed matching. A `depth` flag is not a measured amount of fillable size.

This finding is about **the quality of this captured subset**, not a claim that Polymarket's real-world order books were always unsynchronized, nor that other archives in this repository lack synchronized data. It does not imply that no trades could be executed.

## Implications for investigations

1. Do not convert a last-trade price or a desynchronized book update into a claimed executable ask/bid.
2. Keep feed-health, book-state hash validation, timestamp age, displayed size, exchange fees, queue priority, and actual fills as separately required evidence.
3. Treat missing hash confirmation as **unknown**, not as proof the live book is incorrect. Here there are 1,080 unknown and 247 explicitly false hash comparisons.
4. Multiple status rows from the same asset are not independent statistical observations. The observed 1,327/1,327 ratio cannot be generalized to all tokens or times.
5. When the needed quote or status evidence is absent, mark a strategy outcome **NOT EVALUABLE**; do not score it as a zero return, a losing trade or a profitable trade.

## Evidence tier

- **CONFIRMED WITHIN ARCHIVE:** counts, asset coverage, observed status flags and the zero-row strict gate computed from archived text.
- **UNRESOLVED:** whether a separately archived genuine synchronized quote exists for each desired historical entry; trade-depth availability and achievable fills at those moments.
- **NOT ESTABLISHED:** a reliable net trading PnL, exchange-wide feed failure, insider-trading allegation or predictive advantage.

The previously published `NO_EDGE_VALIDATED` verdict remains unchanged. This note identifies a data-readiness obstacle; it does **not** turn an untested strategy into a validated negative result.

## Reproduce

From repository root with Python 3.10+, no external dependencies:

```bash
python3 research_notes/book-feed-integrity-20261119/recheck.py --self-test
python3 research_notes/book-feed-integrity-20261119/recheck.py --check
```

`--check` refuses unexpected changes to the source snapshot counts. No live API calls, external code or data import. Existing README, protected baselines, frozen studies and master reports remain untouched.
