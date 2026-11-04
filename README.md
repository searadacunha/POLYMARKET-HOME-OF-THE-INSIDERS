# Polymarket, Home of the Insiders

Independent on-chain research into how Polymarket accounts are funded, how they trade, and where their money goes. Fourteen investigations bring together transaction evidence, accounting, funding networks and monitoring tools.

**The investigation has documented direct payment links between Polymarket account keys and resolved a 2,969.568353 mUSD exit from Ethereum to a vmUSD vault on Monad.** The findings below link to the evidence and the checks behind them.

## Key findings

### A resolved route through Relay

A payment of **2,969.568353 mUSD** from the owner key of Polymarket account `0xa8e6…74a5` was traced through Relay from **Ethereum to Monad**. The destination transaction deposits the funds into a vault and credits **2,904.308540 vmUSD shares** to:

`0xea1a3f324c5ee313bb04d9e642c39c8b29e7454b`

Relay explicitly connects the two transaction hashes. The transactions are **29 seconds apart**. Both receipts succeed, and the destination logs confirm the vault deposit and share mint. This resolves a previously open exit and provides a concrete beneficiary address for further tracing. mUSD and vmUSD are different units: the share count is not a measure of funds lost.

[Read the complete trace, archived responses and offline verification](research_notes/relay-followup-2026-11-04/REPORT.md).

### Direct payments and funding

| Finding | Evidence |
|---|---|
| The key associated with `brace227` sent **0.002048944 ETH** to the key associated with `kraben006`. | [Transaction and scope](investigations/ballon-dor-wallets/FINDINGS.md#f-002--confirmed--the-key-of-brace227-sends-0002048944-eth-about-553-to-the-key-of-kraben006) |
| The same `brace227` key sent **5,170 USDC** in two transfers to the key controlling another Polymarket trading wallet, outside the eleven-account cohort. | [Funding investigation](investigations/ballon-dor-flow-trace/FINDINGS.md) |
| Two payments totaling **834.848793 USDC** reached the `kraben006` key from an address attributed to ChangeNOW. The transfers and the service attribution have separate evidence levels. | [ChangeNOW findings](investigations/changenow-proof/FINDINGS.md) |

These are documented financial relationships. Common ownership and the connection between those ChangeNOW payments and subsequent bets remain unresolved.

## Accounting results

| Cohort | Published result | Scope |
|---|---|---|
| Eleven accounts studied around the 2026 Ballon d'Or markets | **$304,137.63 deposited; $493,094.76 withdrawn** in 46 deposits and 25 withdrawals | **$188,957.12 net cash flow**, calculated before rounding, across the observed wallets. Four accounts retain a residue or positions; this is not complete trading PnL. |
| Seven settled accounts within that cohort | **$129,367.79 net cash flow** | A subset of the eleven accounts. It excludes costs outside the observed wallets and other accounts potentially controlled by the same people. |
| Eight accounts studied around the Maduro and Iran markets | **$509,993.24 trading PnL**, including remaining position value | A separate, retrospectively selected cohort. External outflows minus external capital total **$509,624.54**, a different measure. |

Sources: [Ballon d'Or reconciliation](investigations/ballon-dor-wallets/sources/evidence/contre_verification_20261102/reconciliation_montants.json), [Maduro/Iran accounting and formula](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md), [full-precision export](investigations/maduro-iran/sources/phase2/pnl_table.json), and [external-flow reconciliation](investigations/maduro-iran/sources/phase3/RAPPORT_PHASE3_2026-09-29.md). The [arithmetic audit](investigations/maduro-iran/results/accounting_audit_2026-11-04.json) documents aggregate rounding. These figures summarize the published evidence.

## Explore the investigations

The [master report](MASTER_REPORT.md) collects classified findings, contradictions and open questions. The [inventory](INVENTORY.md) records each investigation's published state and data availability.

| Topic | Where to read |
|---|---|
| 2026 Ballon d'Or | [Wallet-by-wallet study](investigations/ballon-dor-wallets/README.md), [independent audit](investigations/ballon-dor-audit/README.md), [funding and exits](investigations/ballon-dor-flow-trace/README.md), [market census](investigations/ballon-dor-census/README.md) |
| ChangeNOW | [Evidence for the eleven accounts](investigations/changenow-proof/README.md), [reverse analysis of payouts](investigations/changenow-outflows/README.md), [payees who traded on Polymarket](investigations/changenow-polymarket/README.md) |
| Maduro and Iran | [Network, accounting and signal studies](investigations/maduro-iran/README.md) |
| Monitoring | [PolySentinel](investigations/polysentinel/README.md), [recovery harness](investigations/polysentinel-harness/README.md), [publication copy](investigations/polysentinel-public/README.md) |
| Other work | [Security incidents](investigations/hacks-parallel/README.md), [search for an edge](investigations/edge-polymarket/README.md), [lost historical corpus](investigations/corpus-historique/README.md) |

Work on other branches is tracked in the [open pull requests](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pulls). Published states are snapshots; collector health is checked separately.

## Method and interpretation

Payment links, wallet control, coordinated betting and access to non-public information are assessed as separate claims. **The documented transfers do not by themselves establish insider trading.** Shared services, matching amounts or nearby timestamps cannot identify a common customer. The Relay trace establishes the credited address, not its human controller or current holdings.

Three validation limits matter when reading the research:

- **Ballon d'Or comparisons:** the original base-rate estimate is invalid because **48 of 78 comparator wallets were unusable**. [Counter-verification](investigations/ballon-dor-wallets/sources/reports/CONTRE_VERIFICATION.md).
- **Maduro/Iran signals:** none of the eight preregistered signals met the out-of-sample exploitation criteria; a later predictive signal did not establish an executable profitable strategy. [Classified results](investigations/maduro-iran/FINDINGS.md).
- **Monitoring:** historical replay and prospective detection are evaluated separately. Prospective detection accuracy remains unestablished. [PolySentinel findings](investigations/polysentinel/FINDINGS.md).

| Evidence level | Meaning |
|---|---|
| `CONFIRMED` | Directly supported within the stated scope by reproducible evidence |
| `SUPPORTED` | Converging evidence with material gaps remaining |
| `HYPOTHESIS` | An interpretation still to be tested |
| `REFUTED` | The stated claim fails its documented check |
| `UNRESOLVED` | Available evidence cannot settle the claim |

[METHODOLOGY.md](METHODOLOGY.md) details the evidence rules, statistical requirements and documented failure modes.

## Reproduce and validate

Verify the Relay trace against the archived responses, without network access:

```bash
python3 research_notes/relay-followup-2026-11-04/verify.py
```

Run the repository checks with the Python 3 standard library:

```bash
python3 scripts/test_phi.py
python3 scripts/test_integrity_regressions.py
python3 scripts/validate_evidence.py
python3 scripts/build_master_report.py --check
```

These checks cover the central utilities, integrity regressions, evidence manifests and generated reports. Each investigation documents its own analysis and reproduction requirements; some need additional packages, raw inputs, RPC access or credentials. Repository checks and full analytical replays have different scopes.

## Data and code

| Path | Purpose |
|---|---|
| `research_notes/` | Focused follow-ups, including the resolved Relay exit |
| `investigations/<id>/` | Findings, evidence index, code, import manifest and source snapshot |
| `MASTER_REPORT.md` and `INVENTORY.md` | Generated research overview and investigation states |
| `datasets/manifests/` | Index of inputs marked `local_only`, which are absent from an ordinary clone |
| `scripts/` | Import, validation, reporting and backup tools |
| `shared/` | [Reusable components](shared/README.md) |

Original `sources/` trees and frozen studies retain their recorded history. Authored investigation files are in English; imported evidence keeps its original language. Import manifests record file hashes, sizes and exclusions, including secrets, profile fields and raw HTTP caches.

[BACKUP_STATUS.md](BACKUP_STATUS.md) records separate backup verification at its stated timestamp. A manifest entry alone is not a backup or proof of restore. [CONTRIBUTING.md](CONTRIBUTING.md) describes the update and publication workflow.
