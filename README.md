# Polymarket, Home of the Insiders

Eleven accounts publicly named around the 2026 Ballon d'Or markets deposited **$304,137.63** and withdrew **$493,094.76**.

Eight accounts linked by transfers of funds, active on the Maduro and Iran strike markets, show a combined PnL of **$509,993.25**.

Were they insiders? A blockchain shows who paid whom and when. It does not show what anyone knew. This repository keeps those two things apart: every claim carries its level of proof, its sources and its limits, and the failed ideas stay in the record.

The title is the question, not the verdict. **No investigation here demonstrates insider trading.**

## What the evidence says

- **Demonstrated.** One direct transfer between the keys of two named accounts, a wallet the press does not name funded by the key of one of them, a network of eight accounts linked by funds, and the exact accounting of deposits and withdrawals.
- **Refuted.** Funding shortly before the first bet as a distinctive trait. Simultaneous redemptions as a link (one batch held 2,711 accounts). A shared ChangeNOW wallet as a link. Eight preregistered trading signals out of sample.
- **Not demonstrated.** Common ownership, coordination of bets, access to private information, and any use of Monero.

Read the [master report](MASTER_REPORT.md) for every finding by level, the links between investigations, the contradictions, and what is missing to conclude. The [inventory](INVENTORY.md) gives the state of each investigation.

## The investigations

| Topic | Investigations |
|---|---|
| 2026 Ballon d'Or | [wallet by wallet](investigations/ballon-dor-wallets/README.md), [independent audit](investigations/ballon-dor-audit/README.md), [funding and exits](investigations/ballon-dor-flow-trace/README.md), [market census](investigations/ballon-dor-census/README.md) |
| ChangeNOW | [what is proven for the 11 accounts](investigations/changenow-proof/README.md), [reverse analysis of payouts](investigations/changenow-outflows/README.md), [payees who bet on Polymarket](investigations/changenow-polymarket/README.md) |
| Maduro and Iran | [network, funding, signals](investigations/maduro-iran/README.md) |
| Prospective detection | [PolySentinel](investigations/polysentinel/README.md), [recovery harness](investigations/polysentinel-harness/README.md), [publication copy](investigations/polysentinel-public/README.md) |
| Other | [security incidents](investigations/hacks-parallel/README.md), [search for an edge](investigations/edge-polymarket/README.md), [the lost corpus](investigations/corpus-historique/README.md) |

[METHODOLOGY.md](METHODOLOGY.md) explains the rules and the errors already paid for. [shared/README.md](shared/README.md) points to the reusable code.

## How to read a finding

| Level | Meaning |
|---|---|
| `CONFIRMED` | Shown directly by reproducible elements |
| `SUPPORTED` | Converging signs, proof incomplete |
| `HYPOTHESIS` | Interpretation not demonstrated |
| `REFUTED` | Contradicted by the data |
| `UNRESOLVED` | Not enough data |

An address is not a person. A label on a wallet does not identify its owner. A public allegation is not ground truth.

## Check it yourself

Python 3 standard library, no install:

```bash
python3 scripts/test_phi.py             # self-test of the tools
python3 scripts/validate_evidence.py    # hashes, sources, secrets, links
python3 scripts/build_master_report.py --check
```

`validate_evidence.py` checks the SHA-256 of imported evidence against its manifest and refuses findings with numeric or address references absent from their cited sources. This is a consistency check, **not** an independent replay of every investigation, and it cannot validate local-only raw captures that are not in the clone.

## What is not here

- **Raw data.** Collector database, HTTP caches and raw captures total about 19 GB. Each file is listed with its size and hash in the investigation's `data_manifest.json`, and [datasets/manifests/local_only.json](datasets/manifests/local_only.json) gathers them. These files are not archived here, so a script that reads them does not run from a clone: each investigation's README says how to reproduce it.
- **Profile data.** Rows carrying Polymarket `bio` or `pseudonym` fields are refused by the import.
- **Third-party content.** Articles, screenshots, label lists and other repositories are referenced, not redistributed.

Each `investigations/<id>/sources/` folder is a verbatim copy of the original working files, mostly in French. The `README`, `STATUS`, `FINDINGS` and `EVIDENCE` files around it are in English.

## Layout

```
MASTER_REPORT.md     generated, every finding by level
INVENTORY.md         generated, state of each investigation
METHODOLOGY.md       rules of evidence
CONTRIBUTING.md      how to add or update an investigation
investigations/<id>/ README, STATUS, FINDINGS, EVIDENCE, data_manifest.json, sources/
datasets/manifests/  generated, files not archived here
shared/              index of the reusable code
scripts/             import, validation, report
```

Work in progress: several investigations are still running, and their findings are marked provisional.
