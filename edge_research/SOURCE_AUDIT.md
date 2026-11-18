# External research and tooling triage — 16 November 2026

Sources below are **methodological candidates**, not evidence about the ownership, knowledge, or profitable future trades of a wallet in our case files. No third-party code or data was copied into this branch. Future incorporation must check license terms and retain required attribution.

| Source | Materially useful function | Evidence/rights caveat and decision |
| --- | --- | --- |
| [outcometick/polymarket-backtest](https://github.com/outcometick/polymarket-backtest) | Tick/book replay, both outcome tokens, depth-walking, estimated maker queues, venue fees and latency | GitHub lists MIT. **First choice for a controlled execution benchmark** once matching historical books exist. Its free crypto sample is not political-market edge evidence. |
| [mileswangs/polymarket-historical-data](https://github.com/mileswangs/polymarket-historical-data) | Tick-level L2, receive timestamps, settlement oracle for BTC Up/Down 5-minute markets | Repo code MIT, dataset separately CC BY 4.0 per project. A compact sampled read can test software; 5.6 GB dataset unnecessary on full disk. |
| [eliazonta/pmarket_arb](https://github.com/eliazonta/pmarket_arb) | Arbitrage basket depth/fees and maker breakeven calculation | GitHub lists MIT. Modeled maker profit is not measured prospective maker PnL; no validated advantage imported. |
| [bradca0/polymarket-pnl](https://github.com/bradca0/polymarket-pnl) | PnL reconstruction with SPLIT/MERGE/REDEEM and as-of shrinkage of wallet skill | Its public result is a *negative* wallet-skill-following signal; GitHub metadata exposes no license, so code is not copied. |
| [darrnhard/polymarket-smart-money](https://github.com/darrnhard/polymarket-smart-money) | Adaptive account-activity pagination and behavioral categories | Top-wallet selection risks survivorship bias; self-reported roadmap defers robust settled PnL. No license in GitHub metadata. |
| [Epsilon-Fund/Epsilon-Quant-Research](https://github.com/Epsilon-Fund/Epsilon-Quant-Research) | 64-day L1/trade archive, walk-forward/CPCV and paper execution journal design | Large dataset and market-matching costs; no license in GitHub metadata. No code/data import. |
| [Polymarket/py-sdk](https://github.com/Polymarket/py-sdk) | Official public API client, market metadata and trading interfaces | GitHub lists MIT, but an SDK does not create a measurable edge. Do not attach a live trading client before validation. |

Additional **external research, not imported data**:

- [Cardozo and Rivero-Wildemauwe (2026), Favorite-Longshot Bias](https://arxiv.org/abs/2609.12878): the estimated return differs sharply when contracts are grouped by parent event. A pooled longshot observation is not an immediate trade rule.
- [Aidan Walker (2026), Price is (Almost) Right](https://theses-dissertations.princeton.edu/entities/publication/d5708372-5ea3-4252-b669-7f9cee07387c): calibration by market domain/horizon, with event-level dependence corrections.
- [Polymarket fee schedule, July 2026 publication](https://help.polymarket.com/en/articles/13364478-trading-fees): taker fee rate varies by category; makers may receive rebates. **Historical fees must be assigned as of the past trade date**, not guessed from the current table.

**Priority by information gain:** maker adverse selection/queue simulation with genuine L2; correcting wallet-following delay, quotes and liquidity; point-in-time PnL with full settlement reconciliation; then event-grouped structural probability hypotheses. The existence of an open-source bot or dataset is not proof of profitable execution.
