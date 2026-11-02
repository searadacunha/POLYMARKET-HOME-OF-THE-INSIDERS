# Tools benchmark — reproducible first pass

**Date:** 2026-11-02. The run took place in an isolated Linux Python environment, **not on the user's Mac**. Local source archives, 19+ GB of unpublished datasets and any production collector were **not accessible**. No external GitHub source or package was executed. Hence this is a **unit/contract test**, NOT a verified performance improvement in live detection or full workflow.

## Exact source versions tested and committed

| File | Git blob SHA (tested bytes = committed bytes) |
|---|---|
| `ledger.py` | `af9309b928a85c41ad8b6df458e9ae582ebd2478` |
| `temporal.py` | `e41c1866b80cfb8104e826031f64133420b33d60` |
| `tests/test_integration.py` | `8d589b2b9f1c3ae91a83638f43cd07cd9d1e4317` |
| `fixtures/ballon_dor_documented.json` | `f408c546d67ade573d6d736b5ab47f6643b4f6a4` |

## Actually executed checks

```sh
cd integrations/forensic-intelligence
python3 -m unittest discover -s tests -q
# Ran 13 tests; OK
```

- **13/13 PASS**: 3 documented transfer fixtures, duplicate rejection, amount unit consistency, float rejection, UTC requirement, service/unknown shared funders excluded, candidates not treated as financial edges, GraphML holds every edge field, exports do not overwrite, 6 synchronization windows, no future observation leakage, no cross-outcome pairing, same-transaction distinct log indices, seeded null-model result.
- **Known case, previously documented:** 0.002048944 ETH transfer and 2,210+2,960 USDC transfers from `brace227` EOA, all 3 retained as transfers; 3 unique nodes, 3 unique edges; zero purported common-owner findings. Source is [ballon-dor-flow-trace](../../investigations/ballon-dor-flow-trace/FINDINGS.md); **no fresh RPC verification**.
- **Synthetic adversarial sample:** 180 artificial trades, 2,736 wallet-pair/window records over six windows. `synchronized_pairs` elapsed **0.050962 seconds**, exploratory 199-draw null elapsed **0.181948 seconds**, Python tracemalloc peak **1,934.1 KiB**. These numbers depend on one runtime and do not extrapolate to 1M events.
- Synthetic null: 90 observed 5-second distinct wallet pairs, median 9 under circular shifts, empirical `p=0.005` with `(1+exceedances)/(199+1)`. **This is deliberately constructed synthetic convergence, not an insider signal and not a real-market p-value.**

### Reference data export SHA-256

| Generated sample (3 documented edges) | SHA-256 |
|---|---|
| `evidence_edges.csv` | `0273d79f1d80aeb084e738e42bdca32b65dea8cce6201de89ab0c8973496ee4b` |
| `financial_graph.json` | `25cbbde085c64e79dcd448d893945d20bc002ff417cddaa305609ac7ff21692c` |
| `financial.graphml` | `65711fdb271a8ecba66aac30edc0a956273b598d17d3a8175111c42420d3bba2` |

These hashes are for **newly generated test artifacts only**, not source backups.

## Before/after assessment

| Metric | Existing PolySentinel baseline | New offline adapter | Conclusion |
|---|---|---|---|
| Full-source runtime/peak RAM on Mac | Not executed here | Not executed on Mac | **NON_ESTIMABLE** |
| Complete market coverage / recall | Not measured; documented partial feeds | Not attempted | **No evidence of improvement** |
| Real-time error/false alarm rate | No ground truth; shadow mode incomplete | Synthetic only | **NON_ESTIMABLE** |
| Existing bidirectional flows and Relay identification | Already implemented | No replacement | **Keep baseline** |
| Standardized all-fields CSV/JSON/GraphML evidence export | No single comparable interface established in inspected modules | **Implemented and tested** | **Narrow verified engineering gain** |
| Exact integer/decimals and service-funder safety checks | Existing protections scattered among modules | **13 exercised cases cover core guardrails** | **Verified local behaviors, not baseline superiority** |
| 5s,30s,60s,5m,15m,60m windows + one null | Several ad-hoc collective tests exist | **Implemented on synthetic/fixture** | Usable experiment, **not validated on real market** |
| Distinct fills in a single transaction | Known risk in market feeds | Explicit per-log dedup test | Tested negative control |
| New on-chain discoveries | Existing cases only | **0** | No research claim |

## External library smoke test (actually executed, sandbox only)

`networkx==3.6.1` was already installed in the isolated Linux environment; **no install or network call**. Its [LICENSE.txt](https://github.com/networkx/networkx/blob/main/LICENSE.txt) is BSD-3-Clause (not resolved by GitHub's NOASSERTION metadata). A `MultiDiGraph` built from the **three documentary Ballon d'Or transfers** preserves **3 nodes, 3 edges, all 3 exact raw amounts and ONCHAIN_CONFIRMED classifications**, PASS (graph construction **0.000283s** on this tiny fixture). This checks basic graph representation, not 2026 contract decoding, ownership or full-path coverage. **Decision: reference/optional adapter, no demonstrated benefit over stdlib for this case.**

## Reject / defer decisions

- **Reject as direct production detector:** retrospective winner-first scoring from `vsbtc/polymarket-insider-detection`: selection after outcome, tests not independently reproduced.
- **Do not deploy:** a second Docker/Redis/Postgres `pselamy` service, Neo4j or GraphSense server; current hardware capacity and incremental value unmeasured.
- **License gate:** `warproxxx/poly_data` GPL-3 GitHub metadata conflicts with MIT in its `pyproject.toml`; `moose-code/polymarket-indexer` lacks a license; the Polymarket exchange sources are BSL 1.1 for non-production use. Use ABI/documentation reference, not copied source.
- **Pilot later:** official Polymarket PublicClient for current metadata and HyperSync bounded log/trace retrieval, only after true coverage, cost and reproducibility tests.

## Missing tests before claims about the final system

1. Independent on-chain reconfirmation of all fixture transactions, including receipt log index and token address.
2. Comparison on **identical local raw data** against `signal_engine/fund_flow/trace.py` with provenance, resource counters and expected negative controls.
3. Full history by market contract and block, with CLOB V1/V2/protocol V2 reconciliation.
4. Mac arm64, local SSD and external disk stress tests, verifying backup and no impact to running jobs.
5. Truly prospective holdout (alerts sealed before public announcements), comparable market controls, family-wise multiple-testing correction and falsification checks.

**Conclusion:** meaningful but deliberately small, reproducible offline adapter; **the full mission's success criterion is NOT MET.**
