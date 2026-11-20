# Historical funding-state guard (20 November 2026)

**Scope:** a reproducible correction to the active Polygon funding monitor, **not** a new wallet-ownership attribution, insider case, or validated predictive signal.

## Concrete defect in the prior implementation

Before this change, `monitoring/phi_monitor/chain.py::account_kind(address, block)` queried `eth_getCode(address, "latest")`, even when a historical `block` was supplied. It queried historical `eth_getTransactionCount` where possible but silently fell back to a present-day nonce if the historical query failed. The resulting `kind` could therefore combine two different observation times, contaminate historical funder classification, and affect which addresses `detect._roots` was allowed to use in a shared-funder grouping.

`monitoring/phi_monitor/collect.py::funding` also cached the classification of a payer by address alone within the collection, even if the address appeared in separate transfer blocks.

This is a **code-level leakage risk**, not proof that any previously reported cluster is wrong. No stored dataset was independently rescored in this change.

## Implemented original fix

1. When a historical block is supplied, retrieve both `eth_getCode` and `eth_getTransactionCount` with the **same historical block tag**. Do not use a latest-state fallback for either method.
2. If a public endpoint cannot provide the required historical state, return `kind: unknown`, `nonce: null`, and `unresolved: historical_state_unavailable`, rather than a purported historical plain key. No personal ownership is inferred.
3. Cache classifications by **(payer, transfer block)**, not merely by address, so a later transfer does not inherit an earlier block's account classification.
4. Leave explicit live (no historical block) reads at `latest`. Keep the known zero-address mint classification.
5. The existing funding-root traversal only accepts `kind == "key"`; unavailable historical state is therefore excluded from purported personal-key shared funding.

No new network, dependencies, paid provider, wallet watchlist, or trading facility was added.

## Offline regressions

Run from the repository root:

```sh
cd monitoring
python3 -m unittest discover -s tests -v
```

New tests in `monitoring/tests/test_account_kind_asof.py` use mocked RPCs and an in-memory SQLite store to check:

- Historical plain key despite hypothetical present-day contract/large nonce.
- Historical contract regardless of later state.
- Missing code or nonce returning `unknown` without a latest fallback.
- Malformed historical RPC responses.
- Explicit current-state classification and live-source failures.
- Zero address, invalid block tags.
- Separate block-aware classifications for transfers from one payer.
- No upstream recursion from a payer with unknown historical state.

## Limitations and next audit

- Existing database funding rows and published historical case analyses are **not** retroactively corrected. The monitor checkpoints completed funding windows. Any historical rescore requires a separate, non-destructive migration or independently reconstructed dataset with evidence hashes.
- Public RPC endpoints may lack archive state; this change deliberately prefers **unresolved** to a fabricated historical classification. Measure the new unknown rate before claiming coverage improvement.
- The heuristic `key` vs. `high_volume_key` is based on nonce only; even a verified low-nonce EOA is **not** proof of a single person or an insider.
- `safe_owners` still uses current owner keys when invoked; this patch does not claim historical Safe-owner attribution.
- No event-level label validation, out-of-sample signal or executable-price backtest was performed. The overall research verdict remains `NO_EDGE_VALIDATED`.

## Research provenance

This code correction responds to the **point-in-time leakage** and shared-service ambiguity documented by the repository's own research:

- [Source-code audit of external suspicion scoring](../point-in-time-external-score-20261119/REVIEW.md).
- [GitHub forensic tooling audit](../github-tooling-audit-2026-11-06/REPORT.md).
- [Existing forensic source-integration decisions](../../integrations/forensic-intelligence/NEXT_INVESTIGATIONS.md).

No third-party source was copied. The improvement concerns the monitor's own state-fetching and caching semantics, not the accuracy of another project's published classifier.
