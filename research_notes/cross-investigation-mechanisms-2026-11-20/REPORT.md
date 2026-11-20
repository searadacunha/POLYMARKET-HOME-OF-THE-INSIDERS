# Seven money mechanisms seen in several investigations

**Date:** 20 November 2026. **Scope:** the financial findings already published in this repository, read across investigations. **Status:** descriptive synthesis. No new chain data was collected; every case below is quoted from the report cited for it, and `verify.py` checks that the quoted sentences are written there.

A mechanism shared by two cases is a shared way of moving money. It is not a link between the cases, not a common owner and not evidence about information. Populations, periods and amounts of different cases are kept apart here and must not be added up.

## Result

Seven mechanisms recur across 13 cases of the repository:

1. **A. The withdrawal of one account becomes the deposit of another** (7 cases). Directly (same transaction hash), through a Relay order to an intermediary key, or through the receiving account's own deposit address; the credit follows within 18 to 50 seconds (A1) to about 19 minutes (A3).
2. **B. Several accounts pay one shared destination address** (6 cases). In most cases it behaves as an exchange customer deposit address, which points to an exchange account, not a person; for B4 no exchange is identified.
3. **C. One source funds several newly created accounts** (3 cases), plus one contrast that is not counted: the 38-proxy Iran cohort shows no funding wallet used by two of its accounts in the observed data.
4. **D. Several accounts consolidate into one wallet** (3 cases).
5. **E. Exits across chains through bridges** (3 cases), most often towards Solana.
6. **F. A privacy pool before or after the bets** (2 cases); neither is attributed coin by coin.
7. **G. EIP-7702 accounts that only forward** (2 cases): delegated to the same contract, relayed by the same relayer and paying the same key, read by their source as one unidentified service, not shown to be one customer.

Iran cluster E (A, B, E, F, G) and Inca Digital's five June 2025 Iran wallets (A, B, E, G) combine the most mechanisms; the Nobel second group (A, C, D) combines three; KPMG earnings markets (A, B), Iran 38-proxy cohort (A, B), Venezuela regime-change markets (C, F) and Nobel 2025 market (C, D) combine two each.

Of the full addresses written in the reports, 54 addresses are named by two or more folders. Eight of them, which connect different investigations or notes, are listed below; five of them are named by both the Inca cross-check and the cluster E note: the two accounts in both lists, the cluster E forwarding wallet, the key that both forwarding wallets pay, and their common delegate contract.

## A. The withdrawal of one account becomes the deposit of another

A Polymarket account withdraws, and the amount arrives as the deposit of another account: directly, through a Relay order, or through the receiving account's deposit address. The receipts show a payment between two accounts; they do not show why it was made or who controls either account.

<!-- table:A -->
| # | Case | Population | What the source records | Level in the source | Source |
|---|---|---|---|---|---|
| A1 | KPMG earnings markets | 22 accounts of Bitquery's published analysis | 14 withdrawals of one account became the deposit of another, matched by Relay keys on Polygon and Solana, 18 to 50 seconds apart | CONFIRMED in the source | [financial-links-replay-2026-11-07/REPORT.md](../../research_notes/financial-links-replay-2026-11-07/REPORT.md) |
| A2 | Iran cluster E | 19 accounts of the February 2026 Iran strike markets | accounts paid other accounts directly or into the receiving account's own deposit address, which converts the amount for that account (39 seconds later in the example quoted) | as recorded in the source | [iran-cluster-e-network-2026-11-05/REPORT.md](../../research_notes/iran-cluster-e-network-2026-11-05/REPORT.md) |
| A3 | Inca Digital's five June 2025 Iran wallets | two of the five, 11 June 2025 | DonkeyDonkey999's three withdrawals paid an address that behaves as 9TungSahur's deposit address, credited 98.8 % about 19 minutes later | L2 in the source | [inca-crosscheck-2026-11-06/REPORT.md](../../research_notes/inca-crosscheck-2026-11-06/REPORT.md) |
| A4 | Iran 38-proxy cohort (G38) | two accounts of the cohort | flipfloppity withdrew about 9,990.03 USDC through Relay to an intermediary key whose value path continued into a Relay deposit for the account provisionally named Anon | funding path, not shared control, in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| A5 | Maduro/Iran eight-account network | eight financially connected accounts | funding relationships such as chileno777 to TacticalInsiderNews, on Polygon, Ethereum and TRON | as recorded in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| A6 | Pulser, cashy and Car | matched control population of the June 2025 Iran market | 25 matched-hash payments between Pulser and cashy, 13,449.999999 USDC combined over both directions | inside a control population, in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| A7 | Nobel second group (NB-2) | one established account and two accounts opened on 10 October 2025 | the established account's withdrawals reached a hub key, then a new key, then a new account, within two minutes; leftovers came back by direct transfers between accounts | transfers verified; common control of the three strongly supported, in the source | [NEW_LEADS.md](../../NEW_LEADS.md) |
<!-- /table -->

## B. Several accounts pay one shared destination address

Withdrawals of several accounts reach one address that sweeps its balance onward, in most cases to an exchange hot wallet with gas from the exchange. Such an address points to one exchange customer account, not to a person, and the receipts do not show whether that customer is one of the traders. For B4 the sources establish no named exchange.

<!-- table:B -->
| # | Case | Population | What the source records | Level in the source | Source |
|---|---|---|---|---|---|
| B1 | Iran 38-proxy cohort (G38) | 38 proxies, 5 January to 9 March 2026 | 32 proxies transferred to one Polygon address that sweeps to addresses bearing Coinbase tags | common customer UNRESOLVED in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| B2 | Venezuela and Iran histories | Frogensky, JamWil23 and bravonoll | three accounts of two market families withdrew to one Ethereum address that sweeps to Coinbase Hot Wallet 10 | common destination, not a common trader, in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| B3 | KPMG earnings markets | 22-account cohort | 7 withdrawal destinations shared by several accounts, all behaving as exchange customer deposit addresses | as recorded in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| B4 | Biden pardon market | two trading proxies | 25 cashouts of the two proxies reach one Polygon address, which another payer also used | not exclusive; no named exchange established, in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| B5 | Inca Digital's five June 2025 Iran wallets | three accounts of the February 2026 network, 13 June 2025 | 65,992.25 USDC paid into one Bybit-classified deposit address within 45 minutes | as recorded in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| B6 | Iran cluster E | 19 accounts of the February 2026 Iran strike markets | Binance, Bybit and Crypto.com customer deposit addresses each used by several accounts of the network | classification partly by labels (erratum) | [iran-cluster-e-network-2026-11-05/NEW_FINDINGS.md](../../research_notes/iran-cluster-e-network-2026-11-05/NEW_FINDINGS.md) |
<!-- /table -->

## C. One source funds several newly created accounts

One wallet, or one tree of wallets, pays the first deposits of several newly created accounts. C4 is a contrast, not a case: it records that the entry side of the 38-proxy cohort does not show this mechanism.

<!-- table:C -->
| # | Case | Population | What the source records | Level in the source | Source |
|---|---|---|---|---|---|
| C1 | Venezuela regime-change markets (Railgun tree) | 71 single-bet accounts, December 2025 to January 2026 | Railgun unshields to six distributors, 384 children, 71 Relay deposits each crediting a new account; the tree is closed | verified tree, operator unknown, in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| C2 | Nobel 2025 market (C7) | eight accounts funded by the owner key of the 6741 Safe, one night (the seven others have their own owner keys) | one key sent 372,521.54 USDC to eight accounts | CONFIRMED in the source | [followup-20261113/FINDINGS.md](../../investigations/followup-20261113/FINDINGS.md) |
| C3 | Nobel second group (NB-2) | one established account and two accounts opened on 10 October 2025 | the established account's withdrawals funded two brand-new accounts through a hub key and brand-new keys, within two minutes | transfers verified; common control of the three strongly supported, in the source | [NEW_LEADS.md](../../NEW_LEADS.md) |
| C4 | Iran 38-proxy cohort (G38), contrast not counted | entry side of the 38 proxies | 86 deposits from 39 funding wallets, none used by two accounts in the observed data; a private common funder is refuted on the wallets read and unresolved for 19 on unread chains | as recorded in the source | [financial-links-replay-2026-11-07/REPORT.md](../../research_notes/financial-links-replay-2026-11-07/REPORT.md) |
<!-- /table -->

## D. Several accounts consolidate into one wallet

The balances of several accounts end in the same wallet. In the two Nobel cases it is the wallet or the account that funded them (C2, C3).

<!-- table:D -->
| # | Case | Population | What the source records | Level in the source | Source |
|---|---|---|---|---|---|
| D1 | Anthropic ticker market (XFM) | 37 numbered accounts, 15 October 2026 | 37 accounts withdrew to two collector wallets in numeric order within 46 minutes | consistent with volume or incentive farming, in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| D2 | Nobel 2025 market (C7) | the same eight accounts | all 16 Relay withdrawals of the eight accounts went back to the funding key or to the 6741 proxy | CONFIRMED in the source | [followup-20261113/FINDINGS.md](../../investigations/followup-20261113/FINDINGS.md) |
| D3 | Nobel second group (NB-2) | one established account and two accounts opened on 10 October 2025 | leftovers and winnings of the two new accounts went back to the established account, twice by direct transfer | transfers verified; common control of the three strongly supported, in the source | [NEW_LEADS.md](../../NEW_LEADS.md) |
<!-- /table -->

## E. Exits across chains through bridges

The money leaves the account's chain (Polygon, or Ethereum for E3) through a bridge order and reaches a wallet on another chain, most often Solana.

<!-- table:E -->
| # | Case | Population | What the source records | Level in the source | Source |
|---|---|---|---|---|---|
| E1 | Iran cluster E (Solana beneficiary) | four accounts, February 2026 | 11 Relay orders delivered SOL to one Solana wallet, which sent most of it to a Bybit-classified deposit address | as recorded in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| E2 | Inca Digital's five June 2025 Iran wallets | ricosuave666's exit wallet, June to September 2025 | four Solana-bound bridge orders (Mayan, LI.FI, deBridge) name one receiver, which later burned USDC through CCTP back to the exit wallet | confirmed in the source | [inca-bridged-exits-2026-11-06/REPORT.md](../../research_notes/inca-bridged-exits-2026-11-06/REPORT.md) |
| E3 | Ballon d'Or 2026 (account 0xa8e6) | the owner key of one account | an Ethereum payment was bridged by Relay to Monad and minted as vault shares to a beneficiary | as recorded in the source | [relay-followup-2026-11-04/REPORT.md](../../research_notes/relay-followup-2026-11-04/REPORT.md) |
<!-- /table -->

## F. A privacy pool before or after the bets

<!-- table:F -->
| # | Case | Population | What the source records | Level in the source | Source |
|---|---|---|---|---|---|
| F1 | Venezuela regime-change markets (Railgun tree) | the same 71 accounts | the tree starts with Railgun unshields to fresh distributor wallets | verified tree, operator unknown, in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
| F2 | Iran cluster E (Solana beneficiary) | the Solana beneficiary | a Privacy Cash withdrawal followed a deposit of the beneficiary | not attributed, in the source | [VERIFIED_FINANCIAL_FINDINGS.md](../../VERIFIED_FINANCIAL_FINDINGS.md) |
<!-- /table -->

## G. EIP-7702 accounts that only forward

An ordinary key is delegated to a smart-account contract and used as a forwarding wallet. The two wallets below, of June 2025 and February 2026, are delegated to the same contract `0x0000fb7702036ff9f76044a501ac1aa74cbab16b`, got their gas from the same relayer and send their outflows to the same key; the Inca cross-check reads them as wallets of one unidentified service and states that customer-specific use is not established.

<!-- table:G -->
| # | Case | Population | What the source records | Level in the source | Source |
|---|---|---|---|---|---|
| G1 | Iran cluster E | one forwarding wallet of the network | an EIP-7702 account that receives from six accounts of the network and Binance and sends everything to one address | as recorded in the source | [iran-cluster-e-network-2026-11-05/NEW_FINDINGS.md](../../research_notes/iran-cluster-e-network-2026-11-05/NEW_FINDINGS.md) |
| G2 | Inca Digital's five June 2025 Iran wallets | one wallet paid by 9TungSahur, 13 June 2025 | an EOA delegated through EIP-7702 to the same contract as the cluster E wallet, gas from the same relayer, all outflows to the same key | same unidentified service, customer-specific not established (L3u), in the source | [inca-crosscheck-2026-11-06/REPORT.md](../../research_notes/inca-crosscheck-2026-11-06/REPORT.md) |
<!-- /table -->

## Addresses named by the reports of two or more folders

Full addresses (40 hexadecimal digits that are not the start of a longer hexadecimal string, so that transaction hashes are not counted) written in the 188 Markdown reports of `investigations/` and `research_notes/` at 0b0882c, outside the `sources/` copies, were indexed by folder. Of the 200 distinct full addresses written in those reports, 54 appear in two folders or more. Most are exchange customer deposit addresses, Polymarket accounts or their keys, named by several notes of the same investigation; fewer than ten are contracts, relayers or hot wallets. The table lists eight that connect different investigations or notes.

| Address | Folders whose reports name it | What they record |
|---|---|---|
| `0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a` | `research_notes/inca-crosscheck-2026-11-06`, `research_notes/iran-cluster-e-network-2026-11-05` | 9TungSahur (later TheOneWhoKnocks1312), one of Inca Digital's five June 2025 wallets and an account of the February 2026 cluster E network |
| `0xcb18ea2923d957bd9cf049cce60a87638722f867` | `research_notes/inca-crosscheck-2026-11-06`, `research_notes/iran-cluster-e-network-2026-11-05` | DonkeyDonkey999, the second exact intersection of the same two lists |
| `0xa6c221448af73af8350291c5cdcd877b39683766` | `research_notes/inca-crosscheck-2026-11-06`, `research_notes/iran-cluster-e-network-2026-11-05`, `research_notes/iran-solana-beneficiary-2026-11-05` | the cluster E forwarding wallet of mechanism G (G1) |
| `0x852dc1c875f0117ea0808610010893e4c576b6a9` | `research_notes/inca-crosscheck-2026-11-06`, `research_notes/iran-cluster-e-network-2026-11-05`, `research_notes/iran-solana-beneficiary-2026-11-05` | the unlabeled, very active key to which both forwarding wallets of mechanism G send; it also paid a Binance deposit address of the network once in June 2025 |
| `0x0000fb7702036ff9f76044a501ac1aa74cbab16b` | `research_notes/inca-crosscheck-2026-11-06`, `research_notes/iran-cluster-e-network-2026-11-05` | the contract to which the two forwarding wallets of mechanism G are delegated |
| `0x4ec2f11d2893eb1bc3bab7449910540c93adf7ec` | `investigations/collective-exposure-shifts`, `research_notes/iran-cluster-e-network-2026-11-05` | arsonicscribe, a member of group G of the cluster E note, cited in the collective-exposure investigation as an account that traded 8 deadlines |
| `0x8f42ae0a01c0383c7ca8bd060b86a645ee74b88f` | `research_notes/iran-pulser-cashy-crossmarket-2026-11-06`, `research_notes/x-history-2026-11-06` | cashy, in the June 2025 control population and in the X claims about February 2026 checked by the X-history note |
| `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | `investigations/changenow-proof`, `investigations/followup-20261113` | an address of unknown owner that pays 291.317423 USDT to the key of the Ballon d'Or account brace227 (link to the service UNRESOLVED); a ChangeNOW payout to it is the output of an order it paid on Base |

Two reports naming the same address is a fact about the reports. It links two investigations only through what each report records about that address.

## Notes not yet merged

Two open pull requests add cases to mechanisms A and G: PR 103 reads a payment of 1,000 USDC on 16 June 2026 from an account of the Iran reference population towards the deposit route of `0x1fa1be3e...` (listed as `MAGAMESSI`), an EIP-7702 account delegated to another contract; PR 99 traces the Nobel funder's treasury to `0x0D40D7Cb...`, also an EIP-7702 account. They are not counted above, because their files are not in this repository yet.

## What is not shown

- That two cases sharing a mechanism are linked. Exchange deposit routes, Relay orders, bridge orders and smart-account contracts are used by very many unrelated people.
- Who controls any account or address of the tables, or that anyone traded on non-public information.
- How common each mechanism is among ordinary traders. No base rate is computed here; the cases were selected by the earlier investigations, most of them from winners or from public reports.
- Totals across cases. The figures quoted belong to different populations, periods and accounting conventions.

## Reproduce

```sh
python3 -I research_notes/cross-investigation-mechanisms-2026-11-20/verify.py   # offline, 13 checks; needs a full clone
```

`verify.py` checks that every quoted sentence of [data/instances.csv](data/instances.csv) is written in its cited report, that the seven tables above are the rendering of that file, that the counts of the Result, the list of cases that combine mechanisms and the overlap count match it, recounts the address index from the Git objects of 0b0882c with the strict address pattern, checks that every address of the table is written by each folder listed for it, and that the checks fail on a forged quote, a transaction hash that starts like an address, or a rendering that would swallow text between tables. `verify.py --write` re-renders the tables.

## Limits

- The synthesis reads the published reports, not the chain. A case is as strong as its source, whose level is copied in the tables.
- The address index reads only full addresses written in Markdown reports; shortened addresses and data files are not indexed, so it is a floor, not a census.
- Mechanisms were assigned by reading. Another reader could split them differently; the KPMG funding wallets, for example, are each recipient's own single-use wallet and are counted under A1, not under C.
- Each quote is checked in the working tree. If a cited report is later corrected, `verify.py` fails until this note is updated.
- An independent claims audit rated the first version FAIL on nine points (among them an address index that counted transaction hashes as addresses); its corrections are applied here and were not audited a second time.
