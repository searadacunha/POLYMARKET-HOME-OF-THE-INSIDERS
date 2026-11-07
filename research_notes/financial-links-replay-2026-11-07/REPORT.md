# Financial-link replay: KPMG handoffs, a Railgun-funded Maduro tree, XFM collectors, Iran and pardon cohorts (7 Nov 2026)

**Type:** primary-chain replay. Every material edge below is re-derived from Polygon receipts, Solana transactions, Relay records, SEC filings or Polymarket's own APIs, and re-checked offline by [`verify.py`](verify.py) (47 checks, no network). Raw responses (about 125 MB) stay outside Git; the evidence needed by `verify.py` is in [`evidence/`](evidence/). This note does not rewrite the [KPMG intake](../kpmg-election-integrity-2026-11-07/REPORT.md), the [external-case intake](../external-polymarket-cases-2026-11-07/REPORT.md) or the [X-lead verification](../x-history-2026-11-06/verification/REPORT.md); it adds what those notes listed as missing.

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

**Expansion test, funding side** ([`data/kpmg_funding_wallet_relay_orders.csv`](data/kpmg_funding_wallet_relay_orders.csv)). The 23 funding wallets made 76 Relay orders, and every counterparty is one of the 22 accounts: no outside account is funded through them, and they receive by Relay only cohort withdrawals. Seen through Relay, the 22-account set is closed.

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
5. **Closure (ACCOUNTING_RECONCILED, TRACE_COMPLETE).** Each distributor passes on exactly what Railgun sent. The children send USDC only to other children or to Relay solvers. The 71 deposits (21,977.513862) plus the residue left in children (66.652297), minus 0.006005 of poisoning dust from outside, equal the 22,044.160154 unshielded.
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
- **Deposit sides of the 38-account cohort** ([`data/g38_deposit_origins.csv`](data/g38_deposit_origins.csv)). All 38 accounts are now read, the 25 that were missing included: 86 Relay deposit orders from **39 funding wallets**, none used by two accounts, none present in any other cohort. The origins are Polygon (30), Ethereum (19), Arbitrum (11), Base (10), Optimism (8), Solana (4), Bitcoin (3) and Monad (1). One hop up, on Polygon and Ethereum, 9 funding wallets are fed by **Robinhood 9** and 6 by Coinbase hot wallets (6, 7, 10, 45); 5 others are fed by unlabelled senders or another Relay hop; 19 sit on chains not read here. Entry is kept separate per account and comes from exchange withdrawals, while the payouts converge on one Coinbase deposit address: the same shape as the KPMG cohort. No private common funder: REFUTED on the wallets read, UNRESOLVED for the 19 on unread chains.
- **Biden-pardon accounts (C6)** ([`data/biden_pardon_shared_deposit.csv`](data/biden_pardon_shared_deposit.csv)). The withdrawals of `0xd9be…` (16 withdrawals, 337,487.34 native USDC, mostly through the Uniswap V3 USDC.e/USDC pool) and of `0xa416…` (9 withdrawals, 146,504.52) reach `0x0a65fdd8…`. That address receives 26 credits from only these flows and sweeps all 484,445.82 to one wallet. The shared deposit is CONFIRMED and the exchange identity is UNRESOLVED; the address is not counted as a trader. a416's later Relay exits (27,607.11) were not traced.

## 4. XFM paired wallets: nine mint matches, two collector wallets for 37 numbered accounts

**Receipts** ([`data/xfm_nine_receipts_decoded.csv`](data/xfm_nine_receipts_decoded.csv)). All nine published transactions on "Will Anthropic's public ticker be $ANTH?" (CTF Exchange `0xe2222d27…`) are **two-party mint matches**. In each, two accounts pay collateral, the Conditional Tokens contract splits it into YES and NO (`PositionSplit`), and each account receives one side. The two accounts are the only maker and taker. The YES/NO mapping read from Gamma reproduces MSR's labels 9/9, and shares sum to 1,779.93 on each side. The taker pays a 1 % fee each time, so a pair buys a complete set worth exactly 1 and loses the fee. The mechanics are ordinary; who is matched with whom is not.

**Names and collectors** ([`data/xfm_collectors.csv`](data/xfm_collectors.csv)). The accounts' own public profile names are `xfm-<series>-<n>`. On **15 Oct 2026**:
- between 14:34 and 14:57 UTC, 20 accounts of series 5 and 6 (`xfm-5-1` … `xfm-6-10`) withdraw by Relay to one Polygon wallet, `0x91243b65…`, pair by pair in numeric order;
- between 15:10 and 15:20, 17 accounts of series 7 and 8 withdraw to `0x75a4aeb1…`.

19 of these 37 accounts are not among MSR's 18. `0x91243b65` signs its own transfers and sent everything on (2,236.97) to `0xdbcf880d…` one minute later. In January it had paid the RelayRouter for `xfm-6-1`'s first deposit (45.50), so one wallet both funded an account and collected 20 of them.

Six other Polygon addresses each take withdrawals from two or three accounts and sweep everything to `0xba2987a1…`. That is a high-volume proxy contract (more than 10,000 transfers, 526 senders), so these six behave as customer deposit addresses of one service.

**Reading.** The 37 balances are CONFIRMED to have been consolidated into two wallets by a scripted, numbered sweep. Common control of the numbered set is SUPPORTED: one consolidation wallet funds an account and collects twenty, but it is not proof of one person. The nine mint matches are therefore trades between accounts that pay out to the same wallet, at no price edge and a fee: consistent with volume or incentive farming, not with an informed bet.

## 5. Iran, 14 January 2026: the YES whale, X34 and the NO side (PR 36 lead D3)

**Market and tape** ([`data/iran_jan14_episode.csv`](data/iran_jan14_episode.csv)). The market is "US strikes Iran by January 14, 2026?" (`0x64b14a09…`, resolved No). Its full tape has 58,803 rows. YES traded at 0.07–0.13 through the day, jumped to 0.63 after 16:00 UTC, and peaked at 0.83 around 21:00–22:00.
- **The new account.** `mutualdelta` (`0xaa6a2bed…`) was created at 20:07 UTC. Its 201 YES buys run from 20:29 to 23:53: 40,021.35 USDC for 255,817.83 shares at an average of 0.156, against 212 distinct counterparties. It made no sale and no withdrawal, and lost everything.
- **Its funding (CONFIRMED path).** A Base wallet, `0x899ecb22…` (nonce 15, personal), sends 40,000 USDC and gas to a one-use key, `0x1c5ce37a…` (nonce 2). That key deposits by Relay into the account at 20:24.
- **The NO side.** While mutualdelta bought, 1,897 accounts bought 2,287,308.77 USDC of NO; the largest took 6.5 %. "One account buying all the NO" is REFUTED.
- **X34**, of the eight-account network, was created at 20:47 and funded at 20:58 from the network's cash box (`0xe9a7230f`, already documented in phase 2). It bought 10,770 of YES, sold YES for 19,343.17, then bought 30,000 of NO at 0.5747 at 22:44: the profitable switch the post describes.
- **The link.** The two accounts share no fill transaction, and none of mutualdelta's funding addresses is in the network. A coordinated pump-and-switch is therefore **not demonstrated**; the upstream of `0x899ecb22` on Base is UNRESOLVED, because the Base explorer is behind an anti-bot page.

## 6. Burdensome-Mix

The SDNY/CFTC account (`0x31a56e9e…`, already reconciled in PR 12) shares no address with the Railgun tree: none of its funding (`2i7HJJTs…`, Solana, 26 Dec 2025) or exit (`ERKEtTTb…`) addresses appears among the tree's 461 addresses or their 458 counterparties. It shares none with the KPMG cohort either. It is a separate case, and this pass adds no new financial edge to it.

## 7. Snoorrason, 14 Oct 2026 08:23:34 UTC (`2110285369748963671`)

The long-form text, previously UNRESOLVED in the X-lead verification, comes back identically from two public mirrors (fxtwitter and vxtwitter). It extends X's own truncated syndication text and ends: "so it seems like top 5 might be 1)kane 2)mbappe 3)yamal 4)rodri 5)messi what is just total bullshit". X's object shows a `note_tweet` and a single edit id, so the post was never edited ([`evidence/x/`](evidence/x/)). Status: SUPPORTED (mirrors of X's API, not X itself). The author **infers** the ranking from Polymarket prices ("someone bought 66k shares at 56c"); the post is not a claim of knowledge.

## 8. Not done, and what would close it

1. **KPMG funding through exchanges.** The Relay-visible set is closed, but an account funded directly from an exchange without a Relay leg would not appear; Bitquery's Solana-side exchange funding (Binance, Bitget, Crypto.com) was not replayed. The Relay v2 API is retired on 24 Nov 2026.
2. **Exchange identity of the sweep wallets.** `0xeb73b4a6…d70f`, `0x901c7c86…`, `5tzFkiKs…`, `ADqZYsW9…`, `A77HErqt…`, `0x4b6f…27bb` and `0xba2987a1…` are unlabelled here.
3. **Base and other unread chains.** Base explorer pages are behind an anti-bot challenge (not bypassed); 19 funding wallets of the 38 cohort and the upstream of `0x899ecb22` are on such chains.
4. **ACDC 544-wallet dataset.** No primary list or transaction set was found; nothing was rebuilt.
5. **The 19 XFM accounts beyond MSR's 18** have not had their own trades decoded.

## Reproduce

```bash
python3 -I tools/resolve_names.py RAW/profiles <names>          # gamma public-search, exact names
python3 -I ../x-history-2026-11-06/verification/scripts/collect.py relay|pm|es|rcpt ...   # existing collector, XLEADS_RAW=RAW/xl
python3 -I tools/relay_handoffs.py RAW/xl RAW/kpmg_accounts.json RAW/handoffs_all.json
python3 -I tools/verify_handoffs.py RAW RAW/handoffs_all.json RAW/kpmg_accounts.json OUT/kpmg_handoffs_verified.json
python3 -I tools/sec_collect.py RAW/sec <tickers>; python3 -I tools/kpmg_markets.py RAW OUT
python3 -I tools/relay_chain_resolve.py RAW/relay_chain <deposit hashes>; python3 -I tools/relay_chain_origin.py RAW/relay_origin <payout hashes>
python3 -I tools/relay_by_hash.py RAW/relay_by_hash <hashes>; python3 -I tools/xfm_decode.py RAW/xl/polygon <hashes> OUT.json
python3 -I tools/build_tables.py RAW            # writes data/ and evidence/
python3 verify.py                               # offline, 47 checks
```

`SHA256SUMS_RAW.txt` lists every raw response kept outside Git.
