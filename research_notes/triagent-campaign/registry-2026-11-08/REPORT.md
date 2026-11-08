# TriAgent historical campaign: registry of examined leads

State of the campaign's SQLite registry, exported 2026-11-08 15:39 UTC (campaign state: stopped). Every row is a lead: a public claim to check, never a finding. Nothing here establishes insider trading, identity or common ownership; no financial claim is published here.

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

- `L-0dce48e84b` (claude, mission `134c7043cf3b4f20`): October 2026 leaderboard anomaly: Mosterin says Polymarket profile 0xb0e74df9430a089aa102e2207af5fde1967439d2 showed about +$2,512,485 on the monthly board as of 28 Oct 2026 while all-time profit was about +$125,196, wit
- `L-1c9c645f0f` (claude, mission `6ecd512a2ff94ad1`): 4 Oct 2026 Brazil election markets: Bitquery’s 8 Oct 2026 thread says a new Polymarket account put about $274K on Lula winning and on Flávio Bolsonaro not winning, funded via about $1M USDT borrowed from Aave at 05:56 UT
- `L-52d975eba8` (claude, mission `f5ab6c0621b04499`): Balance of Power: 2026 Midterms, profile name ndb1: the post says about 3,450,929 Democrats-Sweep shares at 28.7c for about $990k, and about 2,711,272 Republican-Senate/Democratic-House shares at 23.1c for about $626k, f
- `L-52fa9f8946` (claude, mission `645a926e9b5541d9`): The Poly Nerd says four fresh wallets bought “US strikes Iran by Jan 31, 2026” together while the price was under 18%, and that one also bought “US strikes Iran by March 31, 2026”. The post links proxy 0xEFD06D1A6cC221b7
- `L-624333d37c` (claude, mission `a54215b0898c41fc`): Lookonchain says a new Polymarket account it names kynbz spent $18.7K on the market "US x Iran ceasefire by March 31 or April 15" about nine hours before the 23 March 2026 post.
- `L-d372d727ba` (claude, mission `5c82fb5b79ad4fe8`): Same tossup-Senate map on election night: the parent post says None moved from 35.5% to 61.5%, the largest None holder added $281k at 23:18 UTC, had $610k in and a mark of $1.05M, and the account it calls MrOziPM moved f
- `L-dd3322e6f1` (claude, mission `aa110f1dd2574c0a`): Lookonchain says the Polymarket account named Fernandoinfante spent $13.2K on a US–Iran ceasefire by April 7 and was then up $463K.

State: stopped, pass 1. Saturation means the defined sources and leads were examined without a new sufficiently relevant result; it does not mean every case of insider trading was found.

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

## Leads by state

- closed: 72
- deferred: 3
- duplicate: 55
- investigating: 7
- unresolved: 2

## Unresolved and deferred leads

- L-cfac5f3bde [unresolved] Polyfactual says the wallet flagged before two Times/Siena polls bought about $191k of Pete Ricketts at 67–74 cents in the 12 hours before a poll showing him up: mission ede9cfd3f52444f6 ended blocked without a review: uncertain: grok cli exit 1: Error: max turns reached
. Check xAI usage, then retry.
- L-3a00d4e682 [deferred] 2026 World Cup markets: Lookonchain says profiles mintblade, GRIMDRIP, and endlessFate took about $9.24M, $7.6M, and $7.41M and sent profits to the same Binance: UNRESOLVED: no full proxies, destination, condition IDs or transactions supplied. Reported profits sum to $24.25M, but correct addition does not verify profit or control. Defer under the two-follow-up
- L-403620652a [deferred] 25–29 Apr 2026 wash-trade screen: Bitquery flags the Atlético Madrid win market and says wallet 0x2eb10cb8596bf8c8ef409f72cfb5eb6438054ea4 bought about $750,900: HYPOTHESIS: the supplied timestamp-match flag is false and exact market wording is absent. $772,414 minus $750,900 is $21,514, which is not profit without inventory accounting. Counterparty evidence i
- L-1c033bfc24 [deferred] PolyInsider says a fresh wallet put about $1.7k on Gemini 4.0 dropping by 15–16 October 2026 and asks whether it is informed. The profile link is proxy 0x29f9bc: Checkable but low expected information gain: a small first bet alone supplies little evidence of privileged information. Defer under the two-follow-up limit.
- L-dc9fc62c5e [unresolved] iran — 40k YES followed by NO accumulation and copy traders alleged on Jan14: mission 7c24163f641d4a1f ended blocked without a review: uncertain: grok cli exit 1: Error: max turns reached
. Check xAI usage, then retry.

## For the prospective detector

Dated links by phase (A before the first bet, B before the event, C after): {}. No model is calibrated or enabled from these cases; labels are lead states, not proof of insider trading. Next: out-of-sample chronological validation, placebo dates and false positives per 1,000 accounts with `triagent backtest` once enough dated cases exist.

## Limits

- Grok CLI searches the web, not the X API: coverage of X is unknown and deleted posts are invisible.
- Post re-reads use X's public embed endpoint, which is undocumented; a failed re-read is 'not verified'.
- Subscription quotas bound the pace (Grok, Claude and Codex daily caps); a cell is one search per pass.
- Wallet or exchange addresses never establish identity or common ownership.
