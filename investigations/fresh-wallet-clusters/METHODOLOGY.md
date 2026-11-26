# Methodology

## What this repository had already measured

The frozen study of 14 November 2026 read 2,851,593 fills of $1,000 or more on 32,552 markets and traced funding for 20,070 thin or dormant entries. Two plain keys paid more than one of those wallets. One is the published Nobel 2025 group. None fell in the validation window (April to October 2026). That study's entry was a single fill of $1,000, not a cumulative commitment, and it did not test cash-out convergence or the base rate of same-outcome fresh groups on ordinary markets outside its alert screen. `PATTERN_RESEARCH.md` states that base rate directly: it was not measured. `C4_COFUNDED_GROUP` and `C5_RECURRENT_FUNDER` stayed inconclusive on validation because they did not fire. The lonely-thin ignition rule did not beat the price (`PATTERN_RESEARCH.md`). Fresh proxies are not new operators (`NEW_LEADS.md`, NB-2). A shared exchange, bridge or relayer is not a common owner (ChangeNOW, Railgun, Relay and Tornado notes in this repository).

This study does not rerun those tests. It asks the question they left open, under rules fixed in `preregistration.json`.

## Population

Closed Polymarket events with at least $50,000 of volume and a scheduled end from 1 January 2025 through 25 November 2026, plus a separate open stratum. Markets are binary Yes/No with at least $10,000 of volume. Tags use `monitoring/phi_engine/contracts.py`: public-view tags are excluded, season-long sports and listed prices are the control family, and the rest are the information family. The sample inside each family and stratum is systematic across end date. It is not a list of markets chosen for a large price move.

The cash filter on the public trade API is $100. Buys that never print a fill of that size are outside the tape. A market whose tape exceeds the page cap is dropped rather than analysed from a prefix.

## Reconstruction

For each wallet and outcome the tape is walked in time. The reported commitment is the maximum of cumulative buy notional minus cumulative sell proceeds. The threshold time is the first second that quantity reaches $1,000. Freshness uses the oldest activity page. When that page does not reach the wallet's entry, a dormancy gap is not invented. Funding is the collateral transferred to the wallet in the 10,000 blocks before the threshold, then at most three hops through same-transaction relays and low-nonce pass-through keys. Cash-outs are withdrawal receipts, not redemptions. Infrastructure addresses from `chainfund.INFRA` stop the walk.

## Statistics

The null for a shared funder keeps each key's popularity and the calendar month, and breaks the alignment with markets. The null for co-timing compares information markets with public-process markets inside the same volume quintile. Both are one-sided. Three tests share a Bonferroni threshold. A service address cannot contribute a hit.

## What this design cannot see

Collateral that arrives more than about five hours before the threshold, on another chain, or in a token other than USDC, USDC.e and pUSD. The operator behind a new proxy. A mixer or a bridge, past the point the transfer becomes indistinguishable from everyone else's. Public name tags were not consulted; a quiet exchange address with fewer than 1,000 transactions could be labelled plain until the fan-out rule (more than ten traced wallets) catches it. Activity histories are the oldest 1,000 rows and are capped at 4,000 wallets, with the test stratum first. Funding traces are capped at 1,000 wallets. Those caps are coverage limits, recorded in `data/data_coverage.csv` and `data/stats.json`, not silent omissions.

Pre-2025 automated-market-maker markets are outside the window. The frozen study already covered single fills of $1,000 through October 2026; this design adds cumulative commitments on a sample, not a second full census of every fill.

## How the collector was run

The Gamma offset listing returns HTTP 422 past a few thousand events, which would have dropped 2026. The catalogue uses `/events/keyset` and `after_cursor`, which is what that API documents. An edge stores the largest transfer from a given sender, not the sum of several transfers, so a second payment from the same key is visible in the raw logs of that transaction but not added into the dollar column. The first funding queue kept only the tightest window on each market and left some seven-day group members untraced; the queue was then aligned with the coverage rule and those wallets were traced before `analyze` was run again. No threshold in `preregistration.json` changed. Its hash is in `PREREGISTRATION.md`.

Amendment 004 keeps that spec. It adds a screen, not a new confirmatory rate. Each information condition is requested from the public trade API at a 100 USD cash floor, at most three pages. Ending net buy notional of at least 1,000 USD on a complete tape means the high-water is at least 1,000 USD on the fills that were returned. Fills under 100 USD are absent, so a small sell can still pull a wallet under the threshold, as amendment 002 measured. Partials keep only the newest 3,000 fills of at least 100 USD. The screen is not traced for funders. H6 is only the 29 wallets already selected. A shared service remains a shared service when the address is a documented bridge, pool, relayer, or a contract. Nonce and recipient count are recorded and do not, by themselves, assign that class.

Amendment 005 keeps that spec. H7 is one path, not a new rate, so it has no permutation p-value. Stake on a named market is the chronological high-water on that condition. Collateral received by the proxy is a separate number. Cash PnL follows the collateral identity in `investigations/data-completion-20261123/scripts/ledger_build.py`. The 967 partial markets are continued to 15 pages. The sub-100 USD check is limited to the pre-registered 900 USD band and is reported as not run when the band is too large to read.
