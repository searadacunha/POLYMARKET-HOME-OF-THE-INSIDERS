# Registry of hypotheses tested — including everything rejected

New in this study, then the standing rejections this study inherits (no hypothesis retested).

## This study (16 November 2026, frozen)

| # | Hypothesis | Rule (fixed before results) | Verdict | Where |
|---|---|---|---|---|
| H-D1 | Short momentum predicts continuation ≥ costs | 5-min midpoint rise ≥ 0.005, entry at ask +latency, exit at bid +h | 0 signals on 73,200 minute-tokens: `DONNEES_INSUFFISANTES` | `results.md` §1 |
| H-D2 | Short reversal predicts reversion ≥ costs | 5-min fall ≤ −0.005 | 0 signals: `DONNEES_INSUFFISANTES` | `results.md` §1 |
| H-D3 | Top-3 bid imbalance ≥ 0.8 predicts rise | full-frame depth only, no deltas | all cells negative, matched diff ≤ +0.0002: `NON_EXPLOITABLE` | `results.md` §1 |
| H-B1 | Copying public ≥1,000 USD buys within seconds beats the toll | first observed in trades stream, decision at receive time | 3 signals: `DONNEES_INSUFFISANTES`; median detection lag 76 s | `results.md` §1 |
| H-E1 | YES+NO basket under 1 USD (pair gate) | both quotes ≤ 2 s, clocks ≤ 2 s apart | 0 gross violations in 15,555 pairs: nothing to capture | `results.md` §2 |
| H-H1 | Following the labelled alerts of the previous local study beats the price | pooled validation excess, 1 declared comparison | **−2.65 points** (n = 2,885): no | `results.md` §3 |

## Inherited rejections — NOT retested here

| Hypothesis | Source | Result |
|---|---|---|
| `LONELY_THIN` ignition predicts outcome beyond price | frozen study, `PATTERN_RESEARCH.md` | +3.5 points, p = 0.33: `NOT_SUPPORTED` |
| Funding within the hour before a first buy is distinctive | repo investigations | no excess against matched controls |
| Fresh wallet = new operator | NB-2, `NEW_LEADS.md` | wrong by construction (existing trader behind fresh accounts) |
| Shared service (ChangeNOW, exchanges) = shared owner | `changenow-proof`, `ballon-dor-wallets` | not demonstrated; one corroborated contact, no path to bets |
| Simple price moves / volume / synchronized new wallets / concentration predict outcomes | PR 70 + frozen study | no advantage |
| Calibration-side entry on quiet long-horizon politics markets | this study's control cells | guaranteed negative (the toll) |
| Taker directional trading on fast crypto binaries | external: junegun 121 strategies, 478,155 entries | every family lost (−2.1 %/entry) |

## Deliberately not tested (would need data we refuse to fabricate)

- Maker/market-making strategies: no historical queue-position or fill data; unknown cancellations
  prevent certified fills. The depth findings here say the display side is thin — a maker study
  needs a live paper session, not a backtest.
- Anything selecting wallets on realized winners (circular reasoning, per `maduro-iran` limits).
