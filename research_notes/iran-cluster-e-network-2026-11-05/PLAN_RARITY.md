# Plan: how rare is a shared withdrawal destination among early Yes buyers?

Written on 5 November 2026, before any of the data below was collected or computed. Its SHA-256 is recorded in the commit that adds it. Any later change is an amendment, dated and listed at the end of this file.

## Question

Cluster E accounts sent their Polymarket withdrawals to shared destinations (`4dLZQynk…`, `0x519fa16e…`, `0xa6c22144…`). Is sharing a withdrawal destination with another early bettor of the same market common or rare?

## Population (fixed)

The wallets that bought the Yes token of "US strikes Iran by February 28, 2026?" for at least 1,000 USDC (sum of size × price over BUY rows of the Yes token) with a trade timestamp `1772236800 <= t < 1772259300` (28 February 2026, 00:00:00 to 06:15:00 UTC), in the Data API trade tape archived by the previous note (`../iran-solana-beneficiary-2026-11-05/evidence/polymarket_reduced/us_strikes_feb28_trades_reduced.jsonl.gz`), deduplicated exactly as in that note's `verify.py` (115 wallets according to that note).

This population was chosen by the previous note after the cluster was seen. It is reused unchanged so that no threshold is tuned here. It is not a random sample of Polymarket users.

## Data (fixed)

For each wallet: every Relay request returned by `https://api.relay.link/requests/v2?user=<wallet>`, all pages. That endpoint returns orders where the address is the `user` or the `recipient` (checked on 5 November 2026 on `4dLZQynk…`, which returned exactly its 11 known orders).

A **withdrawal** is a request with `user` = wallet, origin chain 137, `status` = `success`, `referrer` = `funxyz|su4gnoxz14` (Polymarket's integration), and `recipient` different from the wallet.

## Unit and statistics

Unit: the wallet. D(w) is the set of recipients of its withdrawals, lifetime as indexed on the collection date.

- **S1, primary.** Number of wallets of the population that share at least one recipient with another wallet of the population. Groups are the connected components of the wallet–recipient graph restricted to recipients shared by two or more population wallets. Reported: number of groups, size of each.
- **S2.** The same count, after removing every wallet already linked before this note (the seven cluster E accounts) and every account first linked in this note. This is the informative number: groups that nobody had found.
- **S3.** For each pair of wallets sharing a recipient, the smallest gap between their withdrawals to that recipient.
- **Coverage.** Number of wallets with zero Relay withdrawals (they may have withdrawn by direct transfer, which this test cannot see).

## Exclusions (fixed)

- Requests whose recipient equals the user (self-conversions of a deposit wallet).
- Nothing else. Exchange deposit addresses are customer-specific and stay in. A recipient that is shown to be a shared service (hundreds of distinct Polymarket users) is reported, not removed.

## What will not be claimed

- No p-value, false-positive rate or significance: the population was chosen after the fact, and there is no null model of withdrawal behaviour.
- A shared destination is a financial relation, not proof of common ownership.
- Withdrawals that do not go through Relay are invisible here.

## Budget

One network worker, one Relay request every 13 seconds or more. If the collection cannot finish, the result is reported as partial with the number of wallets collected; it is not extrapolated.

## Amendments

None.
