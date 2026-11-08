# TriAgent historical campaign: registry of examined leads

State of the campaign's SQLite registry, exported 2026-11-08 15:39 UTC (campaign state: stopped). Rows in LEADS.csv are claims to check, never findings; KNOWN_CASES.csv separately inventories pre-existing investigations. Nothing here establishes insider trading, identity or common ownership; no financial claim is published here.

## Files

- [LEADS.csv](LEADS.csv): every lead from X and from the repository's intake notes, with its dedup key, state, GPT scores, closure reason and the X post as re-read by the supervisor (author and UTC time from X's public embed endpoint).
- [KNOWN_CASES.csv](KNOWN_CASES.csv): the repository investigations registered as closed known cases, so that a duplicate decision can point to them.
- [SEARCHES.csv](SEARCHES.csv): every Grok search cell (topic x period), positive, negative or failed.
- `verify.py`: offline consistency checks of these three files (no network).

## Leads by state

| State | Leads |
|---|---|
| closed | 23 |
| deferred | 3 |
| duplicate | 55 |
| investigating | 7 |
| unresolved | 2 |

## Open leads (missions designed, not run)

- `L-0dce48e84b` (Claude mission `134c7043cf3b4f20`): **wallets** — The reported monthly/all-time discrepancy reflects transaction classification or leaderboard accounting. [Source](https://x.com/Mosterin_0/status/2115390649344123315). **Not independently verified.**
- `L-1c9c645f0f` (Claude mission `6ecd512a2ff94ad1`): **wallets** — An Aave borrow funded approximately $274,000 of election exposure through the two named wallets. [Source](https://x.com/Bitquery_io/status/2108187606983090601). **Not independently verified.**
- `L-52d975eba8` (Claude mission `f5ab6c0621b04499`): **politics** — the advertised guaranteed profit is conditional Democratic-House exposure rather than an exhaustive arbitrage. [Source](https://x.com/unvint/status/2116467967999312156). **Not independently verified.**
- `L-52fa9f8946` (Claude mission `645a926e9b5541d9`): **insider** — four recently funded accounts made synchronized purchases below $0.18. [Source](https://x.com/thepolynerd_/status/2009122571535700312). **Not independently verified.**
- `L-624333d37c` (Claude mission `a54215b0898c41fc`): **geopolitics** — account 0x91710b66a05f2ea3614dd50abe7192c7f90ac3e0 committed approximately $18,700 around midnight UTC before the post. [Source](https://x.com/lookonchain/status/2036005863136362892). **Not independently verified.**
- `L-d372d727ba` (Claude mission `5c82fb5b79ad4fe8`): **politics** — a reported $281k None addition preceded material public election information; its actual timing and economic size remain unverified. [Source](https://x.com/TheDonPoly/status/2117784896198340626). **Not independently verified.**
- `L-dd3322e6f1` (Claude mission `aa110f1dd2574c0a`): **geopolitics** — account 0xd7375270e4769d3cc31885773070a5f12d5bbe95 incurred $13,200 cost and approximately $463,000 profit on this market. [Source](https://x.com/lookonchain/status/2041756515724615930). **Not independently verified.**

State: stopped during pass 1. **No saturation verdict is established.** A stopped, partially searched campaign cannot demonstrate that all leads have been exhausted.

## Passes

| Pass | Started | Ended | Searches | New leads | Significant |
|---|---|---|---|---|---|
| 1 | 2026-11-08 13:09 | — | 6 | 50 | 0 |

## Coverage (topic x period)

| Topic | Period | Searches | Posts | Re-read | New leads | Negative | Failed |
|---|---|---|---|---|---|---|---|
| coordination | 2026 | 1 | 0 | 0 | 0 | 0 | 1 |
| geopolitics | 2026 | 1 | 9 | 9 | 6 | 0 | 0 |
| insider | 2026 | 1 | 13 | 13 | 13 | 0 | 0 |
| politics | 2026 | 1 | 15 | 15 | 13 | 0 | 0 |
| pre_announcement | 2026 | 1 | 8 | 8 | 4 | 0 | 0 |
| wallets | 2026 | 1 | 15 | 14 | 14 | 0 | 0 |

## Registry scope

- **90 campaign leads**: 23 closed, 55 duplicates, 7 investigating, 3 deferred and 2 unresolved (see state table above).
- **49 additional known cases**: pre-registered as closed to identify duplicates, not new findings.
- **139 total registry entries**: 72 show as closed only when the 49 historical known cases are included. The state table above counts campaign leads alone.

## Unresolved and deferred leads

- `L-1c033bfc24` [deferred] — Checkable but low expected information gain: a small first bet alone supplies little evidence of privileged information. Defer under the two-follow-up limit. [Source](https://x.com/PolyInsider_/status/2109101075651604521).
- `L-3a00d4e682` [deferred] — UNRESOLVED: no full proxies, destination, condition IDs or transactions supplied. Reported profits sum to $24.25M, but correct addition does not verify profit or control. Defer under the two-follow-up limit; never reconstruct the abbreviated destination by guesswork. [Source](https://x.com/lookonchain/status/2068581320197021801).
- `L-403620652a` [deferred] — HYPOTHESIS: the supplied timestamp-match flag is false and exact market wording is absent. $772,414 minus $750,900 is $21,514, which is not profit without inventory accounting. Counterparty evidence is necessary to distinguish wash trading from legitimate activity. Defer under the follow-up limit. [Source](https://x.com/Bitquery_io/status/2049501211712492022).
- `L-cfac5f3bde` [unresolved] — mission ede9cfd3f52444f6 ended blocked without a review: uncertain: grok cli exit 1: Error: max turns reached . Check xAI usage, then retry. [Source](https://x.com/polyfactual/status/2119113530632786043).
- `L-dc9fc62c5e` [unresolved] — mission 7c24163f641d4a1f ended blocked without a review: uncertain: grok cli exit 1: Error: max turns reached . Check xAI usage, then retry. Source: `research_notes/x-history-2026-11-06/LEADS.csv#IR-YESNO-JAN14`.

## For the prospective detector

Dated links by phase (A before the first bet, B before the event, C after): {}. No model is calibrated or enabled from these cases; labels are lead states, not proof of insider trading. Next: out-of-sample chronological validation, placebo dates and false positives per 1,000 accounts with `triagent backtest` once enough dated cases exist.

## Limits

- Grok CLI searches the web, not the X API: coverage of X is unknown and deleted posts are invisible.
- Post re-reads use X's public embed endpoint, which is undocumented; a failed re-read is 'not verified'.
- Subscription quotas bound the pace (Grok, Claude and Codex daily caps); a cell is one search per pass.
- Wallet or exchange addresses never establish identity or common ownership.
