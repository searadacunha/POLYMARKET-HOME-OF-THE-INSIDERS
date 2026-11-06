# Iran cluster E: the Privacy Cash withdrawal to the Bybit deposit proved the root created by the beneficiary's 12.33 SOL deposit

Date: 6 November 2026. Follow-up to `../iran-privacy-cash-sequence-2026-11-06/` (section 1, "the decisive question stays open"). That note and the earlier ones are unchanged. The tools come from PR 28 (`research_notes/github-tooling-audit-2026-11-06/`, section 4.6, commit `f8033d7`) and are copied into `scripts/`.

Every figure is recomputed offline by `verify.py` from this folder and `../iran-solana-beneficiary-2026-11-05/evidence/`: `python3 -I -B verify.py` (last run 14 of 14, `verification.json`).

## 1. Question

On 28 February 2026, the beneficiary `4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy` deposited 12.3288002 SOL into the Privacy Cash SOL pool at 14:54:50 UTC. At 14:55:19 the pool's next transaction withdrew 1 SOL (0.9905 to the recipient, 0.0095 fee) to `Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV`, the beneficiary's Bybit deposit address. Was the 12.33 SOL deposit even spendable by that withdrawal? If the withdrawal's proof used a Merkle root older than the deposit's insertion, it was not, and the two could be excluded from each other cryptographically.

## 2. Method

- The pool's tree is append-only, and every leaf appended pushes one root into a history of 100 (`merkle_tree.rs`, `append`). The deposit added leaves 346,814 and 346,815, so the roots that contain at least one of its two notes are R(346,815) and R(346,816). Every earlier root contains neither.
- R(n), the root of the tree holding leaves 0 to n-1, needs only the left siblings along the path of leaf n-1 and the zero values on the right. Left siblings are complete subtrees that never change again, so current Merkle paths of nearby leaves contain them. No rebuild of the 346,816 earlier leaves is needed.
- Current paths come from the pool's public relayer (`api3.privacycash.org/merkle/proofv2`). They are not trusted as such: each is used only because it folds to the root read **on chain**, at byte 880 of the tree account `6VVKJ44WTJGCksTGJHjf1kJWZaMf9Nswgj6w7Dtrw55D`, which is the first account of both transactions.
- Poseidon (BN254, circom parameters) is implemented with the standard library and matches the circomlib vector `poseidon([1, 2])`.

## 3. Results

| Check | Result |
|---|---|
| Relayer root against the chain | equal, `nextIndex` 890,520 on both sides |
| Current paths of leaves 346,805, 346,814, 346,815, 346,817 | all four fold to the on-chain root; changing one sibling breaks the fold |
| States whose root is computable from them | 13, from 346,752 to 346,818 |
| **12.33 SOL deposit** `5j3r5HzQ…` (positive control) | proved R(346,814), the latest root at that moment |
| **1 SOL withdrawal** `2kkJqk86…` to the Bybit deposit | proved **R(346,816)** |
| First deposit `3E3rDmYb…` (0.119 SOL) | proved a root older than every computable state |

R(346,814), R(346,815) and R(346,816) are three different values.

## 4. What this establishes

- **No cryptographic exclusion.** The withdrawal's tree contained both notes of the 12.33 SOL deposit, so the deposit was spendable by it. The hypothesis "the root predates the deposit" is refuted.
- **The withdrawal's proof was built on the tree state created by the deposit.** R(346,816) came into existence with the deposit at 14:54:50 and was the latest root until the withdrawal 29 seconds later. So the withdrawal's proof inputs were fetched after the deposit landed.

What it does not establish:
- **It is not a link.** The proof hides which note it spends. Any unspent note of at least 1 SOL in the tree, which held 346,816 notes, was equally spendable, and a client that fetches the latest root behaves this way whatever note it spends.
- No amount, change note or nullifier ties the withdrawal to the deposit. The change of a 12.33 SOL note spent for 1 SOL would be an encrypted output, which this method cannot read.

## 5. Classification

| Relation | Level |
|---|---|
| Privacy Cash withdrawal → Bybit deposit `Agnhk1Vs…`, relative to the beneficiary's 12.33 SOL deposit | Supported temporal relation (next pool transaction, 29 s), now **cryptographically compatible**: the deposit's notes were in the tree the withdrawal proved. Not a matched deposit |
| Cryptographic exclusion of that pair | Refuted |
| Common control, coordination, inside information | Unchanged: not demonstrated |

## 6. Limits

- The relayer is an off-chain service run by the pool's operators. Its paths are checked against the on-chain root and its root against the chain; nothing else from it is used.
- The on-chain root was read on 6 November 2026 (slot in `verification.json`); the historical roots are derived, not read from a February snapshot, which no RPC serves.
- The deposit's first root (0.119 SOL) and other states between 346,700 and 346,818 are not computable from these four paths. They are not needed for the question.

## 7. Reproduction

- `verify.py`: offline, 14 checks.
- `scripts/poseidon.py`, `scripts/privacy_cash_roots.py`: offline self-checks (`python3 -I -B scripts/privacy_cash_roots.py`).
- `evidence/privacy_cash_roots/`: `merkle/root` and two `merkle/proofv2` responses (two commitments per request at most), and `getMultipleAccounts` from `api.mainnet-beta.solana.com`, keyless, 6 November 2026, each with its SHA-256.
