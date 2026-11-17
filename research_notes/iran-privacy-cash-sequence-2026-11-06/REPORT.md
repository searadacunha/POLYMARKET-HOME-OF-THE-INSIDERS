# Iran cluster E: the Privacy Cash withdrawal is the pool's next transaction after the beneficiary's deposit, and the Relay links hold without the Relay API

Date: 6 November 2026. Follow-up to `../iran-solana-beneficiary-2026-11-05/` (sections N3 and 5). That note and its evidence are unchanged. The decoders come from the tooling audit of PR 28 (`research_notes/github-tooling-audit-2026-11-06/` on branch `research/github-forensic-tooling-20261106`), copied into `scripts/`.

Every figure is recomputed offline by `verify.py` from this folder and the previous note's `evidence/`: `python3 -I verify.py` (last run 19 of 19, `verification.json`).

## 1. The pool's sequence around the 1 SOL withdrawal

Each Privacy Cash `transact` appends exactly two notes to the SOL pool's Merkle tree and logs their positions in two `CommitmentData` events (`anchor/programs/zkcash/src/lib.rs`, lines 346 to 364 at `f79b82f`). The decoder reads every field of the instruction and refuses one whose bytes are not consumed exactly. It also checks that the events repeat the proof's output commitments.

| UTC, 28 Feb 2026 | Transaction | `ext_amount` (lamports) | Tree positions |
|---|---|---|---|
| 14:50:06 | beneficiary deposit `3E3rDmYbGgUy5mKg3ijjXL2Engay6ZsFSA4GLVSsEwj4mgcBp31PYMEJgDGnzkN5SG66pVNmbqBbgaLr8UKKPbAg` | +119,021,900 | 346,804 and 346,805 |
| 14:54:50 | beneficiary deposit `5j3r5HzQm794uR9G6yji43XZj4rhP2SuyTkEfNrB4nZ7DHLfyWp6aWxqSQ1RwyuAnajcyzimie2niDPHEPnrDGJ8` | +12,328,800,200 | 346,814 and 346,815 |
| 14:55:19 | withdrawal to the Bybit deposit address `2kkJqk86KfZ1bmMqxEAMpndtSTAFyBQRp4dNy5vQryHWiKtdXJWoMp8biX2VXmyrtWzHTUQDpSbJouiMWp6y9pdh` | −990,500,000, fee 9,500,000 | 346,816 and 346,817 |

What this adds:
- **No other SOL-pool transaction ran between the beneficiary's 12.33 SOL deposit and the withdrawal to `Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV`.** The withdrawal's positions follow the deposit's directly.
- Four other pool transactions ran between the beneficiary's two deposits.
- The three proofs reference three different Merkle roots.

What it does not establish:
- **It is not a cryptographic link.** The withdrawal may spend any unspent note of 1 SOL or more in the tree, which then held 346,816 notes, and its proof hides which one.
- Order in the tree is a temporal fact. So the relation of N3 stays a supported one, now narrower in time: nobody else used the pool in those 29 seconds.
- **The decisive question stays open: was the 12.33 SOL note spendable by this withdrawal?** That is whether its root is the one produced by inserting positions 346,814 and 346,815. Answering it requires rebuilding the Poseidon tree from the 346,816 earlier commitments, which was not done. If the root is older than that insertion, the withdrawal cannot spend the beneficiary's 12.33 SOL deposit.

## 2. The Privacy Cash code that ran on 28 February

- The program's `programdata` account was written at slot 399,466,617 (11 February 2026, 04:11:16 UTC), then at slot 427,378,345 (18 June 2026). Nothing was written in between. The bytecode that executed the three transactions is therefore the one deployed on 11 February.
- The closest earlier commit touching the program is `0bd1889` (10 February, "Support jlUSDC and jlWSOL"). Between it and the current head `f79b82f`, the only program source file that changed is `lib.rs`, by 6 lines added and 4 removed.
- Those lines are the list of allowed SPL tokens, read at blobs `f2b5cec` and `455f4a6`. `transact`, `Proof`, `ExtData` and `CommitmentData` are unchanged. This part is a reading of the source; the source is BSL-licensed and is not copied here.
- The link between `0bd1889` and the deployed bytecode is inferred from dates, not from a verifiable build. The direct evidence that the layout applies is that all three February instructions decode byte for byte: 694, 696 and 695 bytes consumed out of 694, 696 and 695.

## 3. The eleven Relay links without the Relay API

The Relay Depository on Polygon (`0x4cd00e387622c35bddb9b4c962c136462338bc31`) emits `RelayErc20Deposit(address from, address token, uint256 amount, bytes32 id)` (topic `0x49fed1d0…55e1`). Each of the 11 orders to `4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy` carries in that log the `id` that the Solana payment carries as its memo.

Joining the archived receipts and the beneficiary's history on that `id` alone gives:
- the 11 orders, with the four proxy wallets as depositors;
- 70,065.262869 USDC.e and 856.840698827 SOL;
- no Relay payment to the beneficiary without an origin.

Each link is therefore proven by two on-chain records, with no dependence on `api.relay.link`, whose `requests/v2` endpoint is retired on 24 November 2026. The tooling note of PR 28 also found the 11 origins live from the Solana side only, through Polygon logs (43 keyless calls). The calldata tail and the API's request `id` are not this identifier.

## 4. Classification

| Relation | Level |
|---|---|
| Four accounts → beneficiary (11 Relay orders) | Unchanged (direct economic link through Relay), now confirmed from chain records alone |
| Privacy Cash withdrawal → Bybit deposit, relative to the beneficiary's deposit | Supported temporal relation: the next pool transaction. Not a matched deposit |
| Common control, coordination, inside information | Unchanged: not demonstrated |

## 5. Reproduction

- `scripts/privacy_cash.py`, `scripts/relay_onchain.py`, `scripts/keccak.py`: decoders, standard library only.
- `evidence/solana_program/`: `getAccountInfo` of the program and of its `programdata`, and `getSignaturesForAddress` of `programdata`, from `api.mainnet-beta.solana.com`, keyless, 6 November 2026.
- `evidence/github/`: GitHub API metadata for Privacy-Cash/privacy-cash (commit list of `lib.rs`, comparison `0bd1889...f79b82f`, blob identifiers), with the source text removed.
- `verify.py`: offline.
