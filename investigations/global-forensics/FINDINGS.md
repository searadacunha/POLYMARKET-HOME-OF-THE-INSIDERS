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
