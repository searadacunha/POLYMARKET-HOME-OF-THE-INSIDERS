# Why NO followed by YES may not be a reversal

## A necessary distinction

Let `A` be the event "the same qualifying action happens **by** deadline D1" and `B` be that action **by** the later deadline D2. If and **only if** the market rules define the same event and D1 < D2, then A is a subset of B.

Buying **NO(A)** and subsequently buying **YES(B)** can represent a single positive bet on occurrence **between D1 and D2**, not a belief change from "no event" to "event".

Take one fully funded share of each token, with no intervening sale. Ignore fees for this algebra. Portfolio payoff by mutually exclusive real-world scenario:

| World | NO(A) | YES(B) | Combined shares |
|---|---:|---:|---:|
| Event happens by D1 | 0 | 1 | **1** |
| Event happens after D1 but by D2 | 1 | 1 | **2** |
| Event does not happen by D2 | 1 | 0 | **1** |

This package is equivalent to **one certain dollar plus one contingent dollar for the middle interval**, conditional on both markets' settlement rules and full redemption. It is not a short position simply because one side is named NO.

If the first-date YES price is p1 and second-date YES price p2, the notional purchase cost of the two shares is `(1-p1)+p2 = 1+(p2-p1)` at exact theoretical complements. `p2-p1` approximates the market-implied probability of the interval only under consistent definitions, coherent pricing, and absent spread/fees. With actual bid/ask prices the execution cost may be higher. No risk-free profit is inferred.

## Detecting an actual reversal

At every time T, construct a wallet's **payoff vector**, one dimension per mutually exclusive outcome or event-time bucket. Include the exact contractual resolution language; do not infer nesting from similar titles or matching `endDate` metadata. For market family f, let `Q_w,f(T)` be the vector of redeemable payouts under each scenario, derived from actual token inventory at T.

A **true directional reversal** requires a documented change in payoff differences between relevant outcome scenarios (for instance an event-early exposure that changes sign). Merely obtaining a YES token after a NO purchase is insufficient.

Classify each sequential episode separately:
- `SAME_TOKEN_ROUND_TRIP`: buying then selling a token; can be maker inventory or scalping.
- `SAME_MARKET_OPPOSITE_BUY`: buying both YES and NO without a proven sale; may be hedge/split strategy, not a reversal.
- `DEADLINE_INTERVAL_PACKAGE`: NO on D1 and YES on later D2 for the same nested event. Record payoff mass on the interval.
- `TRUE_NET_ROTATION`: independently reconstructed wallet-level payoff vector shifts sign by a declared amount **after** accounting for inventory, conversion and realized disposals.
- `UNRESOLVED`: missing trade history, unproved contract family, unknown CTF transfer semantics, or insufficient resolution-rule equivalence.

## Data requirements and failure modes

- Reconcile BUY, SELL, ERC-1155 balance changes, splits/merges/redemptions, gas-funded proxies and any V2 NegRisk conversions. A BUY-only feed does **not** establish position closure.
- Recognize on-chain exchanges by contract and version, exclude synthetic exchange maker/taker legs, and retain transaction hashes, log indices and block timestamps.
- Store both `block_time` and `first_observed_at`. Do not label a group as observed at T using transfers, payouts, or common funding relationships first visible after T.
- A missing event definition, data truncation or unsupported exchange version forces `UNRESOLVED` for a purported net rotation, not an inferred YES/NO flip.
- If the contracts settle on materially different definitions, interval algebra is invalid and no monotonic price constraint is assumed.

## Falsification tests

1. Reconstruct a documented market maker's multi-deadline inventory: likely NO/YES trade churn without directional belief reversal.
2. Replay a nested deadline pair with no time-local sell: should become `DEADLINE_INTERVAL_PACKAGE`, not `TRUE_NET_ROTATION`.
3. Replay a single token BUY then SELL in the same minute: should be a round trip, not an insider pattern.
4. Verify `Q_w,f(T)` changes *only* from events recorded by T and never from later redeem/settlement data.
