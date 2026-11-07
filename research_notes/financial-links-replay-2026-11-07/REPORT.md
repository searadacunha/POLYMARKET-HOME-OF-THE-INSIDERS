# Financial-link replay: KPMG handoffs, a Railgun-funded Maduro account tree, Iran and pardon cohorts (7 Nov 2026)

**Type:** primary-chain replay. Every material edge below is re-derived from Polygon receipts, Solana transactions, Relay records, SEC filings or Polymarket's own APIs, and re-checked offline by [`verify.py`](verify.py) (37 checks, no network). Raw responses (about 60 MB) stay outside Git; the evidence needed by `verify.py` is in [`evidence/`](evidence/). This note does not rewrite the [KPMG intake](../kpmg-election-integrity-2026-11-07/REPORT.md), the [external-case intake](../external-polymarket-cases-2026-11-07/REPORT.md) or the [X-lead verification](../x-history-2026-11-06/verification/REPORT.md); it adds what those notes listed as missing.

Status words follow the repository: **CONFIRMED** (reproduced from primary chain data), **SUPPORTED** (primary data consistent, ownership or identity not provable), **THIRD-PARTY REPORTED**, **UNRESOLVED**, **REFUTED**. A shared exchange deposit address means one exchange customer account was credited; it does not name a person. Nothing here shows who traded, or that anyone used non-public information.

## 1. KPMG cohort: 22 proxies, 14 chain-proven handoffs, 7 shared deposit addresses

**Proxies.** All 22 names resolve to exactly one profile each in Polymarket's `gamma-api public-search` ([`data/kpmg_accounts.csv`](data/kpmg_accounts.csv)). Positive control: the 4 proxies published by Bitquery are returned unchanged (4/4). Profile creation times reproduce Bitquery's account-creation clusters to the minute (five core accounts on 6 Nov 2025 19:59:58–20:50:50, four on 8 Nov 14:18–15:01, two on 14 Jan 08:40–08:51). Status: SUPPORTED for the name-to-proxy mapping; CONFIRMED as on-chain parties for the 20 proxies that appear in the handoffs below.

**Correction to the intake.** `0xafed93e1…e696`, cited by Bitquery and by our intake as "Youaregu's last transfer" on Polygon, is not a Polygon transaction. It is the Relay request id: it is the memo of the Solana payout `2nJmCAUf…FFp5` and is embedded in the calldata of the real Polygon withdrawal `0xea5ae0d2…65c5` (78.96 USDC.e from Youaregu's proxy to the Relay solver).

**Handoffs.** For each pair, four transactions were matched by chain data alone ([`data/kpmg_handoffs_verified.csv`](data/kpmg_handoffs_verified.csv)):

1. Polygon: USDC.e from the sender proxy to the Relay solver or Depository, with the request id in the calldata (2025) or in the `RelayErc20Deposit` log, whose depositor is the proxy (March 2026);
2. Solana: Relay pays the intermediary, with that key as memo;
3. Solana: the intermediary signs a transfer of exactly the same atomic amount back to Relay, and its USDC balance returns to zero;
4. Polygon: Relay credits the recipient proxy, with the key carried by step 3 as calldata tail.

| Sender → recipient | Day (UTC) | Intermediary credit | Seconds | In Bitquery's table |
|---|---|---|---|---|
| Youaregu → lawrence3 | 2025-11-06 | 78.50944 | 28 | yes |
| boosthero → greatfan1983 | 2025-11-08 | 641.599942 | 20 | text only |
| lawrence3 → showredto | 2025-11-08 | 598.293722 | 18 | yes |
| bostonguy → makertogo | 2025-11-08 | 381.493863 | 20 | text only |
| shaunres → makertogo | 2025-11-08 | 379.567 | 20 | yes |
| clarkson → molgum12 | 2025-11-08 | 440.913794 | 36 | yes |
| william6 → molgum12 | 2025-11-08 | 439.741371 | 20 | yes |
| johncary → showredto | 2025-11-08 | 409.490561 | 20 | yes |
| **KARLSON1970 → perlgrow** | 2025-11-18 | 998.865012 | 22 | **no (new)** |
| greatfan1983 → pops4532 | 2025-11-21 | 541.68479 | 26 | yes |
| makertogo → pops4532 | 2025-11-21 | 636.966799 | 18 | yes |
| orisonpro → gridconwho | 2026-01-14 | 2,512.031981 | 50 | yes |
| hulklinkme → Protiyaar | 2026-02-10 | 1,498.590069 | 24 | yes |
| Rossatttttt → Protiyaar | 2026-03-12 | 1,641.073104 | 20 | yes |

All 11 Bitquery handoffs are **CONFIRMED** with their published times, plus 3 more. Bitquery attached perlgrow through shared destinations only; its first deposit is in fact a 22-second handoff from KARLSON1970. Each intermediary is the **recipient's** single-use funding wallet, and four of them take withdrawals from two different accounts (showredto, molgum12, makertogo, pops4532). A fifth funding wallet, `CuLxVBqC…`, merges withdrawals from KARLSON1970 and pops4532 into orisonpro's first deposit (1,383.024068): SUPPORTED, from Relay records only (chain legs not replayed).

**Shared deposit addresses** ([`data/kpmg_shared_deposit_addresses.csv`](data/kpmg_shared_deposit_addresses.csv)). Seven withdrawal destinations are paid by 2 to 8 cohort accounts. All seven behave as exchange **customer deposit addresses**, not personal wallets:

- each sweeps its whole balance to one high-traffic wallet;
- on Ethereum, the sweep usually comes 2.2–2.4 minutes after a credit, with gas from the sweeping wallet;
- on Solana, a third party sends a 5,500-lamport fee top-up minutes before each sweep, or co-signs it.

Relay's records show that **no account outside the cohort** pays any of them. Bitquery's "shared payout wallet" `0xabf92618…db9e` (8 accounts, 16 orders, 9,014.22) is therefore an exchange customer deposit address. The new finding is **Youaregu**, the pre-network account that made most of the KPMG profit: its payouts go to three Solana deposit addresses that KARLSON1970, kundragame and pops4532 also pay, `8t5YL8j9…` (33 orders), `89Tw8NBo…` and `Ay1oajpQ…`. Status: SUPPORTED that these accounts' payouts were credited to the same exchange customer accounts; the exchanges are unlabelled here. Limits:

- `0x1cefcfe8…` also receives 3,496.14 that is not matched to cohort Relay orders, mostly from `0x38c474e1…`; this is UNRESOLVED.
- Inbound Solana credits are not enumerated, because token-account credits escape the owner's signature list.

**Market record** ([`data/kpmg_earnings_markets.csv`](data/kpmg_earnings_markets.csv), [`data/kpmg_market_stats.json`](data/kpmg_market_stats.json)). The auditor of each company is the firm signing the EX-23.1 (or sole EX-23, EX-15 or EX-13) consent in the 2025–26 annual filings, found by EDGAR full-text search. The results time is the SEC acceptance of the 8-K carrying Item 2.02. A position counts if it was still held at that time; GitLab drops out, because Rossatttttt sold before filing.

- **21 KPMG markets**, 14.34 expected wins at cost-weighted prices.
- **Biggest-stake rule: 20/21, exact tail p = 0.00116.** This reproduces Bitquery's 0.0012.
- **Every-account rule: 18/21, p = 0.040.** Bitquery's headline 19/21, p = 0.0084, is *not* reproduced: on Dollar Tree, one account still held 20 USDC of the losing side at the filing.
- Other auditors: Deloitte 3/5, EY 3/3, PwC 4/6 (all p > 0.6).
- No buy in the 21 markets after the Item 2.02 stamp; Bitquery reported 247 USDC.
- Dropping markets held only by Youaregu: 19/20, p = 0.0018.
- Šidák correction over the four Big Four groups: 0.0046 (biggest stake) and 0.15 (every account).

The cohort was assembled *because* of this record, so neither p is a probability of informed trading. Outcomes of same-day filers are not independent either.

## 2. Maduro "Railgun" lead: one distribution tree, 71 single-bet accounts, 66 losers

The X lead named four accounts (FrostyFox, ThunderStrike99, W3tLdR9s, speedrinking), each funded once on 26 Dec 2025 and then betting on "Maduro out by January 31, 2026?". The chain shows the following ([`data/railgun_maduro_edges.csv`](data/railgun_maduro_edges.csv), [`data/railgun_tree_accounts.csv`](data/railgun_tree_accounts.csv)):

1. **Railgun exit (CONFIRMED).** On 16 Dec 2025, between 18:54 and 20:29 UTC, six fresh wallets (the "distributors") each receive one Railgun Unshield from `0x19B62092…8C71` (Blockscout label "Railgun: Relay"): 22,044.16 USDC in total, with a fee of exactly 0.25 % of the gross. The trace stops at the pool; no attempt was made to identify depositors.
2. **Fan-out.** The same evening, the distributors give POL gas, then USDC, to 384 child wallets, in batches minutes apart with consecutive nonces.
3. **Accounts (CONFIRMED edges).** Between 17 and 26 Dec, 71 child wallets make **71 Relay deposits** on Polygon. For all 71, the payout to a Polymarket proxy was found by chain data alone: the calldata tail of the deposit equals that of the payout of one of five Relay solvers. Relay's API agrees on the 10 orders resolved both ways.
4. **Bets.** Each of the **71 accounts** was created minutes before its deposit and made **one bet**, of 60.21 to 861.52 USDC:

| Market | Bought | Accounts | Stake | Outcome |
|---|---|---|---|---|
| Maduro out in 2025? | Yes | 32 | 10,393.97 | No |
| US x Venezuela military engagement by Dec 31? | Yes | 21 | 4,847.15 | No |
| US forces in Venezuela by Dec 31? | Yes | 8 | 1,461.35 | No |
| World Leader Out Edition | No | 5 | 1,238.80 | Yes |
| **Maduro out by Jan 31, 2026?** | **Yes** | **5** | **4,024.38** | **Yes** |

In total: 21,965.65 staked; 66 accounts lost everything; 5 won 53,113.16 in shares, about +31,148 net if redeemed. The four accounts in the X post, plus `0xc2dba869…`, are those five, and **none had redeemed as of 7 Nov 2026** (positions API).

**Reading.**

- The "Railgun funding" claim is CONFIRMED at contract level.
- The X narrative is a **survivor sample**: the same tree funded 71 one-shot long-shot accounts, nearly all on deadlines that expired before the 3 January operation.
- A common operator of the tree is SUPPORTED, not proven: the distributors were all fresh on one day, batch nonces are consecutive, and each funding wallet recombines children of three to five different distributors. A service operating the tree for several clients is the alternative it cannot exclude.
- The pattern is a spray of cheap tickets across adjacent deadlines. It does not support precise advance knowledge of the date, and it does not refute that the operator expected an operation.
- None of the 71 overlaps the eight-account Maduro/Iran network. Several appear only as anonymous rows of the September tapes (`phase13/new_wallet_detail.csv`).

## 3. Iran cohorts and the pardon accounts

- **Bitquery's nine Iran accounts.** Relay records (148 orders) and the receipts of 155 deposits and withdrawals give 81 counterparties. **None** is shared with the 38-account cohort, the eight-account network, the PR 27 network or the Inca accounts. The only hit is 65154861 itself, which PR 27 already used as a rarity comparator. Within the nine, flowjj and trevors4 both credit `0x68c3aef6…`, a Binance customer deposit address (sweeps to "Binance 14" and "Binance: Hot Wallet 34"). It has 89 distinct senders in 91 credits, so it is **not discriminating**: it is recorded as a negative control. All nine already appear, unnamed, in the repository's September Iran tapes. The direct counterparties are mostly fresh one-use Ethereum addresses, one per withdrawal (Merlin11111, alealeg, trevors4, flowjj); that is consistent with an instant-exchange service and was not traced.
- **Deposit sides of the 38-account cohort.** 25 of 37 remain unread; this pass did not reach them.
- **Biden-pardon accounts (C6)** ([`data/biden_pardon_shared_deposit.csv`](data/biden_pardon_shared_deposit.csv)). The withdrawals of `0xd9be…` (16 withdrawals, 337,487.34 native USDC, mostly through the Uniswap V3 USDC.e/USDC pool) and of `0xa416…` (9 withdrawals, 146,504.52) reach `0x0a65fdd8…`. That address receives 26 credits from only these flows and sweeps all 484,445.82 to one wallet. The shared deposit is CONFIRMED and the exchange identity is UNRESOLVED; the address is not counted as a trader. a416's later Relay exits (27,607.11) were not traced.

## 4. Snoorrason, 14 Oct 2026 08:23:34 UTC (`2110285369748963671`)

The long-form text, previously UNRESOLVED in the X-lead verification, comes back identically from two public mirrors (fxtwitter and vxtwitter). It extends X's own truncated syndication text and ends: "so it seems like top 5 might be 1)kane 2)mbappe 3)yamal 4)rodri 5)messi what is just total bullshit". X's object shows a `note_tweet` and a single edit id, so the post was never edited ([`evidence/x/`](evidence/x/)). Status: SUPPORTED (mirrors of X's API, not X itself). The author **infers** the ranking from Polymarket prices ("someone bought 66k shares at 56c"); the post is not a claim of knowledge.

## 5. Not done, and what would close it

1. **17 KPMG funding wallets.** Their Relay pages, the remaining expansion test from the funding side, were paused by the API's rate limit; the collector resumes from cache.
2. **Tree beyond Relay.** The 22 non-Relay destinations of the children, and any second unshield batch.
3. **Exchange identity of the sweep wallets.** `0xeb73b4a6…d70f`, `0x901c7c86…`, `5tzFkiKs…`, `ADqZYsW9…`, `A77HErqt…` and `0x4b6f…27bb` are unlabelled here.
4. **Earlier PR 36 items.** The 14 Jan Iran episode (D3), the nine XFM receipts, the ACDC dataset, Burdensome-Mix and the 25 unread deposit sides of the 38 were not reached in this pass.

## Reproduce

```bash
python3 -I tools/resolve_names.py RAW/profiles <names>          # gamma public-search, exact names
python3 -I ../x-history-2026-11-06/verification/scripts/collect.py relay|pm|es|rcpt ...   # existing collector, XLEADS_RAW=RAW/xl
python3 -I tools/relay_handoffs.py RAW/xl RAW/kpmg_accounts.json RAW/handoffs_all.json
python3 -I tools/verify_handoffs.py RAW RAW/handoffs_all.json RAW/kpmg_accounts.json OUT/kpmg_handoffs_verified.json
python3 -I tools/sec_collect.py RAW/sec <tickers>; python3 -I tools/kpmg_markets.py RAW OUT
python3 -I tools/relay_chain_resolve.py RAW/relay_chain <deposit hashes>; python3 -I tools/relay_by_hash.py RAW/relay_by_hash <hashes>
python3 -I tools/build_tables.py RAW            # writes data/ and evidence/
python3 verify.py                               # offline, 37 checks
```

`SHA256SUMS_RAW.txt` lists every raw response kept outside Git.
