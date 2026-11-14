# Sources and tools, re-evaluated on 14 November 2026

What each public source or open-source tool gives today, what it costs, and whether this project uses it. "Probed"
means that a request was sent on 14 November 2026 and the answer read. Nothing was installed and no third-party code
was run. No key was created and nothing was paid.

## Decisions

| Source or tool | What it gives | Limits found | Licence | Probed | Decision |
|---|---|---|---|---|---|
| Polymarket data API v2, `trades` by market with a size filter | every fill of 1,000 USD or more of a market since it opened, with the wallet, in one request for most markets | newest first; a few rows a little under the nominal size; no maker or taker flag | terms of the venue | yes: 32,552 markets read | **Used**: the population of the study |
| Same route without a market | the same for the whole venue | stops at 1 October 2026 00:00 UTC; answers from a 5-minute cache | | yes | Used for description only |
| Data API v2, `activity` of a wallet | trades, deposits, withdrawals, with the transaction of each deposit | 1,000 rows a page; the deposit shown is often a swap, not the funding transfer | | yes: 38,976 wallets read | **Used** |
| Gamma event and market catalogue | markets, tags, scheduled end, outcome | a listing of closed events hides the closed markets of events still open (10,505 on 14 November) | | yes | **Used**, with the open events added |
| Polygon public nodes, receipts | the logs of one transaction | one node answers `null` for receipts it does not hold; batches of 25 accepted by one node, 15 by another | | yes: 24,776 receipts | **Used** |
| Polygon public nodes, old logs over a range | transfers received by an address | one public gateway serves old ranges (five requests a call, one call a second); the others refuse them or have no archive | | yes | **Used**, at that pace |
| Blockscout public name tags | which addresses are bridges, exchanges, pools | a missing tag proves nothing | public service | yes: 3,705 addresses | **Used**; an address whose tags cannot be read never links two wallets |
| Official documentation, contracts and rollout pages | the third exchange and the dates of Protocol V2 | | | yes | **Used**: registry of the engine |
| Goldsky public subgraphs (order book, activity, positions, profit, open interest) | used to give fills by wallet | all five answer that the endpoint is deprecated; the replacement feed answers HTTP 402 without payment | | yes | **Rejected**: closed, replacement paid |
| Envio HyperSync | fast log retrieval | needs a personal token; free limits not stated on the pages read | | yes: 401 without token | Not used: needs an account |
| `warproxxx/poly_data` | a pipeline that downloads fills and markets | licence file GPL-3.0 against MIT in the project file; one exchange only, from block 84,902,353; no ready snapshot; needs the token above; last commit September 2026 | contradictory | read, not run | **Rejected** for now: licence unclear, one contract of three |
| PendulumFlow archive | hourly order-book files | no wallet; about 1.4 GB an hour; non-commercial licence; published with a lag of days to weeks | CC BY-NC 4.0 | page and range request probed | Pilot later for the order-book family, on a few named markets |
| Hugging Face `TimeSeventeen/Polymarket-v2` | daily files of on-chain fills with wallets from April 2026 (55 GB) | no transaction hash, no contract column, coverage of the third exchange unknown, files may be revised | CC BY 4.0 | one day downloaded by a reader | Pilot later: it would give fills under 1,000 USD for 2026; provenance to check first |
| Dune, Allium, Bitquery, Flipside, CryptoHouse | SQL on fills | accounts or payment needed | | not probed | Not used |
| Recent "insider detection" repositories | scores on public trades | young, no out-of-sample test; one published backtest concludes that its score carries the entry price, not foresight | various | read | Reference only |

## What changed for this project

- **History is available without any index service.** The size filter by market returns a market's whole history of
  large fills in one request. That is what made an unselected population possible: 2,851,593 fills on 32,552 markets
  in about one hour, at 9 requests a second, a third of the documented limit of the route.
- **The funding graph needs logs, not only receipts.** See [SYSTEM_AUDIT.md](SYSTEM_AUDIT.md).
- **Three contracts, not two.**
- **Dates to watch**: new markets on Protocol V2 from 23 November 2026; changes of the order-book API on 14 December
  2026 (the trade and order listings change their filters). The first version of the data API was retired on
  2 November 2026.

## Rate limits respected

Documented limits of the venue (read on 14 November 2026): 300 requests in 10 seconds on `v2/trades`, 200 on
`v2/activity`, 800 on all `v2` routes together. The collectors of this study stayed at 9 and 10 requests a second.
No cache-defeating parameter was sent. Public nodes were used at the pace each one accepted: a refusal was followed by
a wait, never by another route to the same provider.
