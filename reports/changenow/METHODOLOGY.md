# Method of the weekly ChangeNOW and Polymarket flow report

Code: [`monitoring/changenow_weekly/`](../../monitoring/changenow_weekly/). Tests: [`monitoring/tests/test_changenow_weekly.py`](../../monitoring/tests/test_changenow_weekly.py). Every figure of a weekly report is rebuilt from public chain data by the commands at the end of this page.

## 1. What is measured

The report lists Polymarket trading wallets for which a movement of funds from, or to, an address attributed to ChangeNOW was read on public chains, hop by hop, during one ISO week (Monday 00:00:00 UTC to the next Monday, end excluded).

It measures flows between the service's infrastructure and a trading wallet. It does not measure exchange orders. ChangeNOW does not publish its orders, a payout wallet serves every product built on the same infrastructure, and one payout can be a swap ordered by the account holder, a payment sent by someone else, or anything else the service pays. An address labelled ChangeNOW therefore never proves an individual order here.

Using ChangeNOW is lawful and common. Nothing in the report is evidence of inside information or of any offence. A public name is a pseudonym, a key is not a person, and two wallets served by the same service are not thereby under one control.

## 2. Window, settled blocks, provisional and frozen weeks

For each network the week is turned into a block range: the first block at or after the start, found by bisection on block times, to the last block before the end. While the week is open the range stops at the last settled block: the node's `finalized` block, or the head minus a fixed depth where the node has no such tag. Nothing younger is read, so no reorganisation has to be undone later.

A report written before every network has passed the end of the week is `PROVISIONAL` and says, per network, the block and time it stops at. The next run reads only the new blocks and rewrites it. Once the week is closed on every network the report is `FROZEN`: a `SHA256SUMS` file lists every file of the week, the tool refuses to write that week again, and a test fails if a frozen file changes, appears or disappears.

## 3. Register of ChangeNOW addresses

File: [`registry.csv`](../../monitoring/changenow_weekly/registry.csv). Evidence for unlabelled addresses: [`registry_evidence.json`](../../monitoring/changenow_weekly/registry_evidence.json). The label snapshot comes from the earlier investigation [`changenow-outflows`](../../investigations/changenow-outflows/), which is not modified.

| Tier | Meaning | Used for a confirmed flow |
|---|---|---|
| `A_LABELLED` | A public explorer or label list names the address as ChangeNOW. Label sources are grouped by lineage (Etherscan tags and their copies, the OLI and hildobby compilation, Blockscout name tags), because lists copy one another: the count kept is the number of independent lineages, not of lists | Yes, in a week where its measured role is a service role |
| `B_STRUCTURAL` | No public label. The address was funded by a tier A address within a day of its own first transaction (transaction hashes kept), and behaves as a service wallet in the measured week | Yes, same condition, and the tier is shown on every row that depends on it |
| `C_SUSPECTED` | One weak source, or behaviour alone | No |
| `X_NOT_SERVICE` | Carries the word ChangeNOW without being a wallet the service controls: its token contract, a third party's deposit, or the service's own deposit address at an exchange, whose key the exchange holds | No |

A label says who, never what for. The function of each registered address is measured again every week from that week's transfers, in recognised tokens only:

| Measured role | Rule over the week |
|---|---|
| `PAYOUT_HOT` | At least 100 value transfers to at least 50 recipients, at least half of them served once |
| `GAS_FUNDER` | Same shape, at least 90 % native transfers, and at least half of its recipients then paid a token into a registered address |
| `CONSOLIDATION` | At least 20 transfers to at most 20 recipients, or one recipient with half of them |
| `COLLECTOR` | Receives at least 20 transfers and sends none |
| `LOW_ACTIVITY` | Anything else |

Only `PAYOUT_HOT` addresses of tier A or B are payout sources. A consolidation or treasury wallet is internal plumbing: its transfers are counted and set aside.

**Labels are read again.** `python3 -m changenow_weekly registry --raw <folder>` reads today's public tags from Blockscout's metadata service for every registered address, and for the outside addresses that dealt with the service often during the week (several payments into its wallets, or among its most paid recipients). What it found is kept in [`registry_labels_refresh.json`](../../monitoring/changenow_weekly/registry_labels_refresh.json). An address that carries a ChangeNOW name tag there and is absent from the snapshot is added with tier A and that single lineage. The service's own list is not walked: more than 20,000 Ethereum addresses carry its ChangeNOW protocol tag, nearly all of them one-time deposit addresses. When the register changes, the week is read again from its first block, because an address added later would otherwise miss its transfers in the blocks already read.

**One-time deposit addresses** are never labelled one by one. An address is treated as a ChangeNOW deposit address of the week when it paid into a payout source during the week and either received its gas from the measured gas funder, or is a plain key that signed at most two transactions in its life. The transaction by which it swept into the service is part of the evidence of every withdrawal.

## 4. Collection

Everything is read by block window from public JSON-RPC nodes, with no key: every ERC-20 `Transfer` from or to a registered address, and on Polygon every native move, which leaves a log there. A window halves when a node refuses its size, and the list of windows actually read is kept, so the block coverage in `COVERAGE.md` is measured. Ranges on disk must be contiguous: a hole is an error.

Native transfers on Ethereum leave no log. They come from Etherscan lists when `ETHERSCAN_API_KEY` is set, with two guards added after real failures. A page is never taken as the last one because it is short: on 2026-11-14 the service returned 996 rows in the middle of a list, and one block held more than 1,000 rows for one address, so the reader restarts at the last block seen until a page comes back empty and pages inside a block when it must. And the number of transactions signed by each address in the list must equal the movement of its account nonce over the same blocks, or the run stops.

On Base the keyless node used for the block scan serves 1,000 blocks a call, and a week there is about 2.8 million blocks. Transfers into the deposit addresses are therefore read from a second public node, which serves 50,000 blocks a call when the filter names at most ten token contracts: the read names the tokens these addresses swept into the service during the week. On 2026-11-15 both reads were made over the same 2,777,080 blocks for the same 1,241 addresses and gave the same 1,276 rows in recognised tokens.

A refusal by a node or an API raises. It is never turned into an empty result. Raw rows and checkpoints stay outside the repository.

## 5. Customer-facing flows

- **Payout**: a value transfer from a payout source to an address that is not registered, not one of the service's deposit addresses and not the zero address.
- **Customer deposit**: a value transfer into a one-time deposit address from an address that is not part of the service.

Transfers in tokens that DeFiLlama does not price with confidence 0.9 or more are not recognised. That removes the look-alike tokens that copy a symbol or forge a `Transfer` from a known address. They are counted, never valued.

## 6. Polymarket accounts

An address is a trading wallet when its bytecode and the official contracts say so (Deposit Wallet of the official factory or beacon, Safe predicted by the official Safe factory, clone of the official proxy implementation). The classifier is the one archived in [`investigations/polysentinel`](../../investigations/polysentinel/sources/signal_engine/fund_flow/wallets.py).

A key owns a wallet when the chain says so: `owner()` of the Deposit Wallet derived from the key returns that key, `getOwners()` of the Safe predicted for the key lists it, or a clone is deployed at the address the legacy exchange derives for it. Every payout recipient and every deposit sender of every network read is tested this way.

The public name and the activity of a confirmed account come from Polymarket's own public APIs (`gamma-api` profile, `data-api` activity). The activity feed does not list plain transfers between a wallet and its key, so deposits and withdrawals are read from chain logs, not from the feed.

## 7. Tracing

One walker serves both directions. It starts from a transfer whose sender must be explained and walks backward, one transfer at a time, to an origin: a ChangeNOW payout source for a funding, a trading wallet for a withdrawal.

| Step | Accepted when |
|---|---|
| Collateral conversion | One transaction holds both legs with the same amount: USDC.e paid into the collateral contract and pUSD minted, or the reverse |
| Relay order | The solver's payment carries an order id in its calldata and the escrow contract logged the same id on the origin chain, with depositor, token and amount. This is the protocol's own record, read on both chains, with no API |
| Pass-through address | Its latest inflow of that asset covers the outflow and it held almost nothing before (1 % tolerance for a token, 5 % for a native coin that pays gas). Otherwise funds are mixed and the walk stops |
| Tracked recipient | The address received ChangeNOW payouts (funding) or transfers from a trading wallet (withdrawal) before the outflow: the lower bound below applies |

**Lower bound for mixed funds.** For an outflow `x` of an address that received tracked money, with balance `b` just before the first tracked inflow and other inflows `o` between it and the outflow, the attributed part is `max(0, x - b - o)`, capped by the tracked money not already attributed. Only what other money could not have covered is attributed. The bound is split first-in first-out over the tracked transfers, and each transfer can be used once, across all walks of the week.

A walk stops at the first step it cannot prove and records the reason. It never bridges a gap with an amount or a time.

Funding is searched from three starts: a payout straight into a trading wallet, any collateral sent on Polygon by a payout recipient of any network (a recipient on Ethereum or Base that bridged and wrapped), and every outside credit of a wallet owned by a recipient. Withdrawals are searched from every deposit into a ChangeNOW address made by a trading wallet, by a sender that received collateral from a trading wallet, or by a bridge solver.

## 8. Levels

| Level | Assigned when | Published |
|---|---|---|
| `CONFIRMED` | Every hop is a transaction read from the chain, every bridge hop carries the protocol's order id on both sides, and the ChangeNOW end is a tier A or B address in its measured role | Main ranking |
| `PROBABLE` | The key that dealt with ChangeNOW owns the wallet, and money was read moving between that key and its wallet on the relevant side of the ChangeNOW transfer, but the continuity of the same funds is not shown | Separate table, upper-bound amounts, never added to the confirmed totals |
| `HYPOTHETICAL` | Key ownership and timing only | `candidates.csv`, not ranked |
| `REFUTED` | A walk reached a proven origin of another kind: the credit was paid by something else | Counted in `COVERAGE.md` under walks `NOT_ORIGIN` |

## 9. USD value

Each event is valued at its ChangeNOW-side transaction: the attributed quantity, in the token's own units, times the DeFiLlama price of that token contract nearest to the block time, refused when further than one hour. The price and its own timestamp are written on each row. No stablecoin is set to 1 by rule. Population totals in `COVERAGE.md` use one price an hour for tokens with at least 20 transfers.

## 10. Ranking

One event is one attributed part of one ChangeNOW-side transfer. Intermediate hops are references of the event, not events, so the same funds are not counted at each hop. The transaction count of an account is the number of distinct ChangeNOW-side transfers. Gross volume is inflows plus outflows; a funding and a later withdrawal of the same account are two events. Net flow is inflows minus outflows and is not a profit or a loss. Accounts are ranked by gross volume, then by address.

`PATTERNS.md` is descriptive and separate from the ranking. Besides counts made on the confirmed events themselves, it shows two readings of Polymarket's public activity feed: the trades of an account in the 24 hours after a funding reached its wallet, and its redemptions (payouts of resolved markets) in the 24 hours before a withdrawal left it. Resolution times are not read.

## 11. Automation

`python3 -m changenow_weekly run` is incremental and can be stopped and restarted. The workflow [`changenow-weekly.yml`](../../.github/workflows/changenow-weekly.yml) runs it every six hours and on demand, runs the tests, and pushes the regenerated report to the branch `data/changenow-weekly`, with a pull request to `main`. It never pushes to `main`. A local equivalent is in [`monitoring/changenow_weekly/local/`](../../monitoring/changenow_weekly/local/).

## 12. Reproduce

```sh
cd monitoring
python3 -m unittest tests.test_changenow_weekly -v                 # offline
export ETHERSCAN_API_KEY=...                                       # optional, free plan: adds Ethereum native transfers
python3 -m changenow_weekly run --raw ~/changenow-raw --week 2026-W46
python3 -m changenow_weekly reconcile --week 2026-W46              # read every published transaction again, by hash
python3 -m changenow_weekly verify                                 # checksums of frozen weeks, offline
```

Public nodes answer differently from day to day. A rerun reads the same settled blocks, so it must give the same events; a node that no longer serves a range makes the run stop, not shrink.

## 13. Limits

- The register knows the wallets that public labels and creation ties reveal. Unlabelled payout wallets on other networks exist and are absent.
- Networks and assets not read are listed in each `COVERAGE.md`. Solana, Tron, Bitcoin and Monero are never read.
- The other side of each swap inside the service is not public.
- A path that changes asset outside the conversions above stops as unresolved.
- Amounts are lower bounds where funds were mixed.
- A week's report can never claim to list every user of the service on Polymarket.
