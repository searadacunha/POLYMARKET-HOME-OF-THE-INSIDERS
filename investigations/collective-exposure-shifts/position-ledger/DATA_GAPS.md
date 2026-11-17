# Data gaps: what the ledger cannot see, and what that does to each reading

Figures from the run `out/full` (1,293 events, 1,579 markets, 3,206,979 fills applied) unless stated. Every
gap below is handled by a status or a bound in the ledger; none is filled in.

## Summary: three readings

| Reading | From the tapes alone | Why |
|---|---|---|
| Directional exposure X = YES − NO per market, payoff shape of a family | **Observable** (`OBSERVABLE`), exact unless an ERC-1155 transfer or a neg-risk conversion moved tokens | splits and merges move both legs together; conversions keep the shape of a complete neg-risk event |
| Inventory (how many YES and NO tokens are held) | **Bounded only** (`BOUNDED`): lower bound = the directional part, no upper bound | splits, merges and redemptions are invisible in fills |
| Anything on a market whose tape is truncated, or after an unbalanced transaction | **Unknown** (`UNKNOWN`) | initial position or a fill is missing |

At each market's last fill, wallet-market pairs by directional status: `OBSERVABLE` 530,333, `UNKNOWN` 2,034 (0.38 %), `EXACT` 0 (no source covers transfers).

## 1. Event classes absent from the fill tapes

The tapes (`data-api /v2/trades`, `taker_only=false`) contain BUY and SELL fills only.

| Class | In the tape | Where it can be read | Effect handled |
|---|---|---|---|
| SPLIT, MERGE | no | per wallet, `/v2/activity` (types SPLIT, MERGE) | X unchanged; inventory bounded; class D unverifiable without it (`D_UNVERIFIED_NO_RETENTION`) |
| Neg-risk CONVERSION | no | per wallet, `/v2/activity` (type CONVERSION, member legs not detailed) | market-level X can move: reason `CONVERSIONS_NOT_COVERED` on 1,034 neg-risk markets; shape of a complete event unchanged |
| REDEEM | no | per wallet, `/v2/activity`; auto-redeemed positions may not produce a row (reported by mission 2, not verified) | happens after resolution; reason `REDEMPTIONS_NOT_COVERED` |
| ERC-1155 transfers | no | on-chain only (`TransferSingle` / `TransferBatch`); no decoder in the repository | X can move; reason `TRANSFERS_NOT_COVERED` on every reading |
| Fees | no fee field | Gamma `feesEnabled` per market; amounts on-chain only | see section 3 |

Measured on the TRAIN episodes of binary families re-read with each wallet's activity feed (`scripts/verify_with_activity.py`,
`out/full/verify_TRAIN.json`): 1,099 of the 1,308 TRAIN A and D episodes: the 209 A episodes of exclusive (neg-risk) families, where conversions
can move X, were not re-read. 516 wallet-market pairs, 40,468 TRADE rows. 362 pairs merged before the market's last
fill (2,620 MERGE rows applied; 2,637 in the feeds, 17 after the last fill), 5 split (27 SPLIT rows); no CONVERSION.

| Class from the tape | Episodes | With the activity feed |
|---|---|---|
| `D_UNVERIFIED_NO_RETENTION` | 849 | `D_YES_ACCUM_KEEP_NO` 414 (49 %), `DIRECTIONAL_ADD` 366, `C_HEDGE_REBALANCE` 68, `NONE` 1 |
| `A_TRUE_INVERSION` | 250 | `A_TRUE_INVERSION` 247, `UNRESOLVED_ACTIVITY` 3 |

Half of the D candidates read from fills alone are not D: the NO they seemed to keep had been merged away. A survives
because merges cannot flip X. The wallet's TRADE rows match its tape fills transaction by transaction in 515 of the 516
pairs; in one pair the activity feed has one transaction the tape lacks (459 against 458 keys), so its 3 episodes are
left unresolved.

Wallet-market pairs whose fills alone prove an unobserved inflow (sold more than ever bought, at second
resolution): 11,748 of 532,367 (2.2 %). These are splits, conversions, transfers or pre-tape history; the tape cannot say
which.

## 2. Transaction completeness (missing or doubled fills)

The tape has no log index and no block number. The per-transaction conservation check (YES supply change = NO supply
change) is the internal test of completeness, run on every transaction: 1,273,287 (transaction, market) groups: `BALANCED` 1,266,172 (99.44 %), `FEE_IN_SHARES` 4,881,
`UNBALANCED` 2,224 (0.17 %; 2,180 of them on fee-enabled markets, 44 elsewhere), `MULTI_TIMESTAMP` 10. The complete
Iran 28 February tape (`feb28_v2.sqlite`, 217,997 fills) is 86,991 of 86,991 balanced.

- A balanced transaction proves that no leg is missing or doubled **inside the tape**. It does not prove that the
  tape matches the chain (a transaction absent from the tape entirely is invisible to this check). The on-chain
  reconciliation proposed by mission 2 (N1, `OrderFilled` events) is still not done.
- Exact duplicate rows: none dropped. `tapes.sqlite` has 5,569 sets of exact duplicates: 5,546 in `BALANCED`
  transactions (so they are distinct fills), 9 in `FEE_IN_SHARES` and 14 in `UNBALANCED` transactions (whose wallets
  already read `UNKNOWN`). Counted by the deliverable audit (REVIEW_LOG.md). Rows without a transaction hash: 0.
- Order inside one second is unknown; running minima are taken at second boundaries, so it cannot create a false
  negative inventory.
- For the examples, the wallet's TRADE rows in the activity feed matched its tape fills transaction by transaction
  (EXAMPLE_PORTFOLIO.md).

## 3. Fees

467 of the 1,579 sampled markets have `feesEnabled = true` in Gamma (fetched 2026-11-17). On those markets a
buyer fee is taken in shares: the buyer's row already shows the shares received, and the transaction is short by the
fee (verdict `FEE_IN_SHARES`, implied rate = gap / (min(p, 1 − p) × shares)). Implied rates observed (base min(p, 1 − p)), by Gamma fee type, as counted by the
deliverable audit:

| Fee type | Accepted as `FEE_IN_SHARES` (main modes) | Left `UNBALANCED` |
|---|---|---|
| `sports_fees_v2` | about 0.06 (516) and 0.03 (432) | 271 |
| `crypto_fees_v2` | about 0.07 (201) and 0.08 (171) | 806, with modes at 0.15 (331) and 0.14 (131) |
| `economics_fees` | 4 | 524, with a mode just above 0.10 (302 at 0.100 to 0.105) |
| `politics_fees` | about 0.08 | 336, with a cluster near 0.14 (119) |
| `tech_fees`, `culture_fees` | | 185 and 58 |

So the declared cap of 0.10 leaves real fee modes `UNBALANCED` (crypto, economics, politics); 2,180 of the 2,224
unbalanced groups are on fee-enabled markets. Those wallets read `UNKNOWN`: conservative, nothing is filled in, and
the cap was not changed after the run. Conversely, the 0.10 band is a plausibility test, not a proof: a missing or
doubled small fill whose gap happens to fall inside it would pass as a fee. Matching each transaction to the fee
schedule of its fee type (and its date) would be an amendment for Benjamin to decide. Implied rates above 0.3 (842
groups) are not explained by a single buyer fee. Fees paid in USDC (sells) do not appear anywhere: cash flows on fee-enabled markets are reported with `fees: UNKNOWN`.
The cap `MAX_FEE_RATE = 0.10` was declared before the run; rates above it stay `UNBALANCED`.

## 4. Contract versions (V1, V2, NegRisk)

- Gamma reports `version = v1` for all 1,580 markets with Gamma metadata. "v2" in this repository is the **data-api version**,
  not the exchange.
- The tape carries no contract address, so the exchange (CTF Exchange or NegRisk CTF Exchange, and its generation)
  of a fill is unknown; the ledger has no exchange field rather than a guessed one, and no reading changes by
  variant. The repository's on-chain decoder (`monitoring/phi_monitor/chain.py`) reads only the V2
  exchanges `0xe1111800…` and `0xe2222d27…` (mission 1); no V1 decoder exists.
- Neg-risk flags come from Gamma (`negRisk`, event `negRiskAugmented`): `negRisk` true on 1,034 sampled markets, false on 543, missing on 2 (reason `NEG_RISK_FLAG_UNKNOWN`). Augmented events can add
  placeholder outcomes, so an exclusive family built from sampled members always keeps the world `OTHER`.

## 5. Families of markets

| Event type in the sample | Events |
|---|---|
| single sampled market | 1,058 |
| neg-risk exclusive family (sampled members, world `OTHER` kept) | 169 |
| proven deadline ladder | 2 |
| refused: wording not cumulative ('on', 'in', or no 'by'/'before') | 50 |
| refused: questions differ beyond the date | 9 |
| refused: no single explicit deadline date per question | 5 |

Only one `B_INTERVAL_PACKAGE` episode exists in the whole sample (TEST). Class B was read at scale only on the Iran
ladder, as exploration (EXAMPLE_PORTFOLIO.md, section 2).

- Deadline ladders need proof that the rules are the same up to the date (`prove_ladder`). Similar titles or Gamma
  `endDate` are not enough: for the Iran market, Gamma `endDate` is 2026-01-31 while the question says 28 February.
- Events worded "on <date>" (for example "Will Israel strike Lebanon on November 3?") are disjoint days, not nested
  deadlines; they are refused. The frozen study's `interval_reading.py` grouped any event with two closing times,
  which mixes neg-risk exclusive events, disjoint days and true ladders.
- The sample (1,579 of the 34,413 markets of the population, 4.6 %) rarely keeps two deadlines of one event, so class B is almost never testable inside the sample.
  It was read on the Iran ladder only, as exploration (EXAMPLE_PORTFOLIO.md, section 2).

## 6. Identities

The tape gives the proxy wallet only. Signers, funders, relayers and the counterparty of each leg are not in it.
Co-participants of one transaction are not linked accounts. No address is merged with another; the S5 funding graph
(mission 1) is still UNRESOLVED.

## 7. Time and observability

- Every archived event has `seen_ts = ts`: the tapes were collected after the fact (2026-11-16), so "known at T"
  means "happened by T", not "served by the API at T". A live system would see fills with a delay; that delay was
  not measured (mission 6 says the same).
- Gamma metadata and activity feeds were fetched on 2026-11-17. They are used for rules text, flags and protocol
  events; their outcome fields were removed from the stored files. The flags are read as of today, not as of each
  fill: if a market's fees were switched on after some fills, gaps on those earlier fills could be read as fees, and
  rules text edited after T could prove or refuse a ladder. No fee activation date is available to correct this. Gamma `closedTime` depends on the outcome for "by date" markets; it is used only in the
  reference partition and the purge rule (PARTITIONS.json).

## 8. Integrity of the inputs

| File | Size (bytes) | sha256 now | Manifest of the frozen study |
|---|---|---|---|
| `tapes.sqlite` (primary, 763 markets) | 719,400,960 | `63c85df4d3bce9f9afe77b713d10036f4fff426b021172fc763cbfe50eb915b3` | same |
| `tapes2.sqlite` (replication, 816 markets) | 800,653,312 (763.6 MiB) | `b65627060569f53a466ebfa5fa9e9731347fe66f79cd3c09cabb3823184f0768` | **differs**: 438,779,904 bytes, `45209773…34fc` |
| `feb28_v2.sqlite` (Iran, exploratory) | 104,607,744 | `1f636371b6573416770ada4cdbfc5f5e8f29b21819791a9c0ca315290c6f1015` | same |

`tapes2.sqlite` no longer matches the manifest written on 2026-11-16 21:52 UTC (it is the same file, same hash, that
mission 1 read this morning; nothing wrote to it during this run). The replication results of the frozen study
cannot be re-hashed against their declared input. This ledger records the hash it actually read. `tapes_all.sqlite`
(not in any manifest) was not used.

## 9. Population (inherited, not re-audited)

Markets of 1 M USD volume and above are excluded by the sample rule; only closed markets are in the population, so the
latest partition is right-censored (markets that closed early are over-represented); the 13 November exclusions are
inherited.
