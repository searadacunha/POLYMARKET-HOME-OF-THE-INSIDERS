# Iran cluster E: erratum to the network note, and the Bybit EVM deposit address checked on USDT0

Date: 6 November 2026. Concerns `../iran-cluster-e-network-2026-11-05/REPORT.md`, which is not rewritten. Both points were raised by an offline test of a third-party classifier in PR 28 (`research_notes/github-tooling-audit-2026-11-06/audit_notes/demixer_evaluation.md`) and checked here. `python3 -I -B verify.py` recomputes them offline (7 of 7, `verification.json`).

## 1. Erratum: the behaviour checks use labels

Section 2 of the network note says: "The behaviour (gas from the exchange's funder, full sweeps to the exchange) is checked by `verify.py` independently of the labels." That is not exact. The checks for the Binance and Bybit deposit addresses also require the Blockscout tags of the gas funder ("Binance: Deposit Funder", "Bybit: Deposit Funder") and of every sweep recipient. What `verify.py` checks without labels is the shape of the behaviour: gas from one funder, full forwarding of every inflow. The names of the exchanges rest on one label source, Blockscout metadata.

Read instead: "The behaviour (a single gas funder, every inflow forwarded in full) is checked by `verify.py`; the identity of the funder and of the sweep recipients rests on the Blockscout labels."

No classification changes.

## 2. The Bybit deposit address also forwards USDT0, to Bybit

The network note and its check read only USDC and USDC.e outflows of `0x93b7e169b93ece646d08cedbb8fa505796a5b96b`. Its archived token history (same Etherscan page, PR 27) also holds three USDT0 outflows:

| Recipient | USDT0 | Blockscout label (metadata service, 6 Nov 2026) |
|---|---|---|
| `0xf89d7b9c864f589bbf53a82105107622b35eaa40` | 1,000.999999 | Bybit 5, Bybit: Hot Wallet |
| `0xa85c29b94f8a22a7268facee89ef4eca051be2ce` | 3,466.798977 (27 Oct 2026) | Bybit: Wallet 131 |
| `0x1347378b1d0eb69d3462e09b3dfa2fe28ebe74ec` | 700.699999 | Bybit: Wallet 130 |

Every non-zero outflow of a real stablecoin (USDC and USDT0) goes to an address labelled Bybit. The two other outgoing rows are look-alike tokens of an address-poisoning attempt. The classification "Bybit customer deposit address (EVM)" holds and now covers USDT0.

## 3. Reproduction

- `evidence/bs_meta_137.json`: Blockscout metadata for the three USDT0 recipients, with its SHA-256.
- `verify.py`: reads that file, the network note's archived Etherscan page and its Blockscout files, and the network note's `REPORT.md` and `verify.py` for the wording.
