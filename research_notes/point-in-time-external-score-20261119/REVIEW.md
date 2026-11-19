# Point-in-time audit of external Polymarket suspicion scores (19 November 2026)

**Type:** externally attributed source-code review. **Verdict:** retrospective investigative ranking cannot be used unchanged as a prospective alert score. This review does not reproduce the authors' datasets or estimate their reported accuracy, and does not claim an original insider detection or new trading advantage.

## Exact external code inspected

- [vsbtc/polymarket-insider-detection, src/build_features.py](https://github.com/vsbtc/polymarket-insider-detection/blob/main/src/build_features.py), Git blob bda6c217f851bf59bd34c00848b88f0e248f908d: filters for the *eventual winning* outcome, then computes paper_edge from final_price and average entry price.
- [vsbtc, src/score.py](https://github.com/vsbtc/polymarket-insider-detection/blob/main/src/score.py), Git blob 296e6d66025b7cdf2604f9094f6ebedc6c545ee6: the suspicion score includes paper_edge; the wallet roll-up uses resolved historical performance and realized PnL.
- [vsbtc, src/enrich_wallets.py](https://github.com/vsbtc/polymarket-insider-detection/blob/main/src/enrich_wallets.py), Git blob 201adcbf3130e79313a1dba17c083bd868ef97ff: derives accuracy using market resolutions and derives lifecycle variables from the complete trade history.
- [vsbtc, src/detect_jumps.py](https://github.com/vsbtc/polymarket-insider-detection/blob/main/src/detect_jumps.py), Git blob 106f9d3b401b651e458675d3eb5beafe2d5df38d: retrospective reveal-jump screen on the winning side.
- [Benja-Pauls/polymarket-insider-detection, src/pminsider/collect.py](https://github.com/Benja-Pauls/polymarket-insider-detection/blob/main/src/pminsider/collect.py), Git blob 4e1850093602e8dac51d2d17d7ebb42895a68128: historical-resync/live-subgraph source selection. The declared constant RESYNC_CUTOFF_TS=1736121600 equals 6 January 2025 00:00 UTC, although its comment says 5 January 2026. It is **not referenced elsewhere in the examined file**, so this documentation mismatch is not proof that any collected result is incorrect.
- Existing local comparator: [EDGE_VERDICT](../../EDGE_VERDICT.md) and [external literature map](../external-market-abuse-corpus-20261117/README.md).

## Point-in-time classification

| Input or mechanism in reviewed code | Available at the original order time? | Permitted use |
| --- | --- | --- |
| Executed trade quantity, observable transaction/block time, entry price | Yes, once actually published/available and accounting for latency | Historical or live, with capture-time evidence |
| Future winning outcome, final_price and paper_edge based on winner | No | Retrospective investigation, never a live alert predictor |
| Realized PnL after the evaluation cutoff and eventual resolved accuracy | No for the same observation | Retrospective, or strictly past-only rolling history |
| Reveal-jump peak identified after the fact | Not before the peak is observed | Retrospective, or a separately specified online detector |
| Full-wallet history and future market activity | No, except the prefix preceding the decision | Point-in-time truncated prefix only |

The above is established by reading actual code paths, not by taking a README at face value. It does **not** establish that the authors claim to have a prospective score; the issue arises only **if** a retrospective ranker is transferred without redesign into a forward detector.

### Required falsification experiment

For each candidate alert timestamp T, reconstruct only records whose **publication/availability timestamp** is no later than T. Resolve historical performance for the wallet only from markets resolved before T. Do not condition market selection on eventual winning outcomes, profitable bets, known later jumps or later exits. Split chronologically and group by wallet-network/event; preserve non-alert markets and missing data. Match on price, spread, market age and liquidity. Compare conditional log loss, Brier, calibration and alert burden against market price alone. For any economic claim, use actual ask/bid/depth/latency and fees and a locked TEST partition.

A two-world counterexample exposes the error: two markets can have identical public data at time T yet resolve in opposite directions. Any score that filters to the eventual winner or uses final price can differ between those worlds **before their observable histories diverge**. It therefore cannot be computed at T without hindsight.

## Conclusions and ownership

**Code-reading findings:** supported by the pinned external blobs above. **External authors' numerical results:** not reproduced. **Independent wallet-level detection here:** none. **New validated financial edge:** none. The local EDGE_VERDICT's NO_EDGE_VALIDATED verdict stays in force. This original methodological comparison is written for this repository, while the source implementations and their authors retain their own provenance. No external code or protected dataset has been redistributed.