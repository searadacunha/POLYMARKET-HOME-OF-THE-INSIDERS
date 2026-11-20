# Receipt-level funding attribution: reject ambiguous equal-amount joins

**Date:** 20 November 2026. **Status:** original code correction and synthetic regression tests. **Not** an independent reattribution of historical wallets, insider information, or trading advantage.

## Defect in previously deployed active monitor

The prior `monitoring/phi_engine/chainfund.py::payer_of_deposit` searched ERC-20 Transfer logs and selected the **first transfer of exactly the same amount** when tracing a wrapped deposit or one-hop source.

It did not require source logs to precede the credit, did not check token identity across upstream transfers, and did not reject multiple equally plausible payers. If two senders transferred identical nominal quantities, the input log order could determine an apparently proven root funder. Multiple equally large wallet credits were also resolved to the first one.

This is a verified code-level attribution risk. It does **not** establish that any specific previously published funding path is false.

## Correction

**Frozen-code safeguard:** `monitoring/phi_engine/chainfund.py` is a hash-locked dependency of the 14 November 2026 study. It remains byte-identical to `main` (Git blob `d039ad88d72005318e3ddb60add4af631ca50d00`). The new implementation is isolated in `monitoring/phi_engine/receipt_link_guard.py`; only the active engine's two deposit-attribution call sites switch to it. This prevents retrospective changes to the frozen study while improving new alerts.


- Preserve uniquely maximal credits as an explicitly selected deposit; return `ambiguous_credit` when largest credits tie.
- Wrapped USDC/USDC.e -> pUSD receipts require **exactly one** equal-value stablecoin input to a known infrastructure address, with a valid **earlier log index**. Missing or multiple candidates return `wrapped_unmatched` or `wrapped_ambiguous` with `payer=null`.
- Any upstream hop within the receipt must be **same token, exact raw amount, earlier log index, and uniquely matched**. Cross-token equality or later transfers cannot establish provenance.
- When multiple earlier equal-value pay-ins exist, stop at the directly observed payer and mark `unresolved=ambiguous_upstream_equal_value_candidates`. Do not select the first sender.
- Keep at most six hops as before. No external code, private API or new dependency is imported.
- The active engine does not automatically rewrite earlier case studies or cached deposit/link data.

## Tests

Run from the repository root:

```sh
cd monitoring
python3 -m unittest discover -s tests -v
```

The added `tests/test_chainfund_unique_receipt_path.py` covers 12 distinct conditions including legitimate one-hop and wrapped cases, later rather than earlier source transfers, different ERC-20 contracts with equal nominal amounts, duplicated candidate payers, ambiguous credit ties, missing log indices and removed logs. The existing `chainfund._selftest()` and frozen studies are preserved.

## Evidentiary limit

Even a unique same-token earlier Transfer in the **same transaction** is only a possible economic path: ERC-20 balances are fungible, and intermediary contracts may hold preexisting liquidity. A value-matched in-transaction path by itself does not demonstrate beneficial ownership, common control, access to non-public information, or even that a particular credit funded a particular trade.

More definitive attribution requires transaction-level contract semantics, internal traces, uniquely linked protocol order identifiers, balance-conservation checks, and external counterexamples. Until then the decoder describes **apparent receipt senders**, not an established beneficial origin.

A future non-destructive rescore should identify which previously stored `links` depended on ambiguous receipt paths, preserve the original report, and report any changed class C4/C5 classifications as a new timestamped finding rather than silently rewriting evidence.

## Relationship to existing work

- [Historical payer-code and nonce correction in phi_engine](../phi-engine-historical-funding-20261120/README.md).
- [Earlier monitoring engine historical state guard](../historical-payer-state-20261120/README.md).
- [Forensic architecture](../../integrations/forensic-intelligence/FORENSIC_ARCHITECTURE.md).
- [Current predictive verdict](../../EDGE_VERDICT.md): `NO_EDGE_VALIDATED` remains unchanged.
