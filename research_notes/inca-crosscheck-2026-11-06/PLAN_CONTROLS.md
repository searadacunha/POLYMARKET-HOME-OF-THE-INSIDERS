# Control plan: are the Inca accounts' money links rarer than those of comparable buyers?

Written on 6 November 2026, around 12:00 UTC. At that time the full Polymarket activity, the Etherscan token transfers and the deposit and withdrawal receipts of the five Inca accounts had been downloaded. Their per-market cash flows had been computed and compared with Inca's profit figures. **Their deposit funders and withdrawal recipients had not been read**, except for the two accounts already in PR 27, whose recipients PR 27 publishes. No control data had been collected. Any change after this commit is a dated amendment at the end of this file, with `results_seen: yes|no`.

## Question

Inca Digital selected five accounts on "Israel military action against Iran by Friday?" (condition `0x7f39808829da93cfd189807f13f6d86a0e604835e6f9482d8094fac46b3abaac`) **from their trading only**. It never looked at deposits or withdrawals. Two of them are in the PR 27 network, which was found **from** exits, so that overlap is post hoc. The three others (PorcoRosso `0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a`, ricosuave666 `0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2`, truthlord `0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44`) were selected independently of exits. For them, and for comparable buyers of the same market, how often do we see:

- **M1**: a funder or recipient in the PR 27 network set N27 (below);
- **M2**: a non-service withdrawal recipient shared with another wallet of the analysed set;
- **M3**: a money transfer between two wallets of the analysed set, either the same hash in both activities (direct) or two or more matched legs (A withdraws x, B deposits y within 3,600 s, 0.97x <= y <= x).

## Population

- **Tape.** data-api `/v2/trades?condition=<id>&limit=1000&taker_only=false`, paged from the newest row back past the window start. Each page must hold a list and a pagination object, and may not be newer than the previous one. An empty page announcing more stops the run. **Completeness oracle**: every BUY Yes row of the five Inca accounts' archived activity inside the window must be present in the tape (same hash, same wallet). Otherwise the population is reported as incomplete and the comparison is not run.
- **Window.** From market start, 2025-06-11 20:10:25 UTC, to T, the timestamp of the first Yes trade of the tape at price >= 0.90 (excluded).
- **P**: wallets whose BUY Yes rows in the window total at least 1,000 USDC, at prices <= 0.50.
- **Controls C** = P minus the five Inca accounts and minus the 19 network accounts of PR 27 (`../iran-cluster-e-network-2026-11-05/accounts.csv`, group "cluster E network"). If C has more than 150 wallets, a simple random sample of 150 is drawn with `random.Random(20261106).sample(sorted(C), 150)`.
- **Analysed set S** = sampled controls plus the five Inca accounts.

## Data per wallet (same code for every wallet)

- Polymarket `/v2/activity`, every page; then the Polygon receipt of every DEPOSIT and WITHDRAWAL hash; then Relay `requests/v2?user=`, every page.
- **Recipient of a withdrawal**: the `to` of the USDC or USDC.e transfer from the proxy. If that `to` is the Uniswap pool `0xd36ec33c8bed5a9f7b6630855f1533455b98a418`, the recipient is the `to` of the pool's outgoing USDC or USDC.e transfer in the same receipt.
- **Funder of a deposit**: the `from` of the USDC or USDC.e transfer to the proxy. If that is the pool, the funder is the `from` of the pool's incoming transfer in the same receipt.
- **Relay**: an order with `user` = wallet gives a recipient (`recipient`); an order with `recipient` = wallet gives a funder (`user`).
- **Service recipients**, excluded from M2: an address with any Blockscout metadata tag, an address with contract code at `latest` on Polygon, and the Polymarket and Relay contracts that appear in the receipts. Untagged EOAs, including exchange deposit addresses, count as non-service: a shared deposit address means credits to one same exchange account.
- **Caps**: if all receipts together exceed 4,000 or a wallet's Relay history exceeds 100 pages, the run stops and the cap is reported. Nothing is silently truncated.

## N27 (fixed from PR 27, head `dd9df29`)

The 19 network proxies of `accounts.csv`, and the customer-specific addresses of PR 27's `REPORT.md` sections 2 to 4: `0x519fa16e9897132b7633f634b76306a327839e06`, `0x9063493a4233006be654da772ef4dc38720cac55`, `0x93b7e169b93ece646d08cedbb8fa505796a5b96b`, `0xa6c221448af73af8350291c5cdcd877b39683766`, `0x20bd758daa8d5c2a51e95370079d34f38d91f8b2`, `0xfe775af18824f4951f19e264901030f8528bf972`, `0x98d4e9aa9527316598c4ee6783329b529e292bcb`, `0xed412759234979acf5818121bc37c606373262b2`, `0x44a2c68087a3e6a9a3eedd9cf9c25fd76241e978`, `0x200b195893faf4da3f431125afc17d0903fc8ea6`, `0x937db5b193b367425919de9c08ed78f9119a883c`, `0xe8e0741f10903c96bba5f2b38a0d124414ab58bd`, `0x9028a9e6545e76e74b26f832ec501d63b80b44e7`, `0x5b1323e6f7ebb4643e6d61da582adac8097c64ab`, `0x08d495fb86399f37a5bda51a2f85a9e21a019ca5`, `0x80f4af8b526f0b6a8b70a81b192f11a464f69efc`, `0x8284600d3a6c04d29b1539209838073843052201`, `4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy`, `FyJ2zJY4yyCr8EZJSDVFB862JRiCYr6yWxEuMgVkaFcH`, `Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV`. Exchange hot wallets and `0x852dc1c8…` are **not** in N27: they serve every customer.

## Comparison

- Per measure: count and share with a Wilson 95 % interval for C, for the Inca three and for the Inca two.
- **Test** (confirmatory, only for the Inca three, whose exits did not drive their selection): one-sided Fisher exact test of the Inca three against C, for M1, M2 and M3, with Holm correction over the three tests at alpha 0.05. The two Inca accounts already in PR 27 are reported descriptively. Their M1 is true by construction.
- **Power.** With n = 3, a test only rejects if the control rate is low. If 1 of 3 shows a measure and 0 of 150 controls do, one-sided p = 3/153 ≈ 0.020. This is stated with the results.
- **Positive controls**, run before any control collection, in `scripts/test_rules.py`: the extraction rules must find `0x519fa16e…` and `0x9063493a…` in the two PR 27 receipts `0x014ba2e4…` and `0x03d11843…`. A synthetic pair with two matched legs must be found by M3, and a pair with one leg or a 4 % fee must not.

## Reading rules

- A shared service, a shared hot wallet, a common exchange, or a common bridge is never a link.
- A shared deposit address or a matched transfer is a **supported financial relation**. It does not prove that one person controls both accounts, and it says nothing about inside information.
- Inca's "insider" label is a third-party judgement from trading heuristics. It is reported as such and never used as evidence.

## Amendments

### A1, 6 November 2026, about 12:25 UTC, results_seen: no

One control wallet, `0x17e5540bc696fd3e8b7da9101a93e4835c783d19`, has more than 200 pages of activity (over 100,000 rows); the collector's page guard stopped the run before any control flow was read. The measures use only DEPOSIT and WITHDRAWAL rows. From now on these rows are read for every wallet of S with `/v2/activity?...&type=DEPOSIT,WITHDRAWAL`, every page. Check made before the change on 9TungSahur: 16 rows, equal to the DEPOSIT and WITHDRAWAL rows of its full activity. `scripts/build.py` also checks that the filtered rows equal the full-activity rows for every wallet read both ways (the five Inca accounts and the 11 controls read in full before the guard stopped), and stops otherwise.

### A2, 6 November 2026, about 12:50 UTC, results_seen: no

The deposits and withdrawals of S need 4,237 receipts, above the cap of 4,000 written in the plan; the run stopped as written, before any receipt of a control was read. The cap was a cost guard, not part of a measure. Dropping the most active wallets would select the population on its activity, so the cap is raised to 5,000 and every wallet is kept. To be reviewed by Benjamin as a deviation.
