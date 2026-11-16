# Source review, 16 November 2026

This is an **original synthesis**, not a claim to have produced any external study. The distinctions below reflect the published primary protocol, repository documentation and the local archive. Numbers reported by other authors are not included in this investigation's findings and have not been independently reproduced here.

## Primary protocol: high evidential value for event semantics

- [Polymarket V2 exchange source](https://github.com/Polymarket/polymarket-v2-external/blob/main/src/exchange/Exchange.sol) and [exchange documentation](https://github.com/Polymarket/polymarket-v2-external/blob/main/docs/exchange.md): OrderFilled reports the maker and taker. The taker's own OrderFilled event uses the exchange contract as its nominal counterparty and is followed by OrdersMatched. A maker's OrderFilled side is the maker's order side, not automatically a general buyer/seller edge under same-side mint/merge modes.
- Existing first-party decoder in [monitoring/phi_monitor/chain.py](../../../monitoring/phi_monitor/chain.py) reads CTF and NegRisk V2 Polygon logs and retains tx, log_index, wallet, counterparty, exchange and token. Its separate synthetic taker event is **not** another person-to-person trade. Duplicating it distorts an interaction graph.
- Practical boundary: a transaction-level edge is evidence of an executed contract interaction, not coordinated ownership. An exchange-address edge is not a counterparty relationship between traders. Token-side and cash amounts must be interpreted using the documented matching regime.

## Local archive: high confidence in arithmetic, limited independence

- [C7 archived four-row transaction table](../../../research_notes/early-detection-2026-11-13/data/c7_intra_group_trades.csv) and [audit](../../../AUDIT_20261113.md): an earlier analysis identifies trades between the C7 seller and two funded buyers.
- This folder recomputes the four-row totals from scratch using Decimal, validates the unique transaction hashes and the approximate price-times-shares amounts, and stores [its result](c7_reconciled.json).
- The new check **does not** fetch Polygon RPC receipts, independently rebuild the maker-to-taker pairing, establish beneficial ownership, or test predictive advantage.

## External research: useful methods, not adopted results

- [Sirolly, Ma, Kanoria and Sethi, Network-Based Detection of Wash Trading](https://business.columbia.edu/faculty/research/network-based-detection-wash-trading), working paper: an iterative method looking for approximately closed networks of counterparties. This suggests graph features, not a validated predictor for informed trading. Market-making is a documented competing explanation.
- [Xhazerie/polymarket-detecting-wash-trading](https://github.com/Xhazerie/polymarket-detecting-wash-trading): publishes weekly network scoring on an older period; reported flagged proportions are detector classifications, **not verified wash volume**. Its reproducibility is not established by this investigation.
- [bandrehc/polywash](https://github.com/bandrehc/polywash): an explicit greedy pairing heuristic matches Data API buy/sell legs within a (transaction, token) group. This may be ambiguous for multi-maker and mint/merge execution. We do **not** copy the implementation or use greedy pairing as proof of a bilateral counterparty.
- [alphalab-research/wash-detector-v3](https://github.com/alphalab-research/wash-detector-v3): publishes a different per-market scoring methodology and much lower headline flagged rates. Differences in windows, populations, calibration and definitions prevent treating the reported rates as directly comparable. Neither estimate is included as our finding.
- [veeradittya/polymarket-insider-detection](https://github.com/veeradittya/polymarket-insider-detection): proposes anomaly-based wallet clustering and repeated cross-case accounts. It is an alternative methodological lead, not proof that its high-scoring accounts possess non-public information.

## Data and licensing boundaries

- [Envio/moose-code Polymarket v1 dataset](https://huggingface.co/datasets/moose-code/polymarket-onchain-v1) is a publicly described historical on-chain dataset spanning the old exchange through April 2026, under CC-BY-4.0 requiring attribution. It has **not** been copied or queried by this addition, and does not by itself establish comprehensive post-migration V2 coverage.
- [wietrade/poly_data](https://github.com/wietrade/poly_data) describes a V2 indexing pipeline but its README states that its current backfill covers CTF V2 standard markets only, not NegRisk V2 and additional contract versions. Treat any dataset derived solely from it as incomplete for cross-market prevalence claims.
- No third-party code, fulltext paper, restricted dataset, trade tape, or researcher's outcome table is presented as original work here. Methods are independently described, original code is written in this folder, and source links remain explicit.

## Reconciliation principle

If two studies flag radically different proportions of volume, do **not** average the results or select the larger number. Before comparing, align the exchange version, date range, token set, actor identities, synthetic-leg handling, maker/taker pairing, score definition, threshold tuning and uncertainty. Then rerun on the **same** public subset and require a held-out validation. Until that work exists, the magnitude of wash-like activity is **UNRESOLVED for this dossier**.
