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
