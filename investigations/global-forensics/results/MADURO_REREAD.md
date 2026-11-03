# Maduro and Iran file: every edge read again from nodes

Read on 2026-11-03. Tool: `engine/tools/verify_maduro.py`. Output: `results/maduro_iran/edge_verification.csv`, one line per edge, and `results/maduro_iran/summary.json`. Input: the 571 edges of `phase2/TABLE1_graph.csv`, all marked `PROVEN` in the September archive. A row that differs stays in the output.

| Result | Edges | What it means |
|---|---:|---|
| `AGREES` | 467 | The transaction shows this move, same parties and amount. 313 read from two node hosts, `REVERIFIED`. 154 on Tron, read from TronGrid only, so one host, `ONCHAIN_CONFIRMED` |
| `CROSSCHAIN_SAME_ID` | 80 | Both sides read, and the same Relay id is on both chains, without the API |
| `CROSSCHAIN_BOTH_SIDES_READ` | 13 | Both sides read. The id test cannot run on Tron here, so the two sides are tied only by the archive's pairing |
| `CROSSCHAIN_ID_ABSENT` | 4 | Both sides read, and the id was not found where this reader looks. Four Solana rows, three of them deposits of `0x31a56e9e…` |
| `ONE_SIDE_READ` | 3 | Same-chain swaps with one hash in the archive. The move reaches the destination near the amount |
| `TX_EXISTS_CROSSCHAIN` | 3 | One hash in the archive for a cross-chain move: the transaction exists, the far side is not read |
| `NOT_READ_CHAIN` | 1 | A Bitcoin deposit: no reader here |

Nothing came back as contradicting a move in the table. Before this file, 64 of the 571 had been read again, and a first pass of this run showed 91 unread and 34 absent. That was a defect of the reader, corrected here: rows holding two hashes were read as one, and native TRX was looked for in logs, where it never appears.

## Accounts

The 12 accounts of `pnl_summary.csv`, rebuilt from the current `/v2/activity` and the cash of each market, all with complete histories: the largest difference is $3.41 on one account, the others are under one cent. The 8 accounts the archive calls its network total $509,989.83 rebuilt against $509,993.25 archived.

## Limits

- This confirms that moves happened, with these amounts. It does not confirm the archive's word `réseau`, nor any reading placed on an edge. A proved move is not a common owner.
- Tron rests on one host. Solana rests on `api.mainnet-beta` with a fallback.
- The 4 `CROSSCHAIN_ID_ABSENT` are not refuted links: a Solana deposit may carry the id in a form this reader does not decode. They stay at the archive's pairing, and the Relay record is kept in `results/links/relay_archive.json`, where it was found.
- `history_complete` is about Polymarket activity. It says nothing about funding on other chains.
