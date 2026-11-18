# Data inventory — what this study used, and what is missing

## Used and verified

| Input | Verification |
|---|---|
| `~/phi-live/market.jsonl`, prefix 2,406,972,265 bytes | sha256 `42f8508d…dc29b` re-read and matched on 16 Nov 2026; live collector `monitoring/livecollect` supervised, running since 14 Nov |
| `data/quotes.jsonl.gz` (1,133,727 quotes), `data/books.jsonl.gz` (7,267 full books) | extraction by frozen `code/col_local.py`; counts in `data/local_manifest.json` (181,747 rows outside window; 1,024 no-BBO; 4,624 invalid BBO; 67 backwards receive times — counted, not silently dropped) |
| `data/trades.jsonl` (4,909 rows) | frozen input; deduplicated by (tx, asset, side, size, price) in the code |
| `data/markets.json` (20 YES tokens) | Gamma snapshot at extraction; universe frozen |
| `data/historical_alerts.jsonl` (6,645 labelled alerts) | frozen copy of a previous local study; sha256 in PROTOCOL.lock; **origin volume (`/Volumes/PHI-Data`) not mounted: the copy could not be re-derived** |
| `data/github/` (11 external repositories) | per-file sha256, never executed; trees complete (`truncated=false`) |

## Known missing or unverifiable

- **Historical order books**: Polymarket serves no historical depth; only full frames captured live
  by our collector exist (7,267 frames / 2.5 d / 20 tokens). No backtest here can claim historical
  fill certainty.
- **Per-token fee rates**: historical exact rates unavailable; the plan uses three scenarios
  (0/0, 0.04/0.001, 0.07/0.002), documented in `analysis_plan.md`.
- **The origin of `historical_alerts.jsonl`** (external volume unmounted): its recount is
  descriptive only and is not an independent validation of anything.
- **Sports match markets**: excluded from this repository's universe since the frozen study; the
  external FLB lead (EDGE_VERDICT) cannot be tested without collecting them.
- **ChangeNOW pre-decision labels and complete non-CN histories**: absent, so no matched PnL test
  for family B is possible; existing repo findings stand.
- **Resolution data for the 20 markets**: none resolved during the window; outcome validation of
  live signals is not possible yet (by design the study measures execution, not resolution).
