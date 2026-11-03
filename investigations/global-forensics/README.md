# Global Polymarket forensics

Started 2026-11-02. A research engine that opens any Polymarket account from its address, rebuilds its public funding and exits as far as proof allows, finds other accounts tied to it by money or by behaviour, and looks for similar patterns elsewhere.

An address is not a person. No civil identity is sought or stated here. An alert, a burst or a shared funder is a reason to look, never a finding of insider trading.

## Layout

| Path | Content |
|---|---|
| `AUDIT.md` | Audit of the existing code: three named risks and others, each with its test |
| `TOOLS_AUDIT.md` | External repositories: commit, license, flaws, decision |
| `catalog/` | Markets publicly suspected, each report with author, URL and date. A report is a lead, never ground truth |
| `engine/gf/` | The engine, standard library only |
| `engine/tools/` | Commands, each resumable from what is already on disk |
| `tests/` | Adversarial tests on existing code, and tests of this engine |
| `results/` | Outputs: references, controls, wallet files, market files, graphs, statistics |
| `results/study_sync/` | The frozen study of synchronised entries: plan, lock, register, audit, results |
| `results/study_sync_v2/` | A second study, frozen before its data. Plan, code, controls, lock. No result yet |
| `results/links/` | Links read hop by hop, each with its proof, and the Maduro table's components |
| `engine/audit/` | Claims auditor apart from the engine: it imports nothing from it and reads through other nodes |

Raw answers, tapes and traces are not in git. They live on the external volume, under `global-forensics/`, found by UUID and not by path, and they go through the encrypted backup.

## Levels of an event

| Level | Meaning |
|---|---|
| `LISTED` | A provider's listing: explorer, API, archive. Not read from a node |
| `ONCHAIN_CONFIRMED` | The receipt read from one node shows this move, with its log index and block hash |
| `REVERIFIED` | Two nodes at different hosts return the same receipt |

`data_class` says where the bytes came from: `archived`, `fresh`, `synthetic` or `computed`. Nothing replayed from an earlier report can reach a higher level. Findings keep the repository's `CONFIRMED`, `SUPPORTED`, `HYPOTHESIS`, `REFUTED`, `UNRESOLVED`.

## Sources

| Need | Source | Note |
|---|---|---|
| History on Ethereum, Polygon, Arbitrum | Etherscan v2, free key, block cursor | No log index on token rows: receipts add it |
| History on Optimism | `explorer.optimism.io` | Keyless |
| Windows on Base and BSC | SQD Portal, keyless | About 150 blocks/s on Base, 1,250 on BSC, measured 2026-11-02: windows, not whole chains |
| Proof | Public nodes, two hosts per receipt | |
| Solana | `api.mainnet-beta`, with Tatum as second | publicnode has returned false zeros |
| Accounts, tapes | Polymarket data API `/v2` | v1 answers 410 since its retirement |
| Bridges | Same id on both chains, a CCTP attested message, Relay's `requests/v2` as a pointer until 2026-11-24 | |

HyperSync needs a token and was not used: creating one is an account decision.

## Reproduce

```bash
export PYTHONDONTWRITEBYTECODE=1
cd investigations/global-forensics/engine
python3 ../tests/test_engine.py && python3 ../tests/test_shadow.py && python3 ../tests/test_adversarial_existing.py
python3 tools/verify_references.py ../results/references     # re-reads every reference from nodes
python3 tools/control_federal_case.py ../results/control_federal_case
python3 tools/tapes.py ../catalog/markets.json
python3 tools/run_wallets.py ../results/lists_ballon_dor.json
python3 tools/discover.py ../catalog/markets.json ../results/discovery
python3 tools/run_wallets.py ../results/discovery/wallets.json --light
python3 tools/build_graph.py ../results/graphs
python3 audit/claims_audit.py --self-test
python3 audit/build_checks.py ../results ../results/claims/checks.json
python3 audit/claims_audit.py ../results/claims/checks.json ../results/claims/audit.json --root ..
```

Commands read the store first, so a re-run costs no network and repeats the snapshot of its collection date. Label tables come from `~/Projects/PolySentinel-flow-trace` and `~/Projects/PolySentinel-ChangeNOW-outflows`, read only, and are not redistributed here.

## Resources

One to three network workers. Each run polls a guard: SSD floor 13.5 GB, data volume, a rise of swap, process memory, battery. When a guard stays red the run stops, and it resumes from the store. The external volume is a USB mechanical disk at about 230 IOPS, so nothing here writes one file per answer.
