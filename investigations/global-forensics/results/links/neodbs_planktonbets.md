# The address shared by the files neodbs and planktonbets

Read on 2026-11-03 by `engine/tools/link_dossier.py`, from `neodbs_planktonbets_spec.json`. Output: `neodbs_planktonbets.json`, 189 network calls. The earlier graph held this link at level `LISTED`. All 12 moves below are now `REVERIFIED`: the receipt or transaction was read from two node hosts that agree.

No wallet here is called an insider. An address is not a person.

## Three separate questions about `0x4e062726688d02cffff7c39918bfb3d4470614eb`

| Question | Answer | Basis |
|---|---|---|
| Common funder of the accounts? | **No** | It never sent anything to neodbs, planktonbets or mrs-joker on Ethereum, Polygon, Arbitrum or Optimism. It received neodbs's withdrawal. Its only value outflows are 98,679.335887 USDT to Bridgers and 0.016753 ETH to `0xa347…`. Base and BSC were read by presence only. |
| A service? | **Nothing says so** | No label in the tables used here, an EOA with nonce 3, 4 value counterparties in and 2 out. The service in this path is Bridgers (`0xb685…`, a contract with over 92,000 listed rows, named in the September archive). This is absence of evidence from size and labels, and an unlisted service using a fresh address per client is not excluded. |
| Who holds it? | **Unknown** | `OWNERSHIP_NOT_ESTABLISHED`. Nothing public names a holder. |

The earlier wording, a shared address reached by both files, hid the direction. It is a destination of neodbs's money, and two addresses from the other files sent it ETH afterwards.

## What happened, in order

| Step | UTC | From | To | Amount | Block | Log | Level | Transaction |
|---:|---|---|---|---:|---:|---:|---|---|
| 1 | 2026-02-28 09:43:59 | `0xf70da978…` | `0xe9a7230f…` | 200,506.064123 USDT | 24554615 | 224 | REVERIFIED | `0x2865d714d86f830545acd085f4d69295b8a08101a5550f8f4eedc06bbf3f9b06` |
| 2 | 2026-02-28 09:49:59 | `0xe9a7230f…` | `0x2225a4fd…` | 0.004315 ETH | 24554644 | native | REVERIFIED | `0x89eceb11f3e6345e1668e7dfca13cebcf36b74bd96b253a99d9e8a212dc93cb3` |
| 3 | 2026-02-28 09:54:11 | `0xf70da978…` | `0x2225a4fd…` | 156,897.758480 USDT | 24554665 | 377 | REVERIFIED | `0x935106d9ea22c9c2d7792b9aaaee5d734781cf5187d2b20480ac7b71f9721716` |
| 4 | 2026-02-28 10:00:35 | `0xe9a7230f…` | `0xb685760e…` | 38,696.450000 USDT | 24554697 | 646 | REVERIFIED | `0x2ba1113c956d752a59070faf6ad1f678693b87fc8d5679575bfc889ec22ba100` |
| 5 | 2026-02-28 10:07:23 | `0x2225a4fd…` | `0xe9a7230f…` | 156,897.758480 USDT | 24554731 | 338 | REVERIFIED | `0x12e4eb2dcc731772e5bf09be5c581d0a6dbc608b02c2cc1fcf67bc6e9cc86dfa` |
| 6 | 2026-02-28 10:13:47 | `0xe9a7230f…` | `0xb685760e…` | 159,373.465355 USDT | 24554763 | 800 | REVERIFIED | `0x28dbb955703158c438128bf310ffed87aa0ef9edabcae33e927c62c06cb1efdb` |
| 7 | 2026-02-28 10:18:35 | `0xf70da978…` | `0x4e062726…` | 98,679.335887 USDT | 24554787 | 879 | REVERIFIED | `0xefab4c3b54dbf1180f5c289adf9e0345e0f1b256a9b706537915d565cf34dd28` |
| 8 | 2026-02-28 10:21:35 | `0xe9a7230f…` | `0xb685760e…` | 159,373.465355 USDT | 24554802 | 149 | REVERIFIED | `0xac894e838b78c631f0485b895a529fde2275e6e0666a8a1d123826f6de106a9e` |
| 9 | 2026-02-28 10:21:59 | `0x4e062726…` | `0xb685760e…` | 98,679.335887 USDT | 24554804 | 722 | REVERIFIED | `0xf6f4ae986acd03e0f6a41dc0d4e064d228fc5c04f88241d9d2f2ce985d9a2172` |
| 10 | 2026-03-01 17:46:11 | `0xe9a7230f…` | `0x4e062726…` | 0.004023 ETH | 24564175 | native | REVERIFIED | `0xa3fe271784fc3f06f7e6fe8625d346b0a872705595868dc87602a89e1570f60c` |
| 11 | 2026-03-01 17:47:47 | `0x2225a4fd…` | `0x4e062726…` | 0.004248 ETH | 24564183 | native | REVERIFIED | `0xc78c5439f16f19fcea82949511b333a44869425371ee7ebfa3f8a197409fc434` |
| 12 | 2026-10-14 20:53:47 | `0x4e062726…` | `0xa347472c…` | 0.016753 ETH | 26193259 | native | REVERIFIED | `0x798500f434aacd93c09890f836db5b93e5fb50c21545060fac33db71792c8c6a` |

Steps 1, 3 and 7 are Relay payouts. Each is tied to its withdrawal on Polygon by the same 32-byte id, read from nodes on both chains, not from Relay's API or from amounts:

| Withdrawal | Polygon deposit | Sender read on-chain | Same id on both chains |
|---|---|---|---|
| planktonbets withdrawal | `0x96774c8c2b6c6a303cf2f00916198a0891abfa6145b6506b7b11cbba6a2e7c98` | `0x38745db27f7360a287f6ca3c9b6a6a9c76149801` | yes |
| mrs-joker withdrawal | `0x4a60fcc6d89147cfd0f635fe9b2755575652ac885d3d1922296cb3d4ec26c2c1` | `0xe9b80c387ba77a585423b13c850c2e126c3befd8` | yes |
| neodbs withdrawal | `0x6182e18523991bed04b1112b8c28316bb7024bbae104862cfcc2e3bad2dd282a` | `0x56efadc9defe5b7a21af751e0d026f2cf54136db` | yes |

## What this shows

- **Moves, confirmed.** Three accounts withdrew through Relay within 35 minutes on 2026-02-28, to three different Ethereum addresses.
- **Order, confirmed.** `0xe9a7…` paid gas to `0x2225…` at 09:49:59, four minutes before `0x2225…` received the mrs-joker payout at 09:54:11. Thirteen minutes later `0x2225…` sent the whole 156,897.758480 USDT to `0xe9a7…`, which then sent USDT to Bridgers.
- **The tie, confirmed.** On 2026-03-01, `0xe9a7…` and `0x2225…` each sent ETH to `0x4e06…`, 96 seconds apart. Before that date, `0x4e06…` had only received neodbs's payout and passed it to Bridgers.

So the exit addresses of three accounts exchange money and act in a tight sequence. That is what one operator would do. It is also what a desk or an agent handling exits for several clients would do. Public data cannot separate these, and this file does not merge owners.

## What this does not show

- Who holds any address, or that the three accounts share a holder.
- Anything about what any of them knew. This file does not look at their bets.
- The two ETH amounts are small, about 0.004 ETH each. Their weight is in the order and the counterparties, not in the money.
- `0xa347…` is older and busier (nonce 23, activity from 2023). It was read here as a destination only. Its holder is unknown too, and sending leftover ETH there says little.

## Coverage and stops

- Read in full on listed rows: Ethereum, Polygon, Arbitrum, Optimism. Base and BSC: nonce and balances today only.
- Bridgers to Tron: the September archive gives Tron destinations with `minReturn` from calldata. The Tron side was not re-read in this file, and a swap service's internal matching of client to payout cannot be proved from public data past what it writes. The conclusion stops at Bridgers on Ethereum.
- The ETH that reached `0x4e06…` at 10:12:23, six minutes before the payout, was sent by Bridgers (`0xb685…`, submitter `0xa377aa68…`). Who paid for it is an internal record of that service: `OFFCHAIN_RECORD_REQUIRED`.
- Tron funding of these accounts: not reconciled here.
