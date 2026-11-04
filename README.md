# Polymarket, Home of the Insiders

Independent on-chain investigations into Polymarket funding, trading activity and withdrawals. This repository brings together the evidence, code and recorded decisions from fourteen investigations.

**The current evidence establishes financial transfers and accounting results. It does not establish insider trading.** A payment link, common control of wallets, coordinated bets and access to non-public information are separate claims. Each requires its own evidence.

Start with the [master report](MASTER_REPORT.md) for classified findings and contradictions, or the [inventory](INVENTORY.md) for each investigation's last recorded state. Those states describe published snapshots, not a live check of the collectors.

## Results, with their scope

| Investigation | Result in the published evidence | What the figure means |
|---|---|---|
| Eleven accounts publicly named around the 2026 Ballon d'Or markets | **$304,137.63 deposited; $493,094.76 withdrawn** across 46 deposits and 25 withdrawals | Gross wallet flows. Their difference, **$188,957.12**, is net cash flow across the eleven accounts, not a complete trading PnL. Four accounts retain a residue or positions. |
| Seven settled accounts within that same eleven-account cohort | **$129,367.79 net cash flow** | A subset of the first row, not an additional amount. It excludes costs outside the observed wallets and any other accounts controlled by the same people. |
| Eight accounts studied around the Maduro and Iran markets | **$509,993.24 trading PnL**, including remaining position value, aggregated before rounding | A separate cohort, selected retrospectively. The report uses SELL + REDEEM + MERGE + remaining value - BUY - SPLIT. Its external outflows minus external capital equal **$509,624.54**, which is a different measure. |

The Ballon d'Or totals can be summed from the [per-account reconciliation](investigations/ballon-dor-wallets/sources/evidence/contre_verification_20261102/reconciliation_montants.json). The Maduro and Iran figures are documented in the [phase 2 report](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md), its [full-precision accounting export](investigations/maduro-iran/sources/phase2/pnl_table.json), and the [phase 3 flow reconciliation](investigations/maduro-iran/sources/phase3/RAPPORT_PHASE3_2026-09-29.md). The [arithmetic audit](investigations/maduro-iran/results/accounting_audit_2026-11-04.json) explains the one-cent correction from $509,993.25, obtained by adding already-rounded rows, to $509,993.24, obtained by rounding the aggregate once. Rechecking these published tables is not an independent retrieval of the underlying chain history.

### Payment links that survive the checks

- The key associated with `brace227` sent **0.002048944 ETH** to the key associated with `kraben006`. This is a documented transfer between two keys. The amount is small and does not establish common ownership or access to information. [Evidence](investigations/ballon-dor-wallets/FINDINGS.md#f-002--confirmed--the-key-of-brace227-sends-0002048944-eth-about-553-to-the-key-of-kraben006).
- The same `brace227` key sent **5,170 USDC** in two transfers to the key controlling another Polymarket trading wallet, outside the eleven-account cohort. Funding an account does not establish that the funder controls it. [Funding investigation](investigations/ballon-dor-flow-trace/FINDINGS.md).
- Two payments totaling **834.848793 USDC** reached the `kraben006` key from a service address attributed to ChangeNOW. The transfers are documented; the service attribution has a separate evidence level, and no documented path connects those payments to the later bets. [ChangeNOW findings](investigations/changenow-proof/FINDINGS.md).

These claims describe the scope actually examined. They do not imply that every chain, account or intermediary was observed.

### Results that limit the conclusions

- Shared service wallets, matching amounts and nearby timestamps do not establish a common customer or owner. Batch redemptions also produced false links between unrelated accounts.
- The original Ballon d'Or base-rate calculation is invalid: **48 of 78 comparator wallets were unusable**. It cannot support a prevalence estimate. [Counter-verification](investigations/ballon-dor-wallets/sources/reports/CONTRE_VERIFICATION.md).
- None of the eight preregistered Maduro/Iran signals met the study's out-of-sample exploitation criteria. A later predictive signal did not establish an executable profitable strategy. [Classified results](investigations/maduro-iran/FINDINGS.md).
- PolySentinel was first deployed after the Ballon d'Or affair had become public. Its conditional historical replay is a case study, not evidence that it detected the event in advance. Prospective detection accuracy remains unestablished. [Monitoring findings](investigations/polysentinel/FINDINGS.md).
- Common ownership, coordinated betting, inside information and a Monero route are not demonstrated by the available evidence. Missing observations are retained as limits, not converted into proof of absence.

## Investigations

| Topic | Where to read |
|---|---|
| 2026 Ballon d'Or | [Wallet-by-wallet study](investigations/ballon-dor-wallets/README.md), [independent audit](investigations/ballon-dor-audit/README.md), [funding and exits](investigations/ballon-dor-flow-trace/README.md), [market census](investigations/ballon-dor-census/README.md) |
| ChangeNOW | [Evidence for the eleven accounts](investigations/changenow-proof/README.md), [reverse analysis of payouts](investigations/changenow-outflows/README.md), [payees who traded on Polymarket](investigations/changenow-polymarket/README.md) |
| Maduro and Iran | [Network, accounting and signal studies](investigations/maduro-iran/README.md) |
| Prospective monitoring | [PolySentinel](investigations/polysentinel/README.md), [recovery harness](investigations/polysentinel-harness/README.md), [publication copy](investigations/polysentinel-public/README.md) |
| Other work | [Security incidents](investigations/hacks-parallel/README.md), [search for an edge](investigations/edge-polymarket/README.md), [lost historical corpus](investigations/corpus-historique/README.md) |

Research on other branches is not automatically part of the findings on `main`. Check the [open pull requests](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pulls) and each branch's stated limits before using its results.

## Evidence levels

| Level | Meaning |
|---|---|
| `CONFIRMED` | Directly supported within the stated scope by the cited reproducible evidence |
| `SUPPORTED` | Converging evidence, with material gaps remaining |
| `HYPOTHESIS` | An interpretation that has not been demonstrated |
| `REFUTED` | The stated claim fails the documented check; this does not automatically establish its opposite |
| `UNRESOLVED` | Available evidence cannot settle the claim |

An address is not a person. A service label does not identify a customer. Public allegations are not ground truth. [METHODOLOGY.md](METHODOLOGY.md) records the rules and the errors that led to them.

## Reproduce and validate

Repository-level tools use the Python 3 standard library:

```bash
python3 scripts/test_phi.py
python3 scripts/test_integrity_regressions.py
python3 scripts/validate_evidence.py
python3 scripts/build_master_report.py --check
```

These commands have distinct purposes:

- `test_phi.py` tests the central import, scanning and report utilities. It does not run every investigation's tests.
- `test_integrity_regressions.py` exercises malformed evidence, import races and recovery failures using synthetic files and archives. It does not operate the live backup service.
- `validate_evidence.py` checks investigation structure, imported-file hashes, evidence-table hashes, selected secret/profile patterns, links and the presence of cited values. Finding a number in a cited file does not establish its meaning, statistical validity or relationship to a particular account.
- `build_master_report.py --check` checks that the generated reports and local-only index match the current metadata. After an accepted investigation update, regenerate them with `python3 scripts/build_master_report.py`.

Each investigation's README lists its own reproduction steps. Some require additional packages, unpublished raw inputs, RPC access or service credentials. A successful repository check is not a full replay of those analyses. The recovery harness and live monitoring engine also require separate operational checks.

## Data availability and preservation

- **Git checkout.** Reports, selected evidence, code and import manifests are versioned here. `data_manifest.json` records the path, size, hash and import decision for the original files.
- **Files marked `local_only`.** These are absent from an ordinary clone. The [generated index](datasets/manifests/local_only.json) records their scope; a manifest entry alone is not a backup.
- **Separate backups.** [BACKUP_STATUS.md](BACKUP_STATUS.md) records encrypted backup and verification results as of its own timestamp. That status is separate from clone availability and does not establish current collector health or a successful restore on another machine.
- **Original evidence.** Each `investigations/<id>/sources/` tree is an imported snapshot, mostly in French. Corrections belong in the authored investigation files or a documented subsequent snapshot. Frozen studies and original evidence must retain their recorded history.
- **Excluded material.** Import rules filter secrets, raw HTTP caches, Polymarket profile fields such as `bio` and `pseudonym`, images and third-party content. Exclusions limit what can be reproduced from a clone.

The authored investigation files are in English. [CONTRIBUTING.md](CONTRIBUTING.md) describes the update workflow, and [shared/README.md](shared/README.md) indexes reusable code.

## Layout

| Path | Purpose |
|---|---|
| `MASTER_REPORT.md` | Generated findings, contradictions and unresolved questions |
| `INVENTORY.md` | Generated investigation states and data availability |
| `METHODOLOGY.md` | Evidence and statistical rules |
| `investigations/<id>/` | README, status, findings, evidence index, manifest and source snapshot |
| `datasets/manifests/` | Generated index of inputs absent from a clone |
| `scripts/` | Import, validation, reporting and backup tools |
| `shared/` | Index of reusable components |
