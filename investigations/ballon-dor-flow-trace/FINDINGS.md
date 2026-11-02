# Findings, ballon-dor-flow-trace investigation

Data read on November 2, 2026. An address is not a person. Detail per account: `sources/reports/FUNDING_FORENSICS_FINAL.md`.

## F-001 | CONFIRMED | The brace227 key sends 5,170.00 USDC to a new key, owner of a Polymarket wallet not named by the press to my knowledge, which buys only Kane Yes
- Sources: sources/reports/COMMON_FUNDERS.md ; sources/data/followups.csv ; sources/state/followups.json ; sources/state/wallet_0xa8e6_activity.json ; sources/state/personal_wallets.json ; tx 0x7e3aecb9b41e6d3f92f25b8760228f15e9b55e798cd27977eb7170445cf64349 (Ethereum, block 26157246, 2026-10-09 20:28:35 UTC) ; tx 0xb07c3c53a713d98aea1d1bd5d6facf849b6edc675c0fe2cfd3df5b791db20add (Ethereum, block 26158556, 2026-10-10 00:51:11 UTC) ; wallet creation tx 0xa6e229972cef372f1efd5dbb24fe2459c4d279b49d1789a1093f7c1dad215d7b (Polygon, block 95166129, 2026-10-08 10:13:20 UTC) ; withdrawal tx 0x09d05d707c4d804dfc86e829f4c1cac90627b7130c54315d16a4d125c207cd3a (Polygon, 2026-10-27 18:49:06 UTC)
- Method: sources/tools/walk.py, sources/tools/proxy_check.py, `owner()` read on wallet `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5`, sources/tests/test_forensics.py section 7, on-chain re-reading by a parallel session
- Limits: 16 purchases for $5,164.99, $8,061.90 withdrawn. Almost equal shares with brace227: 49.98% and 49.95% of what the key receives from SwftSwap on October 9 and 10. Does not prove a common owner, see F-002. Nothing says this wallet is the 12th account alleged by the press.
- Links: none

## F-002 | UNRESOLVED | One owner controls both the brace227 key and the key of the unnamed wallet
- Sources: sources/reports/COMMON_FUNDERS.md ; sources/state/walk_brace227.json ; sources/state/wallet_0xa8e6_activity.json
- Method: reading of the flows and of the exit schedules
- Limits: a gift, a loan or an advance between close contacts gives the same picture. Against a single operator: two distinct keys, and brace227 sells its Kane at 0.999 on October 26 while the other wallet waits for the payout and withdraws 16 hours 51 minutes later.
- Links: none

## F-003 | CONFIRMED | Only one direct transfer exists between the keys of the eleven accounts: 0.00205 ETH from brace227 to kraben006
- Sources: sources/reports/COMMON_FUNDERS.md ; sources/state/pairs.json ; sources/state/walk_brace227.json ; tx 0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98 (Ethereum, block 26119420, 2026-10-04 13:54:35 UTC) ; preceding Relay payment tx 0xb17e1c4627ad8914f98f48a4fa7f5916953d3286e60cf3d80c6508257f46ce3c (Ethereum, 2026-10-04 13:52:47 UTC)
- Method: sources/tools/pairs.py on the raw history (native, internal, all ERC-20, Solana) of the own addresses, 55 pairs ; same reading on 54 control keys, sources/tools/compare_rates.py
- Limits: about $5.5, less than 0.1% of deposits: a link between two keys, not a funding. 1 out of 55 named pairs, 0 out of 1,431 control pairs, which is not a test: the pairs are not independent. BSC and Base not read the same way.
- Links: none

## F-004 | UNRESOLVED | A common funder or owner links all eleven accounts
- Sources: sources/state/pairs.json ; sources/reports/COMMON_FUNDERS.md
- Method: sources/tools/pairs.py: no shared personal-size address apart from the two keys of F-003, 23 shared services classified
- Limits: platform accounts can hide a single holder. Only one positive control for a direct link: the sensitivity of the method is not measured.
- Links: none

## F-005 | SUPPORTED | More than half of the $304,137.63 in deposits comes from addresses labeled KuCoin Hot Wallet 2 ($102,833.93, 5 accounts) and Binance ($65,755.73, 3 accounts)
- Sources: sources/reports/FUNDING_FORENSICS_FINAL.md ; sources/data/funding_paths.csv ; sources/evidence/blockscout_tags.json ; tx 3bn5hJNsXAx814rxWrHrHUPqY5C53NF3sSH4CfH8uhk19ExDFUrNAcE6g73oj5Vmcwc6NTBcD7wpJ8pmdLHnJR2t (Solana, 2026-10-11 15:23:10 UTC) ; tx 0x23e2219c3e902360004a3f893ac3560649617a0ac372ff9aa9d218f0ad442ff3 (BSC, 2026-10-13 13:46:53 UTC) ; tx 0x2c0d0943a7874d99abbc28c4d4930407c8eaad006df45655f6e3ad0c2b808db3 (Polygon, 2026-10-18 20:14:03 UTC)
- Method: sources/tools/walk.py, sources/tools/labels.py, sources/tools/blockscout_tags.py
- Limits: the flows are demonstrated, the names rest on labels. KuCoin Hot Wallet 2: Orb alone, and KuCoin's official 2022 list contains no Solana address. A label does not identify any customer.
- Links: none

## F-006 | CONFIRMED | Relay is involved in all 46 deposits and all 25 withdrawals, the 25th being a swap on the same chain
- Sources: sources/reports/FUNDING_FORENSICS_FINAL.md ; sources/data/funding_paths.csv ; sources/data/cashout_paths.csv ; sources/evidence/relay/
- Method: Relay records, and the same identifier read on both chains by sources/tools/walk.py (`relay_proof`)
- Limits: a solver pays from its own inventory: this is a value equivalence, not the same tokens. A common service, not a link between people.
- Links: none

## F-007 | UNRESOLVED | The funds went through a mixer or through Monero
- Sources: sources/reports/EXCHANGE_AND_PRIVACY_EXPOSURE.md ; sources/tests/test_forensics.py section 8
- Method: search for addresses labeled Tornado Cash, Railgun, ChangeNOW, FixedFloat, SimpleSwap and others across all histories read
- Limits: no interaction with a labeled mixer read, no sign of XMR. Absence of evidence only: platform accounts and unidentified services are opaque, and a break in the trace is not a sign. ChangeNOW, which lists XMR, touches the kraben006 key and a former funder of brace227: simple compatibility.
- Links: none

## F-008 | CONFIRMED | About 74% of the $493,094.76 withdrawn was still on its first address, or had returned to it, on November 2
- Sources: sources/reports/CASHOUT_PATHS.md ; sources/state/walk_thin.json ; sources/state/walk_0x86544e4dfde.json ; sources/state/walk_brace227.json ; sources/state/walk_walletwallet8424.json ; sources/state/walk_kraben006.json ; sources/state/walk_ouldlm3alem.json ; sources/state/walk_0xdd97e6.json
- Method: balances read on public nodes and Solana RPC on November 2: $299,565.17 in stablecoins and 26.97 ETH across 7 accounts, ETH counted at its withdrawal value, $63,143.10
- Limits: snapshot of November 2. An address says nothing about the economic beneficiary.
- Links: none

## F-009 | CONFIRMED | All pUSD and position movements of the 11 wallets reconcile
- Sources: sources/reports/CASHOUT_PATHS.md ; sources/state/reconcile.json ; sources/tests/test_forensics.py
- Method: sources/tools/reconcile.py: 46 deposits and 25 withdrawals matched, remaining mints all `REDEEM`, computed balance equal to the balance read on 11 wallets, 0 position transfers outside a market transaction
- Limits: 0.20 pUSD received by OuldLm3alem from another wallet, absent from the API, looks like a tip, not verified.
- Links: none

## F-010 | REFUTED | Funding less than an hour before the first purchase distinguishes the eleven accounts
- Sources: sources/reports/COMMON_FUNDERS.md ; sources/state/compare_rates.json ; sources/state/comparators.jsonl ; sources/state/comparators_named.jsonl ; sources/reports/COMMON_FUNDERS.md
- Method: sources/tools/comparators.py and sources/tools/compare_rates.py, 78 control wallets, 77 read, same reader, full deposits: 9/11 against 32/39 fresh accounts, p = 0.69 ; 41/76 all controls, p = 0.074
- Limits: refutes this trait against accounts of the same age, not a coordination through another signal. Traits chosen after the fact, none passes the threshold corrected for 9 tests.
- Links: none

## F-011 | CONFIRMED | OuldLm3alem converts its withdrawal, moves it to Hyperliquid, trades the HYPE perpetual at a loss, and 73,001.19 USDC return to the key
- Sources: sources/reports/CASHOUT_PATHS.md ; sources/state/bridges.json ; sources/data/cashout_paths.csv ; tx 0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1 (Polygon, 2026-10-26 23:50:53 UTC) ; tx 0x8c35829294c002aabcd2bd518e88f46f86e4c5a075c6e89938d4532cc62dd2c3 (Polygon, block 96235593, 2026-10-26 23:52:41 UTC) ; tx 0x70a1e0133b21f471c6e5bd556c54c5df982606ac8c45a47286edc0344c5d108f (Polygon, block 96401241, 2026-10-29 20:54:51 UTC) ; tx 0x5c5e1650625c27fdc99cd69993a79132db223b899fef7b1b6b85911cf0fc223a (Arbitrum, block 519468529, 2026-10-29 20:55:52 UTC)
- Method: sources/tools/bridges.py: deBridge order, Circle message, public Hyperliquid registry. 303 executions, $2,415.41 in realized losses, $306.71 in fees, reconciled to within $0.02
- Limits: the pUSD burn is not a destination. This path says nothing about intent.
- Links: none

## F-012 | CONFIRMED | The WenZhuanBuPei withdrawal goes through an address that sets aside exactly 1%, then its 3 pieces are grouped in a single transaction
- Sources: sources/reports/CASHOUT_PATHS.md ; sources/data/followups.csv ; sources/state/followups.json ; tx 0xa06fecae758b361f2acf0c2198c5f399c89326806e0906d58561c6eb338640da (Arbitrum, 2026-10-27 22:58:10 UTC) ; tx 0x8246f4390406420d52f7871285a92eb982990f3da71fd257c7ad63bedb907076 (Arbitrum, 2026-10-27 22:58:11 UTC) ; tx 0x6ef3a7e79935761cc66aea1ac423526682d6b8d26ef107e755218518c2ba1547 (Arbitrum, 2026-10-28 17:23:07 UTC)
- Method: sources/tools/followups.py ; the same address pays exactly 99% on 7 of the 8 inflows of at least $40,000 read, up to $238,567
- Limits: neither a platform nor a mixer is demonstrated. `0x51cf2d9f…4999` has 3,037 senders and 1,630 recipients, and its history as read is truncated in the middle.
- Links: none

## F-013 | HYPOTHESIS | Zoomman17 sent its withdrawals on to Revolut
- Sources: sources/state/walk_zoomman17.json ; sources/evidence/blockscout_tags.json
- Method: profile: `0x8c5dc729…10fe` at nonce 1, a single sweep of 6,893.00 USDC to `0xf7c8da79…d921`, tag Revolut 5
- Limits: single-source tag, confirmed only by 27 rows with Revolut 1. Revolut's records would settle it.
- Links: none

## F-014 | HYPOTHESIS | The kraben006 key resold at ChangeNOW the gas received from brace227
- Sources: sources/state/walk_kraben006.json ; sources/evidence/blockscout_tags.json
- Method: 0.00247 ETH to `0x7e67df45…6e23`, 10 hours after receipt, then 0.00241 ETH to `0x3f3ee0a9…207b`, tag ChangeNOW Dep
- Limits: ETH is fungible, this is sequence and not proof. Single-source tag, ChangeNOW order not public.
- Links: none

## F-015 | UNRESOLVED | The eleven accounts or the unnamed wallet had access to inside information
- Sources: sources/reports/FUNDING_FORENSICS_FINAL.md
- Method: none, the flow data do not answer this question
- Limits: a common origin does not demonstrate inside information, and no civil identity is sought or established. The accounts were chosen after the fact by the press.
- Links: none

## Contradictions

- The first report of the original investigation wrote "0 direct transfers, 0 discriminating links" and "no additional wallet linked": contradicted by F-001 and F-003. The original session corrected it in its report.
- "First outflow in 17 months" for the brace227 key (audit): 16 and a half months, because a BSC outflow dates from May 17, 2025.
- "9/11 against 10/43, p = 0.0006" (original investigation): see F-010.
- The "1% service" attributed to `GxjcMTWW…nvBW` by the original investigation was not found: the sweeps read take nothing. This report measures 1.00% on `0x3ab2206b…7d50`, a different address.

## Missing to conclude

- The records of KuCoin, Binance, Revolut, BloFin, SWFT, ChangeNOW and unidentified services, by legal process.
- The operator of `0x0ce9bdf3…f06d`, `0x58f298e3…0214`, `0xa3222357…59b3`, `0x6bf18baf…7e95`, `GxjcMTWW…nvBW`, `0x51cf2d9f…4999`.
- A complete history on BSC and Base, inflows included.
- A truly independent review.
