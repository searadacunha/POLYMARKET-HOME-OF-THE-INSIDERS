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
