# Where the Nobel funder's treasury went

Read on 19 and 20 November 2026 from public, keyless sources. An address is not a person. This note follows token movements; it attributes no identity, no common ownership and no inside information.

## What this note adds

[`investigations/followup-20261113`](../../investigations/followup-20261113/FINDINGS.md) shows that one key funded eight fresh Polymarket accounts with 372,521.54 USDC on 9 and 10 October 2025 (Nobel Peace Prize market) and received their withdrawals. It leaves one item under "Missing to conclude": where the treasury `0xB282B48ae713Fa2201282E298F3393130c4F851d` sent the 330,020.96 USDC it moved to the Relay depository on 15 April 2026.

This note answers that item transaction by transaction, and says where the answer stops.

## Result

1. On 15 April 2026 the treasury paid 330,025.963260 USDC to the Relay depository on Polygon in three orders (330,020.963260 in the two main orders, the figure in the followup, plus a 5.000000 USDC test order) and received 329,426.024331 USDT on Ethereum at the same address. Both legs of each order are confirmed by receipts.
2. The same day and the next it converted all its USDC and ETH except 0.000471 ETH: 39,983.213328 USDC into 39,611.487618 USDT, and 6.945045 ETH into 16,046.604562 MUSD, then into 15,898.082270 USDT.
3. On 16 April 2026, between 23:02:59 and 23:11:47 UTC, it sent its whole balance, 384,936.596888 USDT, to one address, `0x0D40D7Cb8e1245C2AefDe329375ed2D09377dcC1`, in three transfers that it signed itself. It keeps 0.004 USDT and 0.000471 ETH.
4. Six minutes later that address sent 370,000 USDT to `0x15fF50f3915e0F8410A8b1C0055FCcE706dE3C93`, which forwarded 413,600 USDT to two further addresses within 1 hour 52 minutes. Between 369,650.523377 and 370,000 of the 370,000 is the treasury's money under any accounting convention.
5. From the third hop on, the followed value sits in wallets that receive from 12 to 70 senders above 1 USDT each, among them tagged exchange hot wallets. No address downstream of the treasury on the path carries a public tag (the seed legs come from the tagged Relay solver and MetaMask Swaps spender). Attribution stops there: beyond that point the amount that can be called the treasury's depends on a convention, not on a fact.

All 48 followed transfers are confirmed by transaction receipt on two independent JSON-RPC endpoints. The package is reproduced byte for byte from the saved pages by [`verify.py`](verify.py), without network access, which also asserts every figure of this note.

## 1. Liquidation of the treasury

Relay orders of the treasury on 15 April 2026 (request records archived on 19 November 2026, each leg re-read as a receipt on two endpoints per chain, [`relay/relay_check.csv`](relay/relay_check.csv)):

| Created (UTC) | Paid on Polygon, USDC | Delivered on Ethereum, USDT | Payment transaction | Delivery transaction |
|---|---:|---:|---|---|
| 04:09:06 | 5.000000 | 4.932147 | `0xb51c9ed9fcb0017a43629ea8d82b391af5ff7e0a3d8618603e54fd157ef9321c` | `0xe64a50e17cb809c929eb132fb704316fb6e96c41bfa6d28cd7099876174efff6` |
| 04:12:31 | 165,093.028144 | 164,792.106149 | `0xc281ab93f8ee3eb3c3a43a359d5af55ce129a3588626ecc2f27859bfb1dae400` | `0x621e5f52422e4a07af3225b3790fd49db834e80ad8ff84d7612bdce5fc196360` |
| 04:17:08 | 164,927.935116 | 164,628.986035 | `0x2a3c278f22a155c8f1146fbc83aec3b6ceee6ad50f13b2cf958199137a86f9f3` | `0x09a2e20d83ba5d615e6acee7a7ee19f4c02a2379e172c9ea479972c1cdb4c283` |
| Total | 330,025.963260 | 329,426.024331 | | |

The payments go from the treasury to the Relay depository `0x4cd00e387622c35bddb9b4c962c136462338bc31`; the deliveries come from the Relay solver `0xf70da97812cb96acdf810712aa562db8dfa3dbef` to the treasury itself. The difference, 599.938929, is the cost of the three orders (0.18 %). A fourth order at 03:55:49 bridged 0.002339 ETH into 65.04 POL to pay Polygon gas; its origin leg is confirmed, its destination leg is a native-coin payment made inside a contract call and is not checked by this method.

Other conversions of the treasury ([`native/summary.json`](native/summary.json), public indexer):

| Time (UTC) | Paid | Received | Transaction |
|---|---|---|---|
| 2026-04-15 04:45:35 | 39,983.213328 USDC | 39,611.487618 USDT | `0xd55b7273d43b58965b19928d4a8dffb38b71f1d233acb8f412134cd7aaab5d4e` |
| 2026-04-15 04:47:47 | 6.945045 ETH | 16,046.604562 MUSD | `0x9db96bdea5c28cf8024fb738bc17e0b633bc1f6576beb0ac45234afb1660b6af` |
| 2026-04-16 23:06:59 | 16,046.604562 MUSD | 15,898.082270 USDT | `0x4a5b521a8023b6fded3647bcada55da85e8a53746b995bccac9502eb83db20f7` |

On 10 October 2025 the funder sent the treasury 39,983.213228 USDC and 6.950374 ETH (already published in [`FOLLOWUP_REPORT.md`](../../investigations/followup-20261113/sources/reports/FOLLOWUP_REPORT.md)). The conversion paid 39,983.213328 USDC, 0.000100 more than that inflow; the pages saved here (the USDT ledger and the native history) do not show where the extra 0.000100 USDC came from. The five USDT inflows above total 384,935.594219 and are the seed of the walk.

Reconciliation of the treasury's official USDT: 384,936.600888 in, 384,936.596888 out, 0.004000 left. The inflows that are not seed are one bait of 1.000000 USDT (below) and dust.

## 2. One recipient, three transfers

| Time (UTC), 16 April 2026 | USDT | Transaction | Block |
|---|---:|---|---:|
| 23:02:59 | 1.000000 | `0xe3f4e53f2c99d287a93e9191c9a898d0bd06026a00f2289c02c2ddf35491bc9b` | 24895557 |
| 23:05:23 | 369,000.000000 | `0x2bdde555dcf842e46bd6ce257ddeb1fc5acb0a0a929c42d7fec9f671a602984a` | 24895569 |
| 23:11:47 | 15,935.596888 | `0x255d7864517292fa778e448f42a4acffd4b49f12f2abf5d37a3c5e4aeab97f18` | 24895601 |

One dollar, then the balance: consistent with a test transfer before the balance. Ninety-six seconds after the 1 USDT transfer, at 23:04:35, a look-alike address (`0x0D4015AdBA202C7bc0cb56CD7B2C10511A90DcC1`, same first and last characters as the recipient) sent the treasury 1.000000 USDT of the official contract, a pattern of address-poisoning bait copying the test. The bait transfer is read from the indexer, not from a receipt. The 369,000 USDT transfer, 48 seconds later, went to the same recipient as the 1 USDT transfer, not to the look-alike. The walk finds three look-alike addresses of the recipient among the treasury's counterparties; a tracer that matches addresses on their first and last characters would have followed the wrong wallet.

## 3. What can be followed, and under which convention

Tokens are fungible. Once followed funds enter a wallet that holds other funds, the share of each outgoing transfer that "is" the followed money is a convention. The walk therefore values every transfer twice: "others first" (the wallet spends its other funds first, the lowest-intermediate-balance reading) and "followed first" (it spends the followed funds first). Where the two agree, any convention gives the same answer.

| Hop | Time (UTC) | From | To | USDT | Others first | Followed first |
|---:|---|---|---|---:|---:|---:|
| 1 | 16 Apr 23:02 to 23:11 | treasury | `0x0D40D7Cb...dcC1` | 384,936.596888 | 384,935.594219 | 384,935.594219 |
| 2 | 16 Apr 23:17:59 | `0x0D40D7Cb...dcC1` | `0x15fF50f3...3C93` | 370,000.000000 | 369,650.523377 | 370,000.000000 |
| 2 | 17 Apr 15:50:35 | `0x0D40D7Cb...dcC1` | `0x3D266394...0322` | 20,000.000000 | 12,285.380131 | 14,935.594219 |
| 3 | 16 Apr 23:59:23 | `0x15fF50f3...3C93` | `0x710CbbF2...1749` | 139,300.000000 | 95,349.898491 | 139,300.000000 |
| 3 | 17 Apr 00:19:23 | `0x15fF50f3...3C93` | `0x919BE421...0769` | 173,652.000000 | 173,651.992570 | 173,652.000000 |
| 3 | 17 Apr 00:56:59 | `0x15fF50f3...3C93` | `0x919BE421...0769` | 34,783.000000 | 34,782.990313 | 34,783.000000 |
| 3 | 17 Apr 01:10:11 | `0x15fF50f3...3C93` | `0x919BE421...0769` | 65,865.000000 | 65,864.992983 | 22,265.000000 |

Full addresses, transaction hashes, blocks and the 48 rows are in [`case/path.csv`](case/path.csv).

Reading:

- Hop 1 is exact. The treasury had no other USDT, so all 384,935.594219 of seed reaches the recipient whatever the convention (the 1.002669 difference with the amount sent is the bait and dust).
- Hop 2: the recipient held 348.473326 USDT of its own when the funds arrived. Of the 370,000 it forwarded six minutes later, at least 369,650.523377 is the treasury's. Under followed-first the remainder, 14,935.594219, left the next day inside a 20,000 USDT payment to `0x3D266394f4073959a6689C7bE58C88635B570322`; under others-first 12,285.380131 did, and the rest, 2,999.690711, left in eight payments below 10,000 USDT between 19 April and 18 June 2026.
- Hop 3: within 1 hour 52 minutes `0x15fF50f3...3C93` sent out 413,600 USDT, more than it had received from the recipient, because it also held funds from other senders. Two transfers (173,652 and 34,783) are followed money under both conventions. For the other two the conventions part: between 95,349.898491 and 139,300 of the first, between 22,265 and 65,864.992983 of the last.
- Beyond hop 3 the two conventions give unrelated answers (for the first 100,000 USDT that `0x710CbbF2...1749` sent on, zero under one and 100,000 under the other). The walk stops being evidence there.

## 4. What the wallets are, and are not

Figures are official-USDT ledgers read to their first transfer ([`case/nodes.json`](case/nodes.json)).

| Address | Role here | Transfers | Senders above 1 USDT | Recipients | USDT in | Active |
|---|---|---:|---:|---:|---:|---|
| `0xB282B48a...851d` | treasury | 19 | 2 | 1 | 384,936.60 | 15 to 23 Apr 2026 |
| `0x0D40D7Cb...dcC1` | recipient | 222 | 6 | 25 | 598,854.50 | 3 Apr to 21 Oct 2026 |
| `0x15fF50f3...3C93` | hop 2 | 644 | 13 | 14 | 1,424,898.59 | 28 Feb to 3 May 2026 |
| `0x3D266394...0322` | hop 2 | 895 | 42 | 21 | 3,573,288.98 | 9 Oct 2025 to 21 May 2026 |
| `0x919BE421...0769` | hop 3 | 191 | 12 | 22 | 1,183,722.75 | 3 Mar to 10 Jul 2026 |
| `0x710CbbF2...1749` | hop 3 | 3,281 | 70 | 14 | 4,285,814.63 | 28 Jan to 1 May 2026 |
| `0xa25Ffd06...cc29` | hop 3 | 544 | 23 | 20 | 2,267,642.85 | 10 Dec 2025 to 9 Nov 2026 |

Observations, each from the saved pages:

- **No public tag downstream of the treasury.** None of the seven wallets, and none of the addresses where followed value ends, carries a public tag on the indexer. The only tagged addresses on the path are the two senders of the seed legs, the Relay solver and the MetaMask Swaps spender ([`case/labels.json`](case/labels.json) lists every tagged address met).
- **The downstream wallets have many senders.** Tagged senders into them include Coinbase 10 (443,945.72 USDT), Binance 14 (160,076.57), Binance 15 (157,814.70), FixedFloat (41,886.85) and MEXC 21 (7,518.28). Exchange hot wallets are among their senders. This pattern fits a service (an over-the-counter desk, a payment processor, a merchant); the transfers do not show which, nor who withdrew from those exchanges (E-5, hypothesis).
- **They pay one another.** `0x3D266394...0322` sent 377,457 USDT to `0x15fF50f3...3C93` and 482,065 to `0x919BE421...0769`; `0x15fF50f3...3C93` sent 495,996 to `0xa25Ffd06...cc29`, 299,681.611334 to `0x919BE421...0769` and 173,130 to `0x710CbbF2...1749`; `0x919BE421...0769` sent 282,500.008387 to `0xa25Ffd06...cc29`; `0xa25Ffd06...cc29` sent 980,617.069024 to `0x710CbbF2...1749`, which sent 2,722,000 to one untagged address. `0x15fF50f3...3C93` also paid the first gas of `0x919BE421...0769`.
- **The recipient transacted with that group from its first transaction.** Its first native coin, 0.22 ETH, came from `0x3D266394...0322` on 5 April 2026 at 17:07:59; 1 hour 41 minutes later it paid that address 52,005 USDT. It paid wallets of the same group again on 16 and 17 April (the transfers followed above).
- **The recipient is an active account, not a single-use pipe.** It is a plain key delegated under EIP-7702 to `0x63c0c19a282a1B52b07dD5a65b58948A07DAE32B` (the indexer names it EIP7702StatelessDeleGator), with 598 transactions between 5 April and 17 November 2026. Its USDT comes from the treasury (64 %), from a Rhino.fi bridge contract (85,441.00), from a Chainflip vault (82,615.60) and others; it also received 7.65 ETH from a hot wallet tagged Gemini 9 on 11 November 2026.

## 5. Levels of evidence

| Id | Statement | Level | Rung |
|---|---|---|---|
| E-1 | The treasury paid 330,025.963260 USDC to the Relay depository and received 329,426.024331 USDT on Ethereum, in three orders | CONFIRMED (Relay records, receipts on two endpoints per chain) | 1, direct transactions |
| E-2 | The treasury converted all its USDC and ETH except 0.000471 ETH into USDT and sent 384,936.596888 USDT to `0x0D40D7Cb...dcC1` on 16 April 2026 | CONFIRMED (receipts; the treasury signed) | 1 |
| E-3 | At least 369,650.523377 of the 370,000 USDT forwarded six minutes later is the treasury's money | CONFIRMED (ledger of the recipient from one indexer, read to its first transfer and not overdrawn; both conventions) | 1 |
| E-4 | The funds entered a group of wallets that pay one another and receive from 12 to 70 senders above 1 USDT each | SUPPORTED (ledgers, gas funding, tagged senders; one indexer) | 2, corroborated financial relationship |
| E-5 | That group is a service used by third parties | HYPOTHESIS (behaviour only, no label) | 4 |
| E-6 | The recipient is controlled by the funder | UNRESOLVED | 5 |

Strongest alternative for E-6, in both directions. For the same owner: a 1 USDT transfer, then the whole balance, to one address. For a third party: the recipient has five senders above 1 USDT besides the treasury and transacted with the group eleven days before the treasury's transfers, which would also fit an agent or broker who forwards for others. Nothing here separates the two.

## 6. Checked and not retained

- **Other contact with the Nobel keys.** In the ledgers of the seven wallets the treasury appears only in the transfers above; the funder `0xE206961002FEeBd9EDb152EEd9B630a351874043` and its source `0x3e2c6d068fc6958684e836998285e3a836dbd96f` do not appear at all.
- **A date coincidence.** The first USDT transfer of `0x3D266394...0322` is dated 9 October 2025 at 23:02:11 UTC, the night of the Nobel purchases. Its first native coin arrived two days earlier, on 7 October, and none of its USDT or native-coin counterparties before November 2025 is among the cross-case hits below. Recorded here so that it is not rediscovered as a finding.
- **Cross-case join.** Every address met was looked up in all files tracked on `main` at commit `0b0882c`, outside this folder, gzip files decompressed. Of the 1,230 addresses met, 23 are cited elsewhere in the repository ([`data/cross_case_hits.csv`](data/cross_case_hits.csv), with the folders that cite each one): 16 carry a public tag (exchanges, bridges, routers), one is the treasury, and six are untagged. One untagged hit, the terminal `0x6d988d1233c72ce43b1e344314cbd736ba60509c`, is cited in `investigations/changenow-polymarket`. The join finds citations, not links: this note does not review what role these addresses play in the folders that cite them.

## 7. What is not shown

- Who controls the recipient, the downstream wallets or the address that received 2,722,000 USDT.
- What the downstream group of wallets is. An exchange that received a withdrawal to the recipient (the hot wallet tagged Gemini 9) holds records that this note cannot reach.
- Anything about the information the funder had in October 2025. Moving funds through an untagged group of wallets six months later is ordinary behaviour for many holders and proves nothing about the trades.
- Native coin and other tokens beyond what `native/summary.json` lists. The walk follows one token on one chain.

## 8. Reproduce

```sh
# offline, network blocked, 52 named checks: integrity (manifests and SHA256SUMS), byte-for-byte reproduction,
# counts, every figure of this note, the cross-case file, and negative self-tests on a corrupted copy
python3 -I research_notes/nobel-funder-exit-2026-11-20/verify.py

# from the network (public, keyless): rebuild the walk, then confirm it by receipts
mkdir /tmp/new-case && cp research_notes/nobel-funder-exit-2026-11-20/case/case.json /tmp/new-case/
python3 integrations/forensic-intelligence/value_trace.py walk /tmp/new-case
python3 integrations/forensic-intelligence/value_trace.py replay /tmp/new-case
```

Tools: [`integrations/forensic-intelligence/value_trace.py`](../../integrations/forensic-intelligence/value_trace.py) (walk, replay, check), [`integrations/forensic-intelligence/relay_check.py`](../../integrations/forensic-intelligence/relay_check.py) (Relay records against receipts), [`native_history.py`](native_history.py) (native coin and account type).

## 9. Limits

- Ledgers come from one indexer (Blockscout). Receipts on two JSON-RPC endpoints confirm the 48 followed transfers and the Relay legs; they do not prove that a ledger is complete. A missing inflow that funds a later outflow would show as an overdrawn wallet, and none is. The bait transfer and the wallet table come from the indexer only.
- [`SHA256SUMS`](SHA256SUMS) gives the file-level SHA-256 of every data file and stored `.gz` page; each `manifest.jsonl` gives the SHA-256 of the decompressed response. The cross-case join was computed once at commit `0b0882c`; `verify.py` checks the saved file against the walk, not against later commits.
- The Relay request records were read on 19 November 2026; the API that serves them is announced to retire on 24 November 2026. The saved page and the receipts keep the three orders verifiable after that date.
- Public tags are the indexer's. An untagged address is not thereby a private person, and a tagged one is named on a single source.
- The two conventions bound what one wallet can attribute; they are not a statement about what its holder intended.
