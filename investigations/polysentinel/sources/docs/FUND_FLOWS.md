# Fund flows

A read-only module that follows a Polymarket wallet's collateral in both directions, in shadow mode. No category, score or threshold reads it. It holds no key, sends no transaction, and names no person.

```sh
python -m signal_engine.fund_flow.trace WALLET --pages 8 --scan-days 2 --rpc 400 --http 30 --out result.json
```

## Wallet types

| Type | How it is recognised | Signer |
|---|---|---|
| EOA | No contract code, or an EIP-7702 delegation | The address is its own key; its holder is unknown |
| Gnosis Safe | `getOwners()`; the official factory's `computeProxyAddress` confirms a Polymarket Safe | Owners read on-chain |
| Polymarket Proxy | Clone of the official factory's implementation | `SIGNER_UNKNOWN`, unless a candidate from calldata derives to it by CREATE2 and the official exchange's view agrees |
| Deposit Wallet | ERC-1967 or beacon proxy carrying the official factory or beacon, with `owner()` | Owner read on-chain; session signers are not listed |

The address that submits a transaction is a relayer or a bundler until something else shows otherwise. A proven signer is a key, not a person.

## Following value

Logs are followed one by one, by exact amount and in log order, so one transaction carrying several strangers' deposits credits only the funder of this wallet. A mint is traced to whoever paid the collateral into pUSD. If two equal amounts could pair differently, the relation says `INSUFFICIENT_EVIDENCE`. Each transfer keeps chain, transaction and log index.

An address that nets zero on every token only passed funds on, and one that also gains another token is a pool. The funder is then the one address that only lost tokens in the transaction. It can be the transaction's submitter: submitting neither proves nor rules out being a party. With no such address or several, no origin is named.

`raw` says what it measures through `raw_meaning`: what the target received, or, on a cross-chain relation, what left the sender, with `received_raw` for what arrived.

## States

| State | Means |
|---|---|
| `ONCHAIN_CONFIRMED` | Shown by logs of one confirmed transaction |
| `PROTOCOL_LINK_CONFIRMED` | One order id on both sides. For Relay, the id at the end of the payout's calldata equals the id in the escrow log on the origin chain, read from public chain data, the payout was made by the documented solver, since anyone can append a copied id, and the payer is the transfer that escrow log accounts for |
| `SERVICE_INTERACTION` | Reached or came from an address a cited source attributes to a service. On an inflow the service is the payer on-chain, not the funder: `funder_shown` is false |
| `CROSSCHAIN_CANDIDATE` | Fits by amount and time, or by a record with no shared identifier; never a link |
| `OFFCHAIN_RECORD_REQUIRED` | Only the service's internal record could settle it |
| `XMR_VISIBILITY_BOUNDARY` | The trail stops at Monero; nothing tries to read past it |
| `INSUFFICIENT_EVIDENCE` | Not enough to say |

ChangeNOW keeps four levels: a transaction to a labelled address, a plausible match by time and amount, a match supported by an exchange id verified on both chains, and a match that cannot be shown. ChangeNOW publishes no address list, so without a sourced label the first level is unreachable. A record reaches the third level only if someone entitled to it supplied it and both hashes check out. This code calls no ChangeNOW route and holds no API key.

A Monero proof is checked only through the user's own local wallet RPC. Spend keys, seeds and passwords are refused, and no key is stored. A verified proof shows that an address received an output, and it links to no EVM flow. A later exit on a transparent chain stays an independent observation.

## Accounting

Two calculations are kept apart: transfer logs against on-chain balances, per token in raw units, and the activity API's cash by type against the same balances. Whatever they cannot explain stays as a residual. A consolidated account counts a transfer between its own wallets once, as internal. Trading cash flow is not a profit: open positions are not valued, and deposits and withdrawals are neither gains nor losses.

Public nodes serve fewer than 10,000 blocks per log call, so a long-lived wallet may exceed the request budget. The result then says `NOT_SCANNED` and the API figure is marked as incomplete.

## Graph and groups

Every edge carries addresses, chain, amount, time, hash, log index, source and state. An address has a kind only from a cited label; otherwise it stays `UNKNOWN`. Twenty or more counterparties in one graph mark it `POTENTIAL_INFRASTRUCTURE`, a question and not a classification. Grouping needs on-chain control or money going both ways between two non-infrastructure addresses. One payment or a shared service never groups anyone, and each group lists its evidence and alternatives, with `OWNERSHIP_NOT_ESTABLISHED`.

## Limits

- Bridge records returned by Polymarket's status route carry hashes that were not found on the stated chains, so they stay candidates. They also name no origin sender.
- Inbound Relay payments can be proved on-chain, as above. Outbound ones mostly cannot: Relay's status route does not know the withdrawal ids tested, its full request route needs an API key, and a search of its documented solver's transfers on five chains found no payout for the three largest orders tried. Those withdrawals stop at the depository with `OFFCHAIN_RECORD_REQUIRED`, which does not mean that no payout exists. The older public route, kept as a fallback, is due to retire on 24 November 2026.
- "Kept nothing" is measured on ERC-20 logs. Receipts do not show native value moved by calls, so a router could have kept native value unseen.
- Labels are what a source said on the checked date, and they are incomplete. Exchange deposit addresses are not covered.
- ERC-1155 position transfers, splits, merges and redemptions are counted from receipts and the activity API, not rebuilt into a position history. Native POL movements are decoded from receipts only, not scanned.

## Accidental matches

Measured with `python -m signal_engine.fund_flow.controls`, seed 20261101, on 1 November 2026.

| Control | Result |
|---|---|
| Every USDC.e transfer in 8 windows of about 3 minutes (63,967 transfers, 400 draws of real withdrawal amounts) | At least one unrelated match: 42 % within 0.1 %, 61 % within 1 %, 86 % within 10 % |
| 322 withdrawals against other wallets' deposits within 6 hours, among 87 investigated wallets | Real dates 35, dates moved by days 7 (2.2 %) |
| Same rule within 1 % | Real dates 16, moved 4 (1.2 %) |
| 40 deposits against their sender's bridge records | Real dates 11, dates moved by days 0, another sender's records 0 |

The chain-wide figure is why amount and time never make more than a candidate. The other rows are low estimates over sparse, selected sets. Zero out of 40 still allows a rate of up to about 9 %, and the excess on real dates does not show that those matches are true links, because activity clusters in time.
