# ballon-dor-flow-trace: funding and cash-outs of the 11 Ballon d'Or 2026 accounts

Historical on-chain investigation, data read on November 2, 2026. An address is not a person. These accounts are subjects of investigation, not demonstrated insiders.

## Objective

Answer four questions for each account: where the money came from, which intermediaries it went through, where it went afterward, and whether there are common funders or destinations beyond shared services.

## Summary

- **New link:** the brace227 key funds, in almost equal shares, another Polymarket wallet, `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5`, not named by the press to my knowledge, which bought only Kane Yes. A financial link is demonstrated, a common owner is not.
- **Pairs:** 1 direct transfer out of 55 (brace227 to kraben006, 0.00205 ETH), no other shared personal address.
- **Origin:** more than half of the $304,137.63 in deposits comes from addresses labeled KuCoin Hot Wallet 2 and Binance.
- **Intermediaries:** Relay on every deposit and withdrawal. No labeled mixer, no sign of XMR.
- **Exits:** about 74% of the $493,094.76 withdrawn was still on its first address, or had returned to it, on November 2. No common final destination.
- **Not demonstrated:** common owner, coordination, inside information.

## Where to read

| File | Content |
|---|---|
| `FINDINGS.md` | Graded conclusions, negatives included |
| `EVIDENCE.md` | Transactions, files and hashes to check yourself |
| `STATUS.md` | Actual state and limits |
| `sources/README.md` | Method and detailed evidence levels |
| `sources/reports/FUNDING_FORENSICS_FINAL.md` | The 11 case files, the comparative summary, the link matrix |
| `sources/reports/COMMON_FUNDERS.md` | Common funders, 55 pairs, control accounts |
| `sources/reports/EXCHANGE_AND_PRIVACY_EXPOSURE.md` | Services touched, XMR |
| `sources/reports/CASHOUT_PATHS.md` | Withdrawal destinations |
| `sources/reports/UNKNOWN_PATHS.md` | Traceability breaks |
| `sources/data/`, `sources/graphs/` | Hop-by-hop paths, attributions, GraphML graphs |
| `sources/state/` | Intermediate results, without the HTTP cache |
| `sources/tools/`, `sources/tests/` | Original code and checks |

## Method

Budgeted walk upstream and downstream through personal-size addresses only: native, internal and ERC-20 transfers, Solana with its token accounts. A cross-chain link rests on the protocol's registry, never on a similar amount. A mint, a burn or an exchange return made by the address itself never counts as funding. The detail is in `sources/README.md`.

## Reproduce

`sources/` keeps the original directory layout. To rerun, see the "Reproduire" section of `sources/README.md`, and:

1. Download the label lists: `sources/evidence/labels/SOURCES.md`.
2. Provide a free Etherscan key in `ETHERSCAN_API_KEY`.
3. Create `~/Projects/PolySentinel-investigation/`, whose scripts read the original directories.

Without the HTTP cache, a rerun queries the sources at a different date. The Relay v2 route disappears on November 24, 2026: its responses are in `sources/evidence/relay/`.
