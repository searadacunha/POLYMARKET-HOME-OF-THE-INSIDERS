# Analysis plan: how rare is the exit structure of Iran cluster E among comparable early buyers?

Written on 6 November 2026, before any comparator exit data was collected and before any rate was computed. It is frozen with the code by `gel.py` (`PROTOCOL.lock`); any later change is a dated amendment in `amendements/`, listed at the end of `results.md` as a deviation.

The plan tries to destroy the hypothesis "the Iran exit structure is rare", not to confirm it.

## Question

In the reference population (the 115 wallets that bought at least 1,000 USDC of Yes on "US strikes Iran by February 28, 2026?" between 00:00 and 06:15 UTC on 28 February 2026, frozen in `../iran-cluster-e-network-2026-11-05/PLAN_RARITY.md`), nine wallets form one group linked through several shared withdrawal recipients at once. How often do populations of comparable early Yes buyers, before another sudden Yes resolution, show the same kind of structure: wallets sharing **two or more** non-service withdrawal recipients with one same other wallet, beyond what the wallets' number of recipients and the recipients' popularity predict?

What is already known and is not re-tested: in the reference population, 17 of 115 wallets share a recipient, in groups of 9, 4, 2 and 2 (PR 27). That count had no comparator and no null model. The structure measured here (several shared recipients per pair) was chosen because the PR 27 report describes the network that way. The reference value is therefore post hoc by construction; the comparators are not.

## Data

- **Universe for comparators.** The phase-8 archive of `investigations/maduro-iran`, read on 30 September 2026 for another question: `universe.json` (2,097 closed markets of at least $250,000, end date 2025-10-01 to 2026-09-15, sports, crypto prices, tweet counts and weather excluded by the archive's own rule) and `trades/<condition>.json` (taker rows of at least $100). It was built without any suspicion criterion. `code/col_10_select.py` records the SHA-256 of `universe.json` and of every trade file it reads. Survivorship: closed markets only.
- **Populations.** data-api `/v2/trades?condition=<id>&limit=1000&taker_only=false`, the parameters of the reference tape. On 6 November 2026 the endpoint was checked to ignore `start` and `end` (both `condition` and `condition_id` forms), so `code/col_20_populations.py` pages from the newest row back past the window. A page must hold a list of rows of that market and a pagination object, be no newer than the previous page, and may not be empty while announcing more; otherwise the run stops. A tape is **complete** only if it passed below the window start, or ended at or below the oldest row of the 30 September archive, **and** every Yes taker row of the archive inside the window is found in it (same hash and wallet). The archive is thus an independent completeness oracle.
- **Exits.** Relay `requests/v2?user=<wallet>`, all pages (at most 100), one request every 13 seconds, `code/col_30_relay.py`, into `data/relay/`. Every page must hold a list of requests, and an empty page may not carry a continuation. Every page served since September carries a notice that Relay reduces the v2 rate limit in stages before retiring it on 24 November 2026, so a degraded endpoint is a real risk: every 50 wallets a sentinel re-reads a reference wallet whose single archived page is known, and the run stops if any archived request is missing. The reference wallets reuse the pages archived by PR 27 on 5 November 2026, into a separate folder `data/relay_reference/`, each page checked against that note's `SHA256SUMS.txt` and its `DONE` counts. A comparator wallet that is also a reference wallet is read again live.
- **Recipient classes.** `code/col_40_classes.py`, after the exit collection: the recipient's own Relay pages (at most 5), and for sensitivity D `eth_getCode` at `latest` on each destination chain through keyless public RPCs, and Solana `getAccountInfo`.
- **Accounting**, aggregated by `ana_50_stats.py` into `derived/results.json` and reported in `results.md`: markets per exclusion reason, trade pages per market, termination and oracle misses, Relay files per termination, request counters per source (requests, successes, 429, 5xx, dropped connections or truncated JSON), classes and their reasons, recipients with unchecked chains, incomplete populations by reason. A 429, a 5xx, a dropped connection or a truncated body is retried and counted; any other HTTP error, and any malformed page, stops the run. An error is never read as an empty result.
- **Raw pages** of third-party wallets stay outside git (`/Volumes/TravailExterne/Enquetes-Crypto/iran_exit_rarity_20261106/raw/`). `data/` keeps reduced records with the SHA-256 of every raw page.

## Population (fixed)

1. **Shock rule**, on the archived taker rows of the Yes token (first outcome "Yes", resolved `["1","0"]`): T is the time of the first Yes row at price >= 0.90 such that the Yes VWAP of the rows in `[T - 22,500 s, T)` is <= 0.50, with at least one row. Files flagged `maybe_truncated` are excluded and counted (their oldest rows may be missing). On the archive, this rule places the shock of "Israel strikes Iran by February 28, 2026?" at 06:15 UTC on 28 February, the reference event time; this check was made on selection data before freezing.
2. **Alleged cases are not comparators.** A market listed in `data/catalog_markets.json` (copied from `study_sync`, fixed on 3 November 2026: Nobel 2025, Maduro, Iran 28 February, Khamenei, ceasefire 7 April, Biden pardons), or whose T is within 6 hours of one of its event times (the same shock), is flagged `alleged` and left out.
3. **One population per shock.** Among comparator candidates (alleged markets excluded first), jumps closer than 6 hours belong to one shock. For each shock, the market with a complete tape and the most population wallets after removing known groups (step 5) is kept; ties go to the smaller condition id.
4. **Population**: wallets whose Yes BUY rows in `[T - 22,500 s, T)` sum to at least 1,000 USDC (size times price), identical rows counted once, as in the reference.
5. **Known groups removed from comparators**: the 25 addresses of `data/known_groups.txt` (cluster E, group G, pair H of PR 27). Sensitivity A keeps them.
6. A comparator needs at least 10 wallets after step 5, a complete tape (`PASSED_WINDOW` or `END` within 1,500 pages) and exit data at `END` for every wallet. Otherwise it is excluded and counted.
7. **Collection order and stopping rule**: comparator populations by distance of T to 28 February 2026 06:15 UTC, wallets by first buy. Collection stops when every comparator is complete, or on 22 November 2026 at 23:59 UTC, whichever comes first. A population that is not complete then is excluded and counted, never analysed in part.

## Exit definition and recipient classes

- A **withdrawal** is a Relay request with `user` = wallet, origin chain 137, `status` = `success`, `referrer` = `funxyz|su4gnoxz14`, `recipient` different from the wallet (unchanged from `PLAN_RARITY.md`). D(w) is the set of recipients, lifetime as indexed on the collection date.
- **Visible** wallets have at least one withdrawal. The others are **censored**: they may exit by direct transfer, which this test cannot see. They are reported per population and never counted as "no sharing". The 37 censored wallets of the reference stay censored.
- **Classes**, decided for every recipient held by two or more wallets of one population: **SERVICE** if it is paid by at least 25 distinct Relay users on its first 5 pages; **CUSTOMER** otherwise (exchange customer deposit addresses, per-customer wallets and personal wallets alike). Contract code is not a primary criterion: a Polymarket proxy, a Safe or a per-customer deposit contract is a contract, and several population wallets withdrawing to the same Polymarket proxy is exactly a network signal. Sensitivity D classes as SERVICE, in addition, every recipient with contract code that is not an EIP-7702 delegation (`0xef0100…`) on a destination chain, or owned by a Solana program other than the System Program, or executable; destination chains that no listed RPC serves (Bitcoin, Tron and others) are recorded as unchecked and counted. A shared recipient without a class stops the analysis. Recipients held by one wallet are not classified: a degree-preserving null never makes them shared.

## Unit and statistics

- **Unit**: the population for the rate, the wallet within a population for the statistic. Pairs are never counted as independent observations: a pair-level count enters only through a population-level statistic whose distribution comes from the permutation null.
- **M** (test statistic): the number of visible wallets that share at least two distinct CUSTOMER recipients with one same other visible wallet.
- **Descriptive**, never tested: S1 (wallets in any group of shared CUSTOMER recipients), group sizes, L (largest group), k_max (largest number of wallets on one recipient), censored count.

## Null model

- **Degree-preserving bipartite permutation** (curveball), within one population: each draw starts from the observed wallet-recipient sets and makes 5 x (visible wallets) trades; a trade picks two wallets and reshuffles the recipients that only one of them holds, **separately within each class**. Each wallet's number of recipients and each recipient's number of wallets are kept exactly, and a SERVICE recipient never takes a CUSTOMER slot.
- What it tests: whether wallets overlap on several recipients more than their degrees and the recipients' popularity predict. What it does not model: one operator running many wallets is exactly what it would flag, and so would a family or a team sharing two exchange accounts. A positive result is excess overlap, not common control.
- Compared with the idea in `Ikey168/Noesis` (`onchain_clustering.py`, MIT, read at `e4ae131`): there, slot members of the discovered hubs are shuffled with possible repeats, and only an expected neighbour count of one address is reported. Here degrees are kept exactly, classes are strata, the statistic is population-level and a p-value is computed. No code is taken from it.
- 2,000 draws per population, seed derived from 20261106 and the population key. p_M = (1 + draws with M >= observed) / 2,001. With 2,000 draws the smallest p is 1/2,001; p_M <= 0.01 is resolvable.

## Tests

- **P1** (primary): p_M of the reference population.
- **P2** (primary): the rate r = k / n of complete comparator populations with p_M <= 0.01, with its exact 95 % interval.
- Secondary, reported, never used to choose: A (known groups kept in comparators), B (classes ignored, every recipient CUSTOMER), C (geopolitics/war comparators only), D (contracts and program-owned accounts as SERVICE).
- **Positive control on real data**, before any test: the reference read by this study's code, classes ignored, must reproduce PR 27's published counts (37 censored, S1 = 17, groups of 9, 4, 2, 2). Otherwise the analysis stops.
- Declared tests: 2 primary, 4 sensitivity variants, each variant computing one p per population, plus 3 benchmark plants per population for the power rule (reported, not tests of the hypothesis). Every computed test goes to `registre/tests.jsonl` through `registre.py`; the count of comparisons is the registry's.
- No correction is applied to the verdict thresholds below: the verdict is a classification with fixed cut points, and the registry count is printed beside it.

## Power rule (fixed)

A comparator enters the rate only if the test can see a structure like the reference in it. For each complete comparator, a benchmark is planted three times into its own visible wallets (9 random wallets receive the same 3 new CUSTOMER recipients, seeds derived from the population key) and the same permutation test is run; the comparator is **eligible** if the benchmark reaches p_M <= 0.01 in at least 2 of the 3 plants. This uses the population's degrees and recipients, never its own observed M or p. Ineligible comparators are reported with their p_M, and counted, but they enter neither n nor k. Without this rule, small or crowded populations, where the null cannot see any overlap, would be counted as populations without excess and push the verdict toward RARE (controls, bias trap).

## Verdict (fixed)

With n eligible complete comparators and k of them at p_M <= 0.01:
- **UNDETERMINED** if n < 10.
- **REFERENCE_NOT_DISTINCT** if the reference p_M > 0.01.
- **RARE** if r <= 0.10.
- **UNCOMMON** if 0.10 < r <= 0.25.
- **COMMON** if r > 0.25.

Whatever the verdict: excess overlap is a financial-structure fact, not proof of common ownership, coordination or inside information. With about 10 to 20 comparators, r has a wide interval; it is printed.

## Positive controls (before freezing)

`code/ctl_00_controls.py` runs `permutation_test`, `power` and `verdict` on synthetic populations only (20, 60 and 120 wallets; null, weak, medium and strong plants; 5 seeds each; 40 null populations for calibration; a SERVICE hub held by 30 wallets and five wallets of degree 30 as traps; the power rule on 20 and 120 wallets; five verdict cases, one of them a bias trap with small planted comparators). The gate: at most 2 of 40 null populations flagged, the strong plant found in every seed at 60 and 120 wallets, the power rule separating 20 from 120 wallets, the SERVICE hub never flagged, the five verdict cases as expected. Report: `controles/controles_positifs.md`.

**Changes made before the freeze, after the first run of the controls** (no real comparator or exit data had been collected or computed): the first run failed its gate. The strong plant was not found in populations of 20 wallets (p_M from 0.40 to 0.68), because three recipients held by 9 of 20 wallets overlap by chance under a degree-preserving null; and with comparators of 40 wallets only half the planted ones were found, so the verdict case expected COMMON gave UNCOMMON. The power rule above was added, the verdict cases were moved to comparators of 80 wallets, the bias trap was added, and the gate no longer requires detection at 20 wallets. A generator bug (a trap that could not terminate) was also fixed.

**Changes made before the freeze, after the pre-freeze review of the collectors** (`silent-failure-hunter`, no real comparator or exit data collected): a malformed or empty Relay or data-api page could be read as a normal end; a chain that Etherscan did not serve was read as "no code"; resumed classification skipped new chains; reference and comparator exit files shared one folder; no request was counted. All were fixed as described above. Contract code moved from the primary class rule to sensitivity D, and alleged markets no longer take part in chaining shocks. The gap that flags a market as alleged went from 48 to 6 hours: at 48 hours, the Israel x Hamas ceasefire of 8 October 2025 was flagged only because the unrelated Nobel event of the catalogue fell 35 hours later (seen on selection data, before any exit data).

## Limits stated now

- Relay withdrawals only. Direct transfers, other bridges and wallets that never withdrew are invisible.
- The Relay index is read as of the collection date; reference pages are from 5 November 2026, comparator pages from 6 November 2026 or later.
- The shock rule is a price proxy for an event time. The reference uses the public event time, which the rule reproduces on its sibling market.
- The universe holds markets ending 2025-10-01 to 2026-09-15 with at least $250,000 of volume. Its exclusion of sports is the archive's own rule and may be imperfect.
- Classes rely on code at collection time and on Relay's recipient-side index, which misses same-chain orders whose fill has no hash (PR 27, section 8): popularity is undercounted, so SERVICE is conservative.
- The reference structure was seen before this plan. Only the comparators are new.

## Amendments

None.
