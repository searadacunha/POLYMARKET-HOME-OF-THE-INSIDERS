# Independent phi_engine funding-link time-leakage correction (20 November 2026)

**Scope:** an original engineering correction to the active `monitoring/phi_engine` large-purchase monitor. This is **not** a new blockchain attribution, a confirmed insider operation, or a validated predictive advantage.

## Verified code-level defect

The prior `phi_engine/enrich.py` path labelled historical deposit payers through `describe()`, which read `eth_getCode` and `eth_getTransactionCount` with the block tag `latest`. The same latest-state `addresses` row was reused across every deposit from that payer. `person_like()` then treated an untagged low-nonce current account as a qualifying "plain key" even if its code or nonce was different **when the deposit actually occurred**. The labels came from a present-day Blockscout response. A missing address in a successful tag response was also incorrectly mapped to the empty tag list, permitting a shared-key inference.

Thus C4/C5 multi-wallet funding-link features could admit time-inconsistent observations. This establishes a code-level risk, **not** that any earlier concrete wallet link was factually false. Historical datasets were not rescored in this change.

## Implemented fix

- Add the additive SQLite table `historical_addresses` keyed by **(address, block)**, keeping historical state separate from current service-tag metadata.
- Resolve `eth_getCode` and `eth_getTransactionCount` with the **same explicit historical block tag**, through configured archive-capable RPC endpoints.
- Mark unavailable or malformed historical responses `unavailable`, with null contract/nonce state. Never fall back to `latest` for a historical classification.
- Use only block-pinned state plus existing exclusionary service-tag checks in `person_like_at()`; a missing metadata address is `unavailable`, not an untagged address.
- Apply the block-pinned check to deposit payers, senders preceding contract wrappers and one-hop funding predecessors.
- Persist the block-pinned observations for reproducible diagnostic replay; make the alert's displayed payer class depend on the historical state, reporting unknown if unavailable.
- Leave previously accepted studies, hashes, original evidence, main README, and existing stored links unmodified.

The `person_like` criterion remains **heuristic**, not evidence of a shared human owner. Today's public tags can be used to exclude known services, but an absent current label cannot prove the address lacked a service function historically.

## Offline regression coverage

```sh
cd monitoring
python3 -m unittest discover -s tests -v
```

The new `test_phi_engine_historical_funding.py` cases independently fake the latest and historic RPC responses. They check opposite contract states across time, distinct snapshots of one payer at different blocks, failures/malformed responses without a current-state fallback, missing public metadata, direct funding with a historically plain key, a historically deployed contract that must not become a link, and a known tagged service.

## Remaining limits

1. Existing `deposits` and `links` rows written under the old code are **not retroactively reclassified**, even if new alerts read from the same SQLite file. A safe re-evaluation requires a separately documented migration and historical snapshot audit.
2. Historical state availability depends on the archive RPC. `unavailable` excludes a shared-key link, so apparent detection coverage may decline until better data arrive; this is safer than a false positive.
3. A deposited wallet, an EOA at a particular block, a low nonce and an empty *current* tag list are **not** evidence of a single beneficial owner or non-public information.
4. Existing fuzzy graph joins, historical profile fields, and classification thresholds were not retuned. The study's `NO_EDGE_VALIDATED` verdict is unchanged.
5. `phi_monitor` was separately fixed in [historical payer-state guard](../historical-payer-state-20261120/README.md); this patch addresses a distinct live engine with a separate SQLite schema and C4/C5 funding-link logic.

## Provenance and relationship to previous research

- [Point-in-time code audit of external suspicion scores](../point-in-time-external-score-20261119/REVIEW.md) documents why retrospective/current state cannot enter a past detection decision.
- [Forensic architecture and evidence separation](../../integrations/forensic-intelligence/FORENSIC_ARCHITECTURE.md) distinguishes verified transfers, behavioural links and account/control claims.
- [Existing historical payer-state correction in the other monitor](../historical-payer-state-20261120/README.md).

This patch is original implementation work in the owner's repository; no external implementation or data was copied.
