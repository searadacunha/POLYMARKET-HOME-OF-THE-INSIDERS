# G38 Iran cohort: proof-tier correction and Relay-versus-beneficiary audit

**8 November 2026.** Follow-up to the frozen [November 6 verification](../x-history-2026-11-06/verification/REPORT.md) and the [November 7 funding-origin replay](../financial-links-replay-2026-11-07/REPORT.md). This document does not rewrite the source snapshots, invent fresh RPC responses or attribute real-world identities. The classification below supersedes any reading of "38/38 reached the same Coinbase account" as a confirmed ownership or exchange-credit claim.

## Reproducible population and accounting

The archive contains **38 unique Polygon trading proxies**. One displayed name, **Anon**, is an address candidate matched to an earlier screenshot by an approximately equal result; its corresponding public profile was unavailable. This is **37 profile-supported names plus one supported candidate**, not 38 independently confirmed names. The 36 accounts created 22–25 February have a recorded NO-before-YES sequence and first YES purchases on 27 February. They were selected retrospectively; a matched control-population base rate and a test of independence are absent.

The 38 per-account ledger outcomes sum to **+1,576,522.86 USDC** when each historical account result is rounded to cents. **Eight accounts still have open share tokens** in the snapshot, so this is a recorded trading-result measure, not 38 fully realised final profits. The 86 archived incoming Relay deposit orders came from 39 distinct funding addresses, with no address used for two cohort proxies. Common upstream exchange labels cannot bridge that gap into an assertion of shared control.

## What reaches the common EVM address

Recipient address on Polygon and Arbitrum, also designated by Relay for Base: 0xc5bb1be0407db7312911ec765d399d02461e411a.

| Accounts | Path | Evidence tier and exact boundary |
|---:|---|---|
| **32** | Polymarket proxy directly transfers official USDC/USDC.e into the recipient on Polygon | **CONFIRMED ON POLYGON**: token transfer sender, receiver, contract, amount and time recorded |
| **3** | Proxy places a Relay withdrawal; Relay settles USDC to the same recipient on Polygon | **SUPPORTED AT ORDER/RECEIPT LEVEL**: 12 distinct successful orders, 12 credits, a bijection of exact atomic amounts (not only aggregate equality). Independent source-to-fill order-id replay is not claimed here |
| **1** | Arbitrum destination of a Relay order | **SUPPORTED**: one 59,863.534997-USDC incoming ERC-20 event matches the archived Relay output amount, then the whole amount leaves that address for 0xa656f7d2…; no attribution for the onward wallet or a Coinbase credit |
| **2** | Relay orders naming the same destination on Base | **RELAY-REPORTED ONLY**: 58,475.748639 and 42,142.977084 USDC designated; destination-chain receipt/log collection is not archived in this evidence bundle |

The 12 Polygon Relay output amounts sum to **474,710.981541 USDC**, equal to the 12 recorded Polygon recipient credits **as a multiset of atomic values**. The Polygon recipient also receives official USDC.e directly. Excluding nine unrelated look-alike token events and three microscopic address-poisoning transfers from two look-alike addresses, **1,984,038.168550** official USDC/USDC.e enters and the same quantity leaves this address in the frozen history (5 January–9 March 2026). This is **gross flow, not profit**.

The address signs 24 sequential ordinary EVM transactions (nonces 0–23). Its Polygon gas funders and four nonzero USDC/USDC.e sweep recipients are labelled Coinbase by one Blockscout-derived label lineage. The observed sweep pattern is consistent with exchange deposit infrastructure, **not with an ordinary Relay receiver or pool contract**. Labels and behaviour do **not** confirm the name of an exchange customer, a customer account identifier, or the number of people with access to that customer account. An EVM address used on multiple chains does not guarantee the same exchange will credit the same internal account on every chain.

## Why this does not establish a single controller

1. **Relay is not the final recipient on Polygon.** In 32 paths the proxy is the sender; the other 12 Polygon credit transactions come from Relay settlement contracts/solvers. The destination is a separate address. This disproves the narrow "everyone merely touched the same Relay contract" explanation for those 32 payments.
2. **The Coinbase account assumption is an inference.** No Coinbase internal ledger, account identifier, KYC record or independent customer confirmation has been obtained. The Arbitrum onward destination is unclassified. Base final delivery receipts are absent.
3. **A private common funder is not shown.** The 39 entry-side funding addresses are separate within the observed Relay data; a shared Coinbase/Robinhood hot wallet is a service-level event, not a person-level link.
4. **The cohort is retrospective.** The strong NO-then-YES trading pattern is observed, but without account-creation, market participation and ordinary-bettor comparators it has no valid enrichment probability or insider-trading classifier.
5. **A specific internal value path is distinguishable from service usage.** The same amount, 9,990.027385 USDC, enters intermediary 0x12d5b13f… from a Relay router on 13 January and leaves it for a Relay router 22 seconds later; source and destination Relay histories associate the sequence with flipfloppity and the proxy provisionally named Anon. The time and exact token route support a direct value path. They do not establish who controlled both trading accounts.

## Audit decision

**Retain** the 38 proxy inventory, the 36-account trading sequence, the 32 direct Polygon transfers, the 12 individually amount-matched Polygon Relay deliveries and the 1,984,038.168550-USDC gross balance reconciliation.

**Downgrade** "38 financially proven to one Coinbase customer account" to **35 supported Polygon payout paths, one additional Arbitrum observed recipient payment and two Base orders reported by Relay but not replayed**. Treat Coinbase as a **service attribution hypothesis supported by labels and sweeps**, not as a first-party confirmed customer account. The group may be coordinated, but this corpus alone neither proves one owner nor access to nonpublic information.

## Reproduction

The offline verifier is [verify.py](verify.py). Run it from the repository root with Python 3.12 in isolated mode. Its negative tests are in [test_verify.py](test_verify.py).

The verifier reads the original account CSV, per-account trading ledgers, the 86 recorded entry orders, the Polygon and Arbitrum ERC-20 logs and the relevant Relay request snapshots. It checks exact contract addresses, 6-decimal atomic amounts, distinct proxies, matching transaction values and the unverified cases. Its matching test rejects situations in which sums agree but individual transfers do not. Passing means **the committed archived files agree with this stricter account of the evidence**; it does not replace live independent RPC replay, Coinbase records, or a prospective control experiment.

The Relay provider's own [transaction tracing guide](https://support.relay.link/en/articles/11628584-using-a-block-explorer-to-track-your-wallet-activity-a-step-by-step-guide-for-relayers) distinguishes origin deposits, solver fills and recipient wallets. Its [recipient explanation](https://support.relay.link/en/articles/9260724-how-do-i-find-my-transaction) likewise distinguishes the destination address from a Relay settlement wallet.
