# Forensic Intelligence, first offline adapter

**Status: staged research, read-only and NOT connected to live PolySentinel.** No third-party packages, node calls, API tokens, transactions or automated trade actions. Do not treat output as identification of an insider.

This folder intentionally avoids copying the existing `signal_engine/fund_flow`. It adds a strict, portable EVM evidence schema and simple temporal comparisons for cases already archived elsewhere in this private repository.

## Contents

- `ledger.py`: exact integer/decimal validation, on-chain money graph, separately observed control graph, service/unknown shared-funder exclusions, CSV/JSON/GraphML evidence export (all required edge fields).
- `temporal.py`: wallet/outcome proximity at 5, 30, 60, 300, 900 and 3,600 seconds, with observation-time cutoff and an exploratory wallet-block circular-shift placebo.
- `fixtures/ballon_dor_documented.json`: 3 transfers copied from the **already-documented** Ballon d'Or findings, NOT freshly verified from a node.
- `tests/test_integration.py`: stdlib negative, integrity and synthetic tests; the exact tested SHA is pinned in [TOOLS_BENCHMARK](TOOLS_BENCHMARK.md).
- Seven required investigation/design reports are sibling Markdown files.

Run tests on Python 3.11+ without dependencies:

```sh
cd integrations/forensic-intelligence
python3 -m unittest discover -s tests -v
```

Generate sample financial exports into a **new empty folder** (never overwrite source):

```sh
cd integrations/forensic-intelligence
python3 - <<'PY'
import json
from ledger import save_exports
fixture = json.load(open('fixtures/ballon_dor_documented.json', encoding='utf-8'))
print(save_exports(fixture['edges'], '/tmp/phi-demo-new'))
PY
```

Output is `evidence_edges.csv`, `financial_graph.json` and `financial.graphml`. A repeated run to the same non-empty output directory refuses to overwrite.

**Limitations:** only EVM transactions; no native RPC/capture/live wallet-history scanning; no canonical event-range coverage; no external price valuation; no realized PnL reconstruction; no automatic proxy-owner attribution; no Solana/TRON adapter; no complete market crawl. Confirmed means **confirmed in the cited source**, not independently reverified by this new adapter.

A financial graph edge records money movement, not identity. Common funding counts only after a noncustodial role has independent supporting evidence. Unknown and shared service are unresolved. A temporal p-value is a null-comparison statistic conditional on a chosen universe, not a probability of insider wrongdoing.

## Rules before real deployments

1. Check the existing manifests and re-use verified local data. The original Mac folders, external disk and running agents were **not accessible** in this ChatGPT session.
2. First integrate in a shadow mode on a dedicated branch. Do not change current frozen PolySentinel categories, trained thresholds, alert journal or collectors.
3. Supply a historical **observed_at** for each input row and a contract/ABI/block coverage ledger. An absent log index in batch fills means unmeasured event completeness.
4. A real new result must cite original transactions, block hashes, receipt/log indices and replayable controls; a copied historical fixture alone is not new proof.
5. Treat automatic comparison of USD-equivalent amounts across ChangeNOW, an exchange or Monero as only an unverified candidate.


## Second offline validation pass — 2026-11-02

The initial 13-test baseline has been extended to **34 discovered tests: 33 passed, one skipped** in isolated Linux Python 3.13. The skipped test reads the complete original ChangeNOW CSV, which was accessible through the connected GitHub API but not mounted in this isolated Python runtime. That is not a failed on-chain test, and there has been **no new independent node verification**.

New modules:

- `coverage.py` refuses to equate different chains, contracts, topic0 signatures or protocol variants (CLOB V1 vs CTF Exchange V2 vs Protocol V2). It reports half-open block-range gaps, truncated pages, incomplete cursor exhaustion, and late-observed scans separately. Provider-reported completion is **not** independent verification of missing-log absence.
- `source_ingest.py` accepts the existing `investigations/changenow-proof/sources/data/verified_transfers.csv`, preserving receipt hashes and log-index limitations. It deliberately leaves the `protocol` field unset: a service label is **not** proof of an exchange order, sender ownership or cross-chain payout matching.
- `ledger.py` now rejects two contradictory amounts or counterparties assigned to the same EVM log. `temporal.py` now rejects conflicting fills with the same identity instead of keeping an arbitrary first occurrence.

Run: `python3 -m unittest discover -s tests -v` from this folder. See the updated [TOOLS_BENCHMARK.md](TOOLS_BENCHMARK.md) for exact committed blob SHA-1 values and the negative controls.

These are **offline data-integrity improvements**, not a live investigator, not a coverage certification, and not a measured gain in detecting insider trading.
