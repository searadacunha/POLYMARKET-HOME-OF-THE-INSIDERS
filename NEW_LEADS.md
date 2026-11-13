# New leads, 13 November 2026

Leads found in this pass, strongest evidence first. Each one states what is verified, what is only a hypothesis, and
what would settle it. Data and scripts: [research_notes/early-detection-2026-11-13](research_notes/early-detection-2026-11-13/README.md).

An address is not a person. "Linked" means a transfer of funds was read on chain. It does not mean one owner, and it
never means private information.

Levels used: **fact** (read directly in public data), **correlation** (a measured statistical association),
**common control** (a hypothesis about who operates accounts), **compatible with an information advantage** (behaviour
that private information would explain, among other explanations). No lead reaches a legally established violation.

## NB-1. The first account of the C7 funder set the price itself

| | |
|---|---|
| Market | Will María Corina Machado win the Nobel Peace Prize in 2025? (`0x14a3dfeba8b22a32feb0f10763db68bc4d2abeb5bff90e9ae20de53793b35a1d`) |
| Wallets | `0xa430506774f9efaf39903ee7e0db1351f66891ca` (published as "6741"), owner key `0xe206961002feebd9edb152eed9b630a351874043` |
| Amounts | 16,879.50 USD bought by 23:00:15 UTC; 43,338.58 USD by the announcement; 65,840.84 shares held at 09:00 UTC |
| Period | 9 October 2025, 22:42:57 to 23:00:15 UTC, ten hours before the announcement |
| Pattern | Lonely ignition by an account with no history: one wallet, 97.3 % of the buying in the first fifteen minutes, on a market that had traded 1,082 USD in the three hours before; it paid 0.048, then 0.10, then left a resting order at 0.30 |
| Primary evidence | [Tape](research_notes/early-detection-2026-11-13/data/machado_tape_20251009T2000_20251010T0900.csv); first trade `0x591e4fe5e48a28eb58acbf4b69b3a7a8f2328ab27b9ada7c279d510ecedfd6e2`; funding 80 seconds earlier, `0xe4dd2102d6dd649611557415aa28457e792c5abaac963e5a6fbb7a3b6f3e2516` |
| Level | Fact for the trades and the funding. Compatible with an information advantage. Not proof of one |
| Other explanations | A deliberate attempt to move a thin market; a large punt on a rumour this audit cannot see; a bet placed for a third party |
| Statistical score | Class `LONELY_THIN` of the frozen study; see [PATTERN_RESEARCH.md](PATTERN_RESEARCH.md) for how often that class won elsewhere |
| Status | Verified. Replayed by the monitor: alert at 23:00:15 UTC, cluster seen from 00:50 UTC ([BACKTEST_RESULTS.md](BACKTEST_RESULTS.md)) |
| Next check | A sourced time for the first public mention of the result or of a leak, to measure the lead against something other than the announcement |

## NB-2. A second linked group: one established account and two accounts opened that morning

| | |
|---|---|
| Market | Same |
| Wallets | A `0x5a8e6f7f4ef52b1c1e29969c85d2f523e7c3f55f` (owner key `0x09f0044450e09675ff895e5011443fd1ae3518e7`); B `0x870f371bf3affc9c6f100288887399e8e66ce372` (owner key `0xf292ea57bf43be6cf6fbfee36402c48ee374a8e7`); C `0x8f7a4b414417911e7e9bd738399874792cdbdb40`; hub key `0x36626bd83accd8c1e0b9268a9db98a2233fc8c55` |
| Amounts | Before the announcement: A bought 23,470 USD (33,719 shares), B 28,075 USD (40,211 shares), C 4,124 USD (6,118 shares). A and B redeemed 33,565.26 and 40,363.00 USDC |
| Period | 10 October 2025, 07:02 to 08:22 UTC, then 12:13 to 12:37 UTC after the resolution |
| Pattern | Position split across fresh accounts by an existing trader. C withdraws 60,000 then 31,270.19 USDC; each amount reaches the hub key, then a brand-new key, then a brand-new account, within two minutes. A and B trade nothing but this market. Leftovers and winnings return to C, twice by direct transfer between accounts |
| Primary evidence | [61 transfers](research_notes/early-detection-2026-11-13/data/second_group_circuit_transfers.csv) read from 46 receipts. C to hub: `0x1734cadb3c421d6584e0d3a85677785afec0c025a531c85bebafbda79db9f089`. Hub to the key of A: `0xf35ea620d047f1a6f979d7b320f816ac95ff0586d84a8a22077be0740e3423c0`. Hub to the key of B: `0xecb28ab971d236ab6b311b298507a2eeeb4d8c39cfc85fa45dd32ff3176cacd2`. B to C directly: `0x4e8e7ec557008d8b8a6682bcae346ef9c75e31742af36c859860ec34dc5c5c1a` |
| Level | Fact for every transfer. Common control of A, B and C: strongly supported (a closed circuit, exact amounts both ways). Private information: not shown |
| Other explanations | The three accounts bought after the price had moved: C at 23:09 UTC at 0.30, A and B after eight hours of a visible move, at 0.68 to 0.70. A trader who read the move as informed and followed it through fresh accounts fits everything seen |
| Statistical score | None: one case. In the frozen study such accounts are not initiators and raise no alert |
| Status | Verified. Not in the repository before this pass. No transfer links this group to the C7 funder |
| Next check | The origin chain of the hub's bridge credits (Relay records, retired on 24 November 2026); whether C used fresh accounts on other markets |

Why it matters for detection: A and B look like new participants and are not. A rule that reads "fresh wallet" as
"new person" is wrong here by construction.

## NB-3. The largest buyer of the night belongs to the same component

| | |
|---|---|
| Market | Same |
| Wallets | D `0x551e72eda42a5ab39d6d78239a1d9bbb5db6b0e0`, plus `0x1e1f17412069c0736adfaadf8ee7f46e5612c855`, `0xdaef2be2a19ad331737d06545f85615b094554e9`, `0x63b10df4bfa6d03b909ae728ee79964a594c1676`, and A, B, C above |
| Amounts | The seven accounts bought 291,894 USD of Machado Yes before the announcement, 30 % of all purchases. D alone: 201,573 USD, 259,262 shares |
| Period | Direct transfers between June 2025 and December 2025; purchases on 9 and 10 October 2025 |
| Pattern | A component of the direct-transfer graph among the 45 largest buyers. C sent D 0.01 USDC on 10 July 2025 and 2,000 USDC on 18 October 2025; D sent small amounts to two other buyers; `0x1e1f…` sent D 1,550 USDC in June 2025 |
| Primary evidence | [Graph](research_notes/early-detection-2026-11-13/data/nobel_top_buyers_direct_graph.json): a transaction hash that is a withdrawal of one account and a deposit of another. C to D: `0x7df6cf604a6e20b8660d03c0709e27f7500b94ce73448d11c50151078b70daf1` |
| Level | Fact for the transfers. Common control beyond A, B and C: hypothesis only. Small transfers months apart between established traders also fit people who know each other |
| Other explanations | A circle of traders who settle small debts; an operator with several accounts; a mix of both |
| Statistical score | Descriptive: 4 linked groups hold 60 % of the purchases before the announcement (C7 21.9 %, this component 30.0 %, two others 7.2 % and 1.1 %). No base rate from other markets yet |
| Status | Verified transfers; interpretation open |
| Next check | The same graph on comparable markets, to know whether 60 % in linked groups is unusual |

## NB-4. A purchase before the C7 funder, small and unlike that account

| | |
|---|---|
| Market | Same, and "Will Yulia Navalnaya win the Nobel Peace Prize in 2025?" |
| Wallet | `0x1e1f17412069c0736adfaadf8ee7f46e5612c855`, active since March 2024 |
| Amounts | 270 USD on Navalnaya at 0.09, then 423.81 USD on Machado at an average of 0.029 |
| Period | 9 October 2025, 20:58 to 22:10 UTC: the Machado purchases start 99 minutes before the first trade of 6741 |
| Pattern | Early entry at a very low price by an established account that had made no purchase at 0.05 or less in the nine days before, and traded nothing else that evening |
| Primary evidence | Tape rows of the wallet; its activity of 1 to 9 October 2025 (86 trades); member of the component of NB-3 |
| Level | Fact for the trades. Weak as a sign of anything: two candidates were bought, one lost |
| Other explanations | A small punt on two outsiders the night before an award |
| Statistical score | None |
| Status | Noted, not pursued |
| Next check | Its behaviour on the eve of other awards |

## NB-5. A dormant account reactivated for this market alone

| | |
|---|---|
| Market | Same |
| Wallet | `0xa0f16053cded8f2373e1fd986816aec3f75b1f6a`, one market traded before, in July 2025 |
| Amounts | 24,593.24 USDC received at 04:44:13 UTC, 24,308 USD bought between 04:45 and 05:28 UTC, 35,367 shares redeemed, 35,657.16 USDC withdrawn at 13:06:58 UTC |
| Period | 10 October 2025 |
| Pattern | Dormant account, one deposit, one market, full exit an hour after the resolution |
| Primary evidence | Deposit `0x3f29a4bf38987cff484639d89341fd1dc00dc334adb0e2ce9a8446da9254a645`, withdrawal `0x5ed3a8ed95d30b2447c43cd2d958fbbc5e46063e67c4a03b5f43906eaac7e69f` |
| Level | Fact for the flows. The deposit arrived through a bridge solver used by very many accounts, so its origin is unknown and it links this account to nobody |
| Other explanations | A follower of the visible move, six hours after it began |
| Statistical score | None |
| Status | Open |
| Next check | The bridge record of the deposit and of the withdrawal |

## What was looked for and not found

- No transfer between the C7 accounts and any of the 37 other large buyers.
- No payer shared by the six accounts first examined other than bridges and the hub key of NB-2.
- `0x9db778f46b7c9b458045764a67ff4afcae917e1f`, the fourth largest buyer, first bet against Machado (20,458 USD of No at
  22:57:43 UTC) and only then bought Yes: not an early informed buyer.

## Leads from the systematic study

See [PATTERN_RESEARCH.md](PATTERN_RESEARCH.md): every alert of the tested class on markets never examined before is listed
there with its market, account, time and outcome. Each is a lead of the same kind as NB-1 and none has been
investigated.
