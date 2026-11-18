# Step 6/7: executable edge, collective exposure shifts

Verdict **NO_DEMONSTRATED_EDGE** (stop rule: the input statistics hold no valid signal). Historical execution
**UNVERIFIABLE** (no archived order book). Everything else is a hypothetical simulation from the trade tape.

| File | Content |
|---|---|
| `EXECUTION_LIMITS.md` | verdict, method, limits, comparison table, paper trading, reproduction |
| `out/EXECUTION_RESULTS.json` | every cell of the fixed grid (2 triggers × 3 latencies × 3 sizes × 3 costs × splits), stats gate, selection and detector-delay readings |
| `out/TRADE_REPLAY.csv` | one row per alert × cell, status FULL / PARTIAL / NO_TX / AMBIGUOUS_ONLY / NO_ASK_EVIDENCE, `execution=HYPOTHETICAL_TAPE_EVIDENCE` |
| `out/FALSE_POSITIVES.csv` | the 75 alerts whose side lost, headline cell (PnL empty when not executable) |
| `prereg/GRID.json`, `prereg/amendements/001-…` | grid fixed before any execution figure; post-audit amendment |
| `code/replay.py`, `code/test_replay.py` | historical replay (reads the frozen study and the tapes read only) |
| `code/paper_trade.py` | prospective paper trading, no order ever sent; prepared, not started |
| `evidence/BOOK_AND_FEES_SOURCES.md` | sources on order-book history and fees (read 17/11/2026) |
| `out_v1/` | first run and its code, kept unchanged |
| `audit_scratch/` | read-only scripts of the independent auditors |
