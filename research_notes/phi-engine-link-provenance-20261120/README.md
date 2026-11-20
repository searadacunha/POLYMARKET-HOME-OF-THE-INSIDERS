# Prospective alerts: quarantine cached pre-guard wallet links

**Date:** 20 November 2026. **Scope:** an additive, non-destructive runtime safeguard for the active `phi_engine`; not a new transaction attribution or proof of insider activity.

## Why this change is necessary

Two independent corrections were accepted on 20 November:
- [Deposit-block code/nonce and source-tag safeguards](../phi-engine-historical-funding-20261120/README.md).
- [Unique ordered receipt path and ambiguity checks](../receipt-link-ambiguity-20261120/README.md).

However the existing `phi_engine` persisted source-to-wallet links in SQLite's `links` table with no record of which method had accepted them. `trace_funding` skips deposits already stored with `status='ok'`; therefore previously cached links could survive both changes and still feed **new** C4/C5 co-funder or recurrent-funder alerts. The evidence section of new alerts likewise listed old links alongside newly checked ones.

That is an observable state/migration gap in the code, not proof that any particular historic link is wrong.

## Implemented fail-closed change

1. Add an independent `link_provenance` table keyed by `(wallet, root, deposit tx)`, with `validator`, receipt SHA-256 and the time this engine checked the original deposit.
2. When the **current** `trace_funding` processes a receipt and accepts a link after the historical-account and receipt-path gates, store a provenance record with `validator='receipt_guard_v1'`.
3. For the live C4/C5 funding-link join, counterpart search, and fan-out, use only links with that explicit provenance. For new alert evidence, also list only accepted method-version links.
4. Preserve all original `links`, `deposits`, `inflows`, `hops`, historical research, and previously emitted alerts **without modification**.
5. Do **not** backfill a provenance row merely because a legacy `deposits` entry has `status='ok'`; it was never checked under the new methodology.

The additional table is backward-compatible with existing SQLite files, and the change is deliberately conservative. A new monitor using an older SQLite file may produce **fewer** C4/C5 group alerts because existing links remain excluded until their original receipt sources can be reprocessed. That loss of coverage must not be presented as an improvement in precision without a prospective comparison.

## Reproduce the regression checks

```sh
cd monitoring
python3 -m unittest discover -s tests -v
```

New isolated cases in `tests/test_link_provenance.py` verify:
- Two cached legacy links cannot trigger a new C4.
- Certifying one side alone cannot manufacture a pair; both sides require new-method records.
- Legacy links cannot inflate the fanout denominator.
- Legacy recurrent funders cannot trigger C5.
- Unknown validator versions are excluded.
- Processing a new receipt records method version and receipt digest, while a cached old receipt is preserved without silent promotion.

## Evidentiary limits

- A `link_provenance` row is **not** an external validation of beneficial ownership, the source-of-funds chain, non-public information, or a trading signal. It means this version of the live collector applied its receipt and historical address gates.
- No production SQLite database was opened, migrated or rescored from GitHub. The engine's additive schema is created only when an operator runs it on their own database.
- A non-destructive rescore of existing links requires actual archival receipts and historical block data; the current SQLite `deposits` table stores a receipt digest, not the original receipt bytes. Backfilling without those bytes would fabricate provenance.
- This is a code-level forensic integrity improvement. `NO_EDGE_VALIDATED` is unchanged, and no prior research finding has been promoted or rewritten.
