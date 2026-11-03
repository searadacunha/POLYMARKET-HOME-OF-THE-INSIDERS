# Findings

## F-001 | CONFIRMED | All 104 reference transactions of the Ballon d'Or and ChangeNOW files agree when re-read from two nodes at different hosts
- Sources: results/references/reference_verification.json ; results/references/reference_verification.csv
- Method: engine/tools/verify_references.py reads each receipt from a node, then the same receipt from a second host, and compares them with the amounts in the files. Hashes come from the files.
- Limits: confirms that the moves happened as written. Says nothing of who holds the addresses, nor of any reading placed on the moves.
- Links: ballon-dor-wallets:F-001 ; ballon-dor-wallets:F-002 ; ballon-dor-flow-trace:F-001 ; changenow-proof:F-001

## F-002 | CONFIRMED | Public data reproduces the figures an indictment gives for the account with the username Burdensome-Mix: 13 buys, 33,934.339992 in purchases, 409,880.950989 in cash result, a withdrawal of 437,858.687686 USDC.e
- Sources: results/control_federal_case/control.json
- Method: engine/tools/control_federal_case.py rebuilds buys, cash by market and withdrawals from the current API and from receipts, against figures read by eye from the scanned indictment, whose SHA-256 is in the output. 11 of 12 listed purchases match one row within a share, and the twelfth matches as two rows.
- Limits: an indictment is an accusation and no verdict is known here. It names no wallet: the link is the username in press coverage and in the API's own rows. This validates the accounting method on one external case, and nothing about intent, access to information or detection. The earlier PnL was computed in September without this document.
- Links: maduro-iran:F-002

## F-003 | UNRESOLVED | The first destination of that withdrawal is not reconciled: earlier files call it Coinbase 4, on one Solscan name, and the indictment describes a foreign vault
- Sources: results/control_federal_case/control.json ; results/wallets/burdensome-mix.md
- Method: Relay payout read on Solana, then the receiving address's history. The destination address holds 1.88 million USDC by a node read, with over 1,000 signatures in about 3 hours.
- Limits: a hub tells nothing about who holds an account inside it. The later 444,209 USDC.e and the brokerage account are private records, so the path cannot be finished from public data.
- Links: none

## F-004 | CONFIRMED | Three risks named before integration exist in the code: an exchange can become a shared funder, convergence over 24 hours alone sets the top category, and validation passes a claim opposite to its source
- Sources: tests/test_adversarial_existing.py
- Method: synthetic inputs against the unmodified modules, no network. Details in AUDIT.md.
- Limits: shows the code's behaviour on crafted inputs. How often it changed a past category was not measured. The active engine was not touched.
- Links: none

## F-005 | SUPPORTED | Wallets align on low-priced outcomes more than local intensity allows, and on average those bursts show no large excess over the price paid: the frozen verdict is NOT_SUPPORTED on all six windows
- Sources: results/study_sync/results.md ; results/study_sync/tables/verdict.json ; results/study_sync/tables/h1.json ; results/study_sync/amendements/001-2026-11-03.md
- Method: frozen plan on 2,091 resolved large markets, 648 events, taker rows of at least $100. Bursts of 3 entrants against entrants of the same price, crowd and token size, cluster bootstrap on events. Reproduced in a fresh copy with identical outputs, and the frozen table rebuilt with identical bytes.
- Limits: this is an average over matched bursts. A subset of informed bursts stays compatible with it, and synthetic effects of +0.10 on all bursts were never detected. Three blind audits found that a matching key descends from the outcome, and that controls did not fully pass. Amendment 001 was written before results were opened and restricts every reading. Says nothing about any wallet or about insider trading. All auditors are instances of one model family.
- Links: maduro-iran:F-006

## F-006 | SUPPORTED | Of 431,444 recipients of attributed ChangeNOW payout addresses over 90 days, 26 reach a known trading wallet directly, and 9 of them bought in the Ballon d'Or family between payment and the first public report, for 202.30 in total
- Sources: results/CHANGENOW.md ; results/changenow/cn_join_report.json
- Method: engine/tools/cn_polymarket_join.py, offline, with a positive control (11 of 11 known keys) and a negative control (0 hits on 20,000 random addresses).
- Limits: archived data, not re-read from nodes here. Attribution rests on labels. A recipient forwarding before funding is invisible, so this is a lower bound. Safe wallets untested, several chains absent, no base rate from another service. A payment is not a funding of a bet.
- Links: changenow-polymarket:F-002

## F-007 | CONFIRMED | A public order book archive covers the Iran and Khamenei windows of February 2026 and not Maduro, the 2025 Nobel or the Ballon d'Or, at the hours tested, and holds no row for the ceasefire market on 2026-04-07
- Sources: results/ORDERBOOKS.md
- Method: HEAD on hourly file names, then row groups read by HTTP range for three markets.
- Limits: not every hour was probed. One third party's capture, terms not confirmed, real-time capture not shown. Depth reads one token's side only.
- Links: none

## F-008 | SUPPORTED | Replayed read-only on what the collector kept, the shadow detector gives 283 alerts in 6.25 days, and 19 gaps in collection, the largest about 34 hours
- Sources: results/shadow/status.json
- Method: engine/gf/shadow.py, clock moved by observation time, no outcome in the module, enforced by a test.
- Limits: a replay, not a prospective run: nothing was scheduled, since that is a production decision. No precision or recall exists, for lack of ground truth. Alerts are timing patterns.
- Links: none

## F-009 | CONFIRMED | The address shared by the files neodbs and planktonbets is no common funder and shows no sign of being a service: it received neodbs's withdrawal, and addresses from the planktonbets and mrs-joker exits later sent it ETH. Its holder is unknown
- Sources: results/links/neodbs_planktonbets.md ; results/links/neodbs_planktonbets.json ; results/links/neodbs_planktonbets_spec.json
- Method: engine/tools/link_dossier.py reads 12 moves from two node hosts each, all REVERIFIED, and ties the three Relay withdrawals by the same id read on both chains, without the API. The address's history is read on Ethereum, Polygon, Arbitrum and Optimism.
- Limits: base and BSC by nonce and balance only. Tron not re-read here. Past Bridgers, a swap service's internal matching is a private record. The tight order and the shared counterparties fit one operator, and they also fit a desk or agent handling exits for several clients. Owners are not merged, and this says nothing about what any account knew.
- Links: maduro-iran:F-002

## F-011 | SUPPORTED | The shadow replay's delays come mostly from collection, not detection: 111 of 283 alerts arrive at a median of 189 s, and 172 arrive hours later, while 88.5 of 159 hours of span sit in collection gaps
- Sources: results/SHADOW.md ; results/shadow/latency_sources.json ; results/shadow_v2/status.json
- Method: engine/tools/shadow_latency.py reads the collector's state in short read-only pages, offline. Each alert is classed by its delay and by the gap before it.
- Limits: a replay on what the collector kept, no precision or recall. The state grew since the first replay, so rows and alerts come from slightly different spans. Causes of each gap are not established one by one.
- Links: none

## F-012 | CONFIRMED | shadow-1 groups entries spread wider than the window it states, in 100 of 283 alerts, and a research successor removes that
- Sources: results/SHADOW.md ; results/shadow/latency_sources.json ; results/shadow_v2/status.json ; tests/test_shadow.py ; engine/gf/shadow2.py
- Method: measured on the replay's alerts, and reproduced on a synthetic out-of-order case that shadow-1 reports as a 5-second set over 2,100 s. shadow-2 fits each set inside its window and labels each alert LIVE or LATE, with tests.
- Limits: shadow-2 was only replayed, on the same kept rows. It proves nothing about detecting anything. Nothing was installed, and PolySentinel and its sealed alerts were not touched.
- Links: none

## F-010 | CONFIRMED | Of the 571 edges of the Maduro and Iran file, 547 agree when read again, by amount and parties or by the same bridge id on both chains, none contradicts its move, and 24 stay partly read
- Sources: results/MADURO_REREAD.md ; results/maduro_iran/edge_verification.csv ; results/maduro_iran/summary.json
- Method: engine/tools/verify_maduro.py reads each edge on its own chain: EVM receipts from two hosts, Tron from TronGrid, Solana from public nodes. Cross-chain rows are read side by side and tied only by the same Relay id. Cash for the 12 accounts is rebuilt from the current activity route.
- Limits: confirms moves, not the file's reading of them or who holds any address. Tron rests on one host. 13 rows are tied only by the archive's pairing, since the id test does not run on Tron here. 4 Solana rows do not show the id where this reader looks, which is no refutation. One Bitcoin row has no reader.
- Links: maduro-iran:F-002

## F-013 | SUPPORTED | On re-read edges only, services removed, the 8 accounts the September file calls its network stay one connected group of money, even with its 6 busiest other addresses removed. The federal-case account, SBet365 and 0xa72db1749e stay apart from it in this table
- Sources: results/links/maduro_components.json ; results/maduro_iran/edge_verification.csv
- Method: engine/tools/maduro_components.py keeps 349 of 571 edges, those that came back AGREES or CROSSCHAIN_SAME_ID and touch no address the archive labels a service, computes connected components, writes a shortest proved path from one account to each other, then removes each busy unlabelled address in turn and all together.
- Limits: a table built by following money from these accounts finds them connected by construction, and it holds no comparison group. A component ignores direction, time and size. An unlabelled service could join what it should not, which the removal test only partly answers. Accounts apart here can be linked outside this table. It shows money between addresses, and no common holder and nothing about what anyone knew.
- Links: maduro-iran:F-002

## F-014 | SUPPORTED | On February 26, the three entries of mrs-joker, planktonbets and neodbs in the Iran strike market paid the visible ask or less, with $21,566 to $28,355 of ask depth within 2 cents, and the mid moved a cent or less over five minutes around them
- Sources: results/ORDERBOOKS.md ; results/orderbooks/iran-strike-feb28.json
- Method: engine/tools/pmxt_market.py reads the hours of chosen entries from a public capture by HTTP range, and engine/tools/book_at_trades.py takes the state one second or more before each trade, with a quote at most 900 s old.
- Limits: one third party's capture, terms not confirmed. Depth reads one token's side. No comparison with other buyers of that day. It describes what the trades met, and nothing about what anyone knew.
- Links: maduro-iran:F-002

## F-015 | SUPPORTED | The 26 wallets reached from ChangeNOW's attributed addresses are no excess: the same test on Bridgers and SwftSwap finds a known trading wallet at a higher rate per recipient
- Sources: results/CHANGENOW.md ; results/changenow/comparators.json ; results/changenow/cn_polymarket_hits.jsonl
- Method: engine/tools/cn_comparator.py applies the join to recipients of other swap addresses in the same block window, against the same known wallets and wallet forms, with Wilson intervals.
- Limits: a few addresses against many, different collectors, one partial read, labels from public lists. A rate of reaching a known wallet is no rate of funding a bet. It says nothing about any one of the 26.
- Links: changenow-polymarket:F-002

## F-016 | HYPOTHESIS | A second study of synchronised entries is frozen before any of its data: it fixes the defects the audits found in the first, scores only rows after the first study's period, and its verdict can state a bound
- Sources: results/study_sync_v2/analysis_plan.md ; results/study_sync_v2/controles/controles_positifs.md ; results/study_sync_v2/PROTOCOL.lock.copy.txt ; results/study_sync_v2/code/lib_v2.py
- Method: three blind audits before the freeze, all findings treated. Controls through the same parser on synthetic tapes, 100 seeds on each null and trap at the stopping size. Stop at 200 facts with a trigger or on 2027-06-30, from counts with no outcome. No outcome and no rate of its holdout was read.
- Limits: this is a plan and no result. The first study's data shaped it, and that role is stated in the plan. One trap reaches the limit of 5 false passes in 100. Synthetic power is an upper reference. A true informed set a few hours before its news can only reach POSITIVE_NOT_INTERPRETABLE, a choice open to Benjamin's review. All reviewers are one model family.
- Links: none
