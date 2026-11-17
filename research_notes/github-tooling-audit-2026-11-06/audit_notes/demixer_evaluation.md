# Offline test of the deposit-address classifier of prettydeath/TornadoCash-demixer

Date: 6 November 2026. Commit `cc30ba7c19f990d7a055614a9f80500adac9c307` (29 Oct 2026), MIT (`LICENSE`, "Copyright (c) 2026 tornado-demix contributors"). The third-party code was read only, never imported or run. `../scripts/demixer_eval.py` is an own re-implementation from that reading (standard library, `python3 -I -B demixer_eval.py <iran-cluster-e-network note> <iran-solana-beneficiary note>`, both on the PR 27 branch); its output is `../results/demixer_eval.json`. Written by a sub-agent; the one new fact it raised was checked by the main session (section 4).

## 1. What the classifier computes (`tornado_demix/deposit_addresses.py:104-168`)

- A candidate X is rejected if it has contract code (`eth_getCode != "0x"`, `rpc.py:133-149`), if page 1 of its `txlist` holds 1,000 rows, or if it has more than 50 distinct senders over `txlist` + `tokentx`.
- Among X's 3 most frequent outgoing destinations, a destination is a hot wallet if it is labelled as an exchange, or if it is unlabelled, not a contract, has at least 10,000 transactions, and X "forwards" to it: an outflow 0 to 3,200 blocks after one inflow of the same asset, at least 99 % of it (`:70-101`).
- X is a deposit address when hot wallets take at least 80 % of its outgoing **rows**; it is scored only when labelled exchange wallets alone take 80 %.
- It feeds a linking signal (`shared_deposit_hits`, weight 0.40). The repository's accuracy figures are for that link, not for the label. In its own second pre-registered hold-out, the labelled link was not supported at 30 days on Ethereum (R 1.77, 0.16 to 3.91, `docs/HOLDOUT2_RESULTS.md:27`).

## 2. Result on 9 Polygon addresses of PR 27 and one BSC hot wallet

| Class in PR 27 | n | As written: scored / context / not | Adapted to Polygon tokens: scored / context / not |
|---|---|---|---|
| exchange customer deposit (Binance, Crypto.com, Bybit) | 3 | 0 / 0 / 3 | 3 / 0 / 0, same exchanges as PR 27 |
| other per-customer address (EIP-7702 wallet, Relay and pUSD forwarders) | 4 | 0 / 0 / 4 | 0 / 1 / 3 |
| unlabelled | 2 | 0 / 0 / 2 | 0 / 0 / 2 |
| service (`0xef3aeff9`, BSC, nonce only) | 1 | not | not |

Why the rule as written fails on Polygon:
- A token sweep from an EOA appears twice: as a `txlist` row to the token contract and as the `tokentx` row to the hot wallet. Counting rows, the token contract becomes a top destination (one call row per sweep on 9/9, 26/26 and 24/24 sweeps measured).
- Address-poisoning rows (zero-value and fake-token transfers) count as outgoing rows and push the real hot wallet out of the top 3.
- An EIP-7702 delegated EOA has code, so it is rejected as a contract.
- 3,200 blocks is about 1.8 h on Polygon; aggregated sweeps fail its one-to-one forwarding test.

The adapted variant (zero-value, fake-token and call rows dropped; EIP-7702 treated as an EOA) recovers the three exchange deposit addresses, but only through the same Blockscout labels PR 27 already uses. No known service was scored in any variant; with contract status unknown, the Relay Depository and the pUSD contract were taken for hot wallets three times.

## 3. Decision

**Rejected as a method, kept as a reference.** It adds no evidence independent of labels, it rejects EIP-7702 wallets, and it has no category for Relay or Polymarket per-account forwarders. Its written definition of forwarding and its decoy-window design (target windows against windows moved before the first deposit) are worth keeping as references. Ten addresses chosen after the fact, with one label source, are not a validation.

## 4. Points raised for our own rules, checked

- **USDT0 outflows of the Bybit deposit address `0x93b7e169…`.** PR 27's check reads only USDC and USDC.e. The address also sent USDT0: 1,000.999999 to `0xf89d7b9c…`, 3,466.798977 to `0xa85c29b9…` (27 Oct 2026) and 700.699999 to `0x1347378b…`. Blockscout metadata (`../evidence/usdt0_followup/`, 6 November 2026) labels them **Bybit: Hot Wallet**, **Bybit: Wallet 131** and **Bybit: Wallet 130**. So every outflow still goes to Bybit, the classification of PR 27 holds and extends to USDT0. (A first reading reported no tags: the service keys its answer by checksummed address.)
- **Wording in PR 27.** `iran-cluster-e-network-2026-11-05/REPORT.md`, section 2, says the behaviour is checked by `verify.py` "independently of the labels". Checks 4 and the Bybit check also require the funder and sink tags. Only the full-forward part uses no label, and it holds for 8 of these 9 addresses, so on its own it separates little. Corrected by an erratum in PR 27, not by rewriting that report.
