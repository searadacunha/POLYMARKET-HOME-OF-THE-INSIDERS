# Audit notes: Maduro and Iran work of the repository (audit-maduro-iran, 2026-11-13)

Scope: `investigations/maduro-iran/` and the Maduro/Iran/KPMG/Railgun research notes listed in the task. Repository: commit d8189e8, read only (git status clean at the end of the run). Nothing here is a statement about the guilt or identity of anyone: an address is not a person, and no claim reaches "legally established violation".

Deliverables in this folder: `claims_register.csv` (64 claims), `recompute_results.json` (117 items), `onchain_spotcheck.json` (134 receipts), `case_registry.json` (9 cases), scripts (`claims_register.py`, `recompute.py`, `spotcheck.py`, `native_check.py`, `trade_spot.py`, `case_registry.py`, `build_notes.py`, the sandbox runners), `verify_logs/`, `raw/` (every HTTP response, gzip by sha256 plus `INDEX.jsonl`).

## 1. How it was done

1. Claim register: each finding of `investigations/maduro-iran/FINDINGS.md`, each README / VERIFIED_FINANCIAL_FINDINGS (VFF) line in scope, and the claims of each note, with the stated level; then an audit state from re-reading primary data (basis column: R recompute, S on-chain spot check, V repo verifier run, L logic read). MASTER_REPORT lines 73, 75, 98, 100, 123, 160, 162, 164, 219 mirror FINDINGS F-001..F-011 verbatim, so every correction below also applies there (MASTER_REPORT row line 23 counts CONF:3 SUPP:2 HYPO:2 REFU:3 UNRE:1, which is FINDINGS as written).
2. Recompute from the CSV/JSON files of the repo (`recompute.py`, offline): 94 match, 8 mismatch, 15 informational.
3. Repo verifiers run read-only. Eight of the verify.py scripts (`iran-cluster-e-network`, `iran-cluster-e-erratum`, `iran-solana-beneficiary`, `iran-privacy-cash-sequence`, `iran-privacy-cash-root`, `inca-crosscheck`, `inca-bridged-exits`, `kpmg-statistical-correction`) contain file writes (mostly `verification.json` in the note folder): they are not read-only as written (the kpmg one writes only behind an option). The seven that write unconditionally were therefore executed under `sandbox-exec` with the repo write-denied and `open()/write_text` diverted to stdout (`sbrun.sh`, `runpatched.py`; `python3 -I -B`). Results: cluster-e-network 24/24, solana-beneficiary 18/18, erratum 7/7, privacy-cash-sequence 19/19, privacy-cash-root 14/14, inca-crosscheck all PASS, inca-bridged-exits all PASS, financial-links-replay 47/47, x-history verification 22/22 executed, g38 verify + 7 negative tests, kpmg-statistical-correction verify + 8 unit tests, pulser-cashy offline PASS. The plain (unsandboxed) run of the financial-links verifier hit my 2,700 s timeout (exit 124); only the sandboxed run completed. Logs in `verify_logs/`.
4. On-chain spot check by JSON-RPC receipts (Polygon: drpc, publicnode, 1rpc, tenderly; Ethereum: publicnode, drpc), second-RPC cross-check of block hash, status and log count, positive control first. Hashes taken by script from the evidence files. 134 receipts:

| dossier | receipts | PASS | not PASS |
|---|---|---|---|
| control | 1 | 1 | 0 |
| maduro | 27 | 27 | 0 |
| iran_june_2025 | 29 | 28 | 1 |
| iran_2026 | 25 | 25 | 0 |
| kpmg_railgun_xfm_pardon | 52 | 52 | 0 |

   Strata: Maduro = 8 trade/redeem hashes from `phase2/pnl_transactions.csv` plus 19 hashes parsed from RAPPORT_2026-09-29.md section 3 (withdrawals/transfers, gas, cash-out). Iran June 2025 = Inca EVIDENCE_INDEX rows E001/E003/E017-E025 and cluster-E 13 June withdrawals (withdrawal), `flows.csv` DEPOSIT rows (funding), pulser-cashy 2025 transfers. Iran 2026 = G38 direct receipts (withdrawal to 0xc5bb1be0), cluster-E Relay deposits (withdrawal to Relay), cashy OrderFilled receipts (trade). KPMG/Railgun = all 28 KPMG handoff legs, 6 Railgun unshields, distributor/child edges, pardon, XFM. Two Maduro "gas" hashes are native-ETH transfers (no ERC-20 log): checked by `eth_getTransactionByHash` (`native_check.py`). Maduro report timestamps are minute-level and mix legs, so the time tolerance there is 1 hour (loose); all other strata use 2-5 s. No hash was missing. One record is a MISMATCH on time only: `0xecba8b81...` (flows.csv, Inca-wallet deposit of 3.52 USDC.e) is a 91-log batch transaction whose block time is 9 s later than the data-API event time in the file (receipt, status and amount agree; kept as MISMATCH in the JSON, with a note). Every other receipt agrees with its file on existence, status, block, time and amount. This is a spot check, not an exhaustive replay; the zero-mismatch result says the evidence files are honest about the hashes they print, not that the inferences drawn from them hold.
   Not checkable with the allowed sources: TRON legs (no TRON RPC), Solana legs, Arbitrum and Base legs, Relay API (retired 24 Nov, rate limited), June 2025 Polymarket trade hashes (the repo holds none for the June 2025 accounts; their trades appear only as aggregates).

## 2. Errors and weaknesses, ranked by materiality

Every item gives the file and line, the stated value and the correction. "Stale" means a later note of the repo already contradicts it but the older text was not annotated.

**M1. Stale "38 of 38 pay one Coinbase deposit address / SUPPORTED that all 38 payouts were credited to one Coinbase account".**
`research_notes/x-history-2026-11-06/verification/REPORT.md` lines 17 and 119 (line 16 says the same for the three-account link). README lines 111 and 119 still link this file as the transaction reconstruction. The `g38-proof-tier-audit-2026-11-08` note (and VFF section 1) establishes 32 direct Polygon senders, 3 accounts by Relay (12 credits, only 7 with an order id in the transaction data, 5 matched by unique amount), 1 Arbitrum and 2 Base, with ownership of the recipient UNRESOLVED. Correction: annotate the x-history report; a shared deposit address identifies a deposit destination, not an exchange customer. The same reasoning applies to x-history line 16 (JamWil23, bravonoll, Frogensky, README line 103): shared address, not a shared account.

**M2. KPMG inferential statistics still printed after the 10 November correction.**
`research_notes/financial-links-replay-2026-11-07/REPORT.md` lines 55 to 60 (p = 0.00116, 0.040, Sidak 0.0046 and 0.15) and `research_notes/kpmg-election-integrity-2026-11-07/REPORT.md` lines 11 to 15 (19 winning markets of 21, p = 0.0084, 11 handoffs, `0xafed93e1...` as a Polygon transaction). The correction note shows that the every-account event cannot occur under the reused price vector when sides are opposed, and the cohort was selected for its record; VFF line 87 is already descriptive. Recomputed here: 20/21 and 18/21 (core 19), 20/21 and 17/21 (all 22), Poisson-binomial 0.00116 reproduces arithmetically but is not an inference. The intake text was never corrected for the 14-not-11 handoffs and the `0xafed93e1` identity (which the replay REPORT line 11 does correct). Correction: banner both texts as superseded; quote descriptive counts only.

**M3. F-002 "CONFIRMED" for figures that no data file contains.**
`investigations/maduro-iran/FINDINGS.md` line 9 (also README eight-account table near line 83, MASTER_REPORT line 75): external capital 151,084.40, external outflows 660,708.94, net 509,624.54. PnL 509,993.24 is exact (recomputed from `phase2/pnl_table.json` and from 261 raw activity rows). The other two exist only as text in `phase3/RAPPORT_PHASE3_2026-09-29.md` lines 37, 39, 114. The outflow reproduces only if three internal edges are deducted at SEND-side amounts (2,077.54 + 9,278 + 29,500) from withdrawals of 701,564.48; the capital reproduces only with implied internal deposits of 40,706.76, while the same report's RECEIVE-side internal edges sum to 40,743.46 (36.70 apart). `TABLE3_funding.csv` totals 192,119.13 (not 191,791.16) and `TABLE4_outflow.csv` 701,510.46 (not 701,564.48). The "0.07 % gap" between PnL and net cash flow (368.70) is unexplained. Correction: PnL CONFIRMED; capital and outflow SUPPORTED, with the send/receive bookkeeping stated. Also note PnL is the whole-account result in all markets, not Maduro/Iran only.

**M4. Level labels stronger than the data (signals).**
FINDINGS lines 33 and 51: F-006 and F-009 are REFUTED while their own intervals include zero (F-009: TEST -0.7 % [-7.7, +7.1]; VALID +1.3 % [-2.4, +5.1]); the protocol outcome B means "net > 0 with an interval excluding 0 was not achieved", which is NOT_DEMONSTRATED. F-007 (line 39, MASTER_REPORT line 100): the phase 9 report's control C (events of the same wallets without the signal) shows an uplift of about +24 points against +17.6 to +20.7 for the signal (`RAPPORT_PHASE9.md` lines 133 and 341: "la propriete appartient au wallet, pas au trade"): the property belongs to the wallets and the context, not to "SIG_HIST precedes moves"; phase 14's stable-definition difference has an interval including 0 in VALID (-0.001) and TEST. The phase 8 raw tapes are not in the repo, so these were read, not recomputed (288 = 8 x 6 x 3 x 2 is recomputed).

**M5. F-001 "CONFIRMED" mixes edge types.**
FINDINGS line 3 (MASTER_REPORT line 73, VFF section 2 line 33). Re-verified on chain: all EVM legs sampled (27/27 Maduro receipts). Not verified: TRON legs. Only three edges are direct account-to-account value paths (chileno777 to TacticalInsiderNews, Mrs.Joker to Planktonbets, X34 via 0xe9a7230f to Mrs.Joker); Chiwawas and 154x838hjd6 join through a shared destination EOA (0x44b6f8de), Neodbs only through TRON hubs, and phase 2 itself (`RAPPORT_PHASE2_2026-09-29.md` line 214) classes the hub TA4chMzt as an OTC/P2P USDT ecosystem (35 senders, 36 recipients, 1.17 M USD), i.e. a shared service. Per the repo's own rule (shared destination is not a transfer) the level for the full eight is SUPPORTED, the three direct edges CONFIRMED.

**M6. Population denominators and a retracted timing anchor.**
`investigations/maduro-iran/sources/phase2/TABLE5_population_iran.csv` and FINDINGS F-004 (line 21): the 128 "independent" Iran-window YES buyers include 17 proxies of the later 38-account cohort (11 filled in the same second, 05:46:37) and the earliest Maduro-window buyer (flipfloppity) is in that cohort, so ranks such as "66 % bought before 154x838hjd6" treat dependent accounts as independent. `sources/RAPPORT_2026-09-29.md` line 74 states "first rise at 05:28 (0.135 to 0.205)"; phase 10 (`RAPPORT_PHASE10.md` line 411) retracts the 05:28 anchor ("mauvaise reference"), and the minute tape (`phase10/maduro_iran_minutes.csv`) shows a drift, not a step: 0.14 at 05:00, 0.19 at 05:24, 0.20 at 05:26, 0.19 at 05:28, 0.21 at 05:29, then 0.26 at 06:10 and 0.52 at 06:12. FINDINGS never carried the correction.

**M7. "Result" is neither realised profit nor Iran-only (ledger figures).**
README line 115 and VFF lines 58 to 60 (flydartball +841,375.23) and `x-history-2026-11-06/verification/REPORT.md` check B2 (cashy 464,159.10). Recomputed from `ledger_maduro_alerts.json`: flydartball result = cash formula 841,137.63 + 237.60 of `other_reward` credits, and it equals net withdrawals (841,375.23). Cashy result = cash 458,232.30 + 5,926.79 of rebates/rewards/yield, but net withdrawals are only 354,455.13: 109,704 of the stated result was not withdrawn at the ledger end. (My first draft of this audit attributed the gap to open-inventory valuation: wrong, corrected here; the open tokens are valued at zero.) PURE698's result also exceeds net withdrawals by 404.84. The Iran/Israel class of flydartball's ledger is 837,224.02 over 26 markets, so the account result is not Iran-only (VFF line 60 wording "including both profitable and losing Iran markets"). README line 39 (G38 +1,576,522.86) has the same issue: not Iran-specific (flipfloppity alone 232,895.40 on 348 markets of which 311 are non-military; Anon 59,937.29), and sum(result) minus sum(withdrawals minus deposits) is -43,988.35, i.e. 43,988 more was withdrawn than the result: unreconciled in the repo.

**M8. XFM consolidation counts.**
`financial-links-replay-2026-11-07/REPORT.md` line 106 says 19 of the 37 consolidated accounts are not among MSR's 18; `data/xfm_collectors.csv` gives 20 (17 of the 37 are in MSR's 18). VFF line 130 ("the matched trades are therefore between accounts whose balances end in the same wallet") holds for 8 of the 9 receipts: xfm-7-1, partner of xfm-8-1, is among MSR's wallets but not among the 37.

**M9. Railgun window.** `financial-links-replay-2026-11-07/REPORT.md` line 68: "between 18:54 and 20:29 UTC"; `data/railgun_maduro_edges.csv` gives 18:43:51 to 20:29:01 (six unshield receipts re-read on chain). Amounts, the 0.25 % fee and the closed-tree balance (21,977.51 + 66.65 residual + 0.006 dust = 22,044.17) recompute exactly.

**M10. KPMG shared deposit addresses.** VFF line 86 ("no outside payer identified in the studied Relay sample") omits that 0x1cefcfe8 receives 3,496.14 USD not matched to cohort Relay orders (replay REPORT line 49, "UNRESOLVED", mostly from 0x38c474e1). The sample is therefore not clean for that address.

**M11. Time of public information is not sourced for any case.** Phase 10 section 12 labels Maduro launch order ~03:46, first explosions ~06:00, Israeli announcement 06:23, authorisation 20:38 as APPROXIMATE or "VERIFIE" without a URL; the iran-exit-rarity catalogue uses 09:21 as the Maduro event time while the measured repricing is 06:15:41 to 06:16:11. `first_public_information_utc` is therefore null in all 9 registry cases (details inside each case).

**M12. iran-exit-rarity is a plan, not a result.** `research_notes/iran-exit-rarity-2026-11-06/`: frozen plan, `PROTOCOL.lock`, code and 74 synthetic positive-control tests only; no comparator data, no results file, no verdict. Nothing about rarity is demonstrated, and cluster-E `REPORT.md` section 9 rarity test (population chosen after the fact, no null model; 8 of 69 non-network wallets also share a destination) does not fill the gap.

**M13. Smaller points.**
- README line 45 / R-07: 1,984,038.17 USDC received and swept is reproduced by the repo verifier from archived logs, but coverage is not shown exhaustive (no per-range manifest).
- README line 38: Base legs rest on "later RPC check recorded in summaries, raw receipts not archived"; not independently re-read here.
- `external-polymarket-cases-2026-11-07/CASES.csv` C1 still says the Burdensome-Mix proxy is "unverified against eight-cohort"; the replay REPORT line 123 treats 0x31a56e9e as the SDNY/CFTC account "already reconciled in PR 12" (PR not in this checkout). Registry amounts are only approximate matches to the DOJ press figures (capital 32,538.34 vs about 33,034; market PnL 404,221.27 vs about 409,881).
- Biden pardon (VFF lines 115-117): withdrawal totals are exact (483,991.868223; 453.947234 outside funder) but 22 of the 25 go through a Uniswap pool and the traded market is not identified in the repo data; the registry case uses the catalogue's biden-pardon-fauci entry as an assumption, flagged.
- `inca-crosscheck-2026-11-06/data/flows.csv` has 7,596 rows but only 4,381 distinct (wallet, type, time, amount, hash) tuples (3,215 exact duplicate rows, one tuple repeated 344 times: batch transactions). Any count or sum taken from it without de-duplication is inflated; the pulser-cashy index de-duplicates by hash (27 unique), so its figures are not affected.
- The kpmg-election-integrity note and `x-history` still use "insider" language in titles of third-party material; levels in them are the third party's.

## 3. Links dismissed earlier that later evidence could reopen

None is reopened by this audit; these are the places where the repo's own later evidence leaves the question open:
1. **flipfloppity.** Phase 2 files it as outside the 8-account network; later the 38-account cohort includes it, and `x-history` check A18 shows its 13 Jan Relay withdrawal followed the same minute by 0x12d5b13f funding "Anon". Exact-proxy overlap with the eight accounts is zero (recomputed), so no new edge to the 8 network; but the Maduro-window population is not independent of the Iran cohort (M6).
2. **KPMG 0x1cefcfe8** (`data/kpmg_shared_deposit_addresses.csv`, 3,496.14 unmatched): an outside payer is not excluded.
3. **mutualdelta / 0x899ecb22 (Base).** `iran_jan14_episode.csv` and REPORT section 5: funded from Base by a one-use key paid by 0x899ecb22, upstream UNRESOLVED (anti-bot explorer page). If that upstream resolves to a network wallet, the "pump-and-switch not demonstrated" conclusion changes.
4. **xfm-7-1 / xfm-8-1** (M8): the one pair whose partner is outside the 37 consolidated accounts.
5. **The TRON hubs of the 8-account network** (TA4chMzt, 35 senders): excluded as service, which is right under rule 4; a TRON-capable replay could show whether any sender is also a Polygon account of the cohorts. Not possible with the allowed sources.

## 4. Claim-state table

States: CONFIRMED (shown directly by reproducible data), SUPPORTED (converging, proof incomplete), NOT_DEMONSTRATED (the data do not show it; includes level labels stronger than the data), REFUTED, UNRESOLVED. Totals over 64 claims: CONFIRMED 26, NOT_DEMONSTRATED 7, REFUTED 3, SUPPORTED 25, UNRESOLVED 3. The "stated" column is the level the repo prints. Full notes, figures, wallets and sources per claim are in `claims_register.csv`.

| id | source:line | claim | stated | audit state |
|---|---|---|---|---|
| F-001 | FINDINGS.md:3 | Eight Polymarket accounts are linked by transfers of funds through 0x44b6f8de, 0xe9a7230f and TRON addresses | CONFIRMED | **SUPPORTED** |
| F-002a | FINDINGS.md:9 | Aggregate PnL of the 8 accounts = $509,993.24 | CONFIRMED | **CONFIRMED** |
| F-002b | FINDINGS.md:9 | External capital $151,084.40 and external outflows $660,708.94 (net +$509,624.54) | CONFIRMED | **SUPPORTED** |
| F-003 | FINDINGS.md:15 | The 8 accounts may be controlled by one person or a small group sharing wallets | HYPOTHESIS | **NOT_DEMONSTRATED** |
| F-004 | FINDINGS.md:21 | Timing of the bets may be compatible with prior information on two US military operations | HYPOTHESIS | **NOT_DEMONSTRATED** |
| F-005 | FINDINGS.md:27 | The service paying the network is identified as MoonPay (outcome B, strong but unproven) | SUPPORTED | **SUPPORTED** |
| F-006 | FINDINGS.md:33 | None of the 8 preregistered signals is exploitable out of sample (288 comparisons) | REFUTED | **NOT_DEMONSTRATED** |
| F-007 | FINDINGS.md:39 | SIG_HIST precedes moves: LEAD60 30% vs 10-13% matched buys, reproduced in VALID and TEST | SUPPORTED | **SUPPORTED** |
| F-008 | FINDINGS.md:45 | Capturing the lead across all alerts is neither demonstrated nor refuted | UNRESOLVED | **UNRESOLVED** |
| F-009 | FINDINGS.md:51 | The second buy of a SIG_HIST wallet offers no executable window: -0.7% net in TEST | REFUTED | **NOT_DEMONSTRATED** |
| F-010 | FINDINGS.md:57 | Infrastructure not validated: live audit vs chain on 151,313 trades, 4 defects incl. RTDS false market | CONFIRMED | **CONFIRMED** |
| F-011 | FINDINGS.md:63 | 0x73e237f9 did not win on Maduro (July 30 conclusion false): no activity before 30 Apr 2026 | REFUTED | **CONFIRMED** |
| R-01 | README.md:29 | 38 distinct trading proxies; 36 created 22-25 Feb, NO then YES between 20:49 and 23:35 UTC on 27 Feb | recorded observation | **CONFIRMED** |
| R-02 | README.md:35 | 32 direct Polygon proxy senders to 0xc5bb1be0... | CONFIRMED on Polygon | **CONFIRMED** |
| R-03 | README.md:36 | 3 accounts via Relay on Polygon, 12 individually matched USDC credits | SUPPORTED (order/receipt) | **SUPPORTED** |
| R-04 | README.md:37 | Arbitrum: 1 account, matching receipt; onward attribution not established | SUPPORTED | **SUPPORTED** |
| R-05 | README.md:38 | Base: 2 accounts documented by Relay; later RPC check in summaries | Relay-reported | **SUPPORTED** |
| R-06 | README.md:39 | Combined recorded trading result +$1,576,522.86 with eight accounts still holding shares | recorded measure | **CONFIRMED** |
| R-07 | README.md:45 | Recipient received and swept 1,984,038.17 USDC/USDC.e (5 Jan-9 Mar 2026); exchange-style deposit wallet; not one verified Coinbase customer | gross flow | **CONFIRMED** |
| R-08 | README.md:47 | flipfloppity -> 9,990.03 USDC via Relay -> intermediary -> proxy provisionally 'Anon' | financial link | **SUPPORTED** |
| R-09 | README.md:65 | chileno777 -> TacticalInsiderNews; Mrs.Joker -> Planktonbets; X34 -> intermediate Ethereum address -> Mrs.Joker | documented relationships | **CONFIRMED** |
| R-10 | README.md:83 | Eight-account numbers: PnL +509,993.24; capital 151,084.40; outflows 660,708.94; net +509,624.54 | figures | **SUPPORTED** |
| R-11 | README.md:103 | Frogensky 101.64, JamWil23 9,962.37, bravonoll 42,858.47 USDC routed through Relay to 0xd1262395... | shared destination | **SUPPORTED** |
| R-12 | README.md:115 | flydartball: 359,679.08 YES before repricing; account result +$841,375.23 | reconstructed | **SUPPORTED** |
| V-1a | VERIFIED_FINANCIAL_FINDINGS.md:16 | 32 cohort proxies transferred official USDC/USDC.e to 0xc5bb1be0 | CONFIRMED | **CONFIRMED** |
| V-1b | VERIFIED_FINANCIAL_FINDINGS.md:21 | Entry-side: 86 Relay deposits from 39 distinct funding wallets, none reused by two cohort proxies | observed | **CONFIRMED** |
| V-1c | VERIFIED_FINANCIAL_FINDINGS.md:27 | Common Coinbase customer-account / beneficial-owner hypotheses remain UNRESOLVED; trading-synchrony significance unmeasured | UNRESOLVED | **UNRESOLVED** |
| V-2 | VERIFIED_FINANCIAL_FINDINGS.md:33 | Eight financially connected accounts, verified value-transfer paths on Polygon, Ethereum and TRON | verified | **SUPPORTED** |
| V-3 | VERIFIED_FINANCIAL_FINDINGS.md:50 | Receiving address got gas from a Coinbase hot wallet and swept to Coinbase Hot Wallet 10 | SUPPORTED | **SUPPORTED** |
| V-4 | VERIFIED_FINANCIAL_FINDINGS.md:58 | flydartball: 359,679.08 YES shares before repricing; June 2025 +256,137.07; whole account +841,375.23 | reconstructed | **SUPPORTED** |
| V-6a | VERIFIED_FINANCIAL_FINDINGS.md:83 | 22 of 22 accounts resolved to Polygon proxies | SUPPORTED/CONFIRMED | **SUPPORTED** |
| V-6b | VERIFIED_FINANCIAL_FINDINGS.md:84 | 14 withdrawal->deposit handoffs matched by Relay keys on Polygon and Solana (11 published + 3), 18-50 s | CONFIRMED | **CONFIRMED** |
| V-6c | VERIFIED_FINANCIAL_FINDINGS.md:86 | 7 shared withdrawal destinations classified as exchange-style deposits; no outside payer in the studied Relay sample | SUPPORTED | **SUPPORTED** |
| V-6d | VERIFIED_FINANCIAL_FINDINGS.md:87 | Original 19 accounts: 20/21 aggregate main-side wins, 18/21 every-account; expanded 22: 20 / 17 | descriptive | **CONFIRMED** |
| V-6e | REPORT.md:0 | (replay report) Biggest-stake rule 20/21, exact tail p=0.00116; every-account 18/21, p=0.040; Sidak 0.0046 / 0.15 | inferential | **NOT_DEMONSTRATED** |
| V-6f | REPORT.md:0 | Bitquery: 19 winning markets of 21, p=0.0084; 11 handoffs; 0xafed93e1... is Youaregu's last transfer | THIRD-PARTY | **REFUTED** |
| V-7a | VERIFIED_FINANCIAL_FINDINGS.md:101 | Railgun unshield events on 16 Dec 2025 to six distributor wallets: 22,044.16 USDC | CONFIRMED | **CONFIRMED** |
| V-7b | VERIFIED_FINANCIAL_FINDINGS.md:103 | 71 Relay deposits each crediting a new Polymarket account; 66 lost, 5 won; winning shares never redeemed 53,113.16 | CONFIRMED | **CONFIRMED** |
| V-7c | VERIFIED_FINANCIAL_FINDINGS.md:109 | None of the 71 accounts appears in the eight-account network; common operator of the tree SUPPORTED not proven | SUPPORTED | **SUPPORTED** |
| V-8 | VERIFIED_FINANCIAL_FINDINGS.md:115 | Withdrawals of two proxies (16 + 9) total 483,991.868223 USDC and reach 0x0a65fdd8... | CONFIRMED | **CONFIRMED** |
| V-8b | VERIFIED_FINANCIAL_FINDINGS.md:117 | Address not exclusive: extra 453.947234 USDC from 0xf5042e6f... | CONFIRMED | **CONFIRMED** |
| V-9a | VERIFIED_FINANCIAL_FINDINGS.md:123 | Nine published receipts, 1,779.93 shares on each side, two-party mint matches | decoded | **CONFIRMED** |
| V-9b | VERIFIED_FINANCIAL_FINDINGS.md:123 | On 15 Oct 2026, 37 accounts of series 5-8 withdrew to two Polygon wallets (20 + 17) | CONFIRMED | **CONFIRMED** |
| V-9c | VERIFIED_FINANCIAL_FINDINGS.md:130 | The matched trades are therefore between accounts whose balances end in the same wallet | SUPPORTED | **SUPPORTED** |
| V-10 | VERIFIED_FINANCIAL_FINDINGS.md:136 | 11 Relay orders from four accounts: 70,065.262869 USDC.e debited, 856.840698827 SOL to the same Solana beneficiary; 842.687802663 SOL to a Bybit depos | CONFIRMED | **CONFIRMED** |
| V-10b | VERIFIED_FINANCIAL_FINDINGS.md:138 | 19-account cluster E: account-to-account payment paths and shared exchange deposit destinations; exchange classification relies on Blockscout labels a | SUPPORTED | **SUPPORTED** |
| V-10c | VERIFIED_FINANCIAL_FINDINGS.md:138 | A Privacy Cash withdrawal shortly after a deposit is not cryptographically attributed to those coins | limit | **CONFIRMED** |
| V-11a | VERIFIED_FINANCIAL_FINDINGS.md:144 | Two exact address intersections between Inca's five June 2025 wallets and the Feb 2026 network: 9TungSahur (=TheOneWhoKnocks1312) and DonkeyDonkey999 | CONFIRMED | **CONFIRMED** |
| V-11b | VERIFIED_FINANCIAL_FINDINGS.md:144 | 65,992.25 USDC paid by three network accounts into the same Bybit-classified deposit address on 13 June 2025, 01:42-02:27 UTC | SUPPORTED | **SUPPORTED** |
| V-11c | VERIFIED_FINANCIAL_FINDINGS.md:146 | ricosuave666's four Solana-bound exits converge on one beneficiary; AugsburgFClover and metushelah on the same personal wallets; indictment figures ma | SUPPORTED/compatible | **SUPPORTED** |
| V-12 | VERIFIED_FINANCIAL_FINDINGS.md:152 | 25 distinct hash payments between Pulser and cashy (13,449.999999), 250 USDC cashy->Car, 1,000 comparator: 27 tx / 14,699.999999 | CONFIRMED | **CONFIRMED** |
| N-01 | REPORT.md:0 | Two more accounts paid the same beneficiary (oveiStheair, aaamsaasa): 59,361.2479 USDC.e = 84.7 % of what the beneficiary received | recomputed | **CONFIRMED** |
| N-02 | REPORT.md:0 | Cluster E is a network of at least 19 accounts; one operator is a hypothesis | SUPPORTED/HYPOTHESIS | **SUPPORTED** |
| N-03 | REPORT.md:0 | Behaviour checks use Blockscout labels (erratum); Bybit EVM address also forwards USDT0 | erratum | **CONFIRMED** |
| N-04 | analysis_plan.md:0 | Frozen plan: how rare is the cluster-E exit structure among comparable early buyers? | plan only | **NOT_DEMONSTRATED** |
| N-05 | REPORT.md:0 | Downgrade '38 financially proven to one Coinbase customer account' to 35 Polygon payout paths + 1 Arbitrum + 2 Base | audit decision | **CONFIRMED** |
| N-06 | RAPPORT_PHASE2_2026-09-29.md:0 | Network not distinguished by price or timing; distinguished by size (128-buyer Iran window) | MESURE | **SUPPORTED** |
| N-07 | RAPPORT_2026-09-29.md:74 | Iran price 0.135 at 05:00, first rise at 05:28 (0.135 -> 0.205) | MESURE | **REFUTED** |
| N-08 | RAPPORT_PHASE10.md:0 | Event times: Maduro launch order ~03:46, first explosions ~06:00, repricing 06:15:41-06:16:11, Trump announcement 09:21; Iran authorisation 27 Feb 20: | APPROXIMATE / MESURE | **UNRESOLVED** |
| N-09 | REPORT.md:0 | '38 of 38 resolved; all 38 pay one Coinbase deposit address; pooled-service hypothesis rejected' | SUPPORTED | **REFUTED** |
| N-10 | REPORT.md:0 | cashy bought YES before the news: REFUTED (0 YES shares at the 06:13:22 repricing; first YES fill 33 s after) | REFUTED | **SUPPORTED** |
| N-11 | REPORT.md:0 | Bitquery's nine Iran accounts: 81 counterparties, none shared with the 38 cohort, the 8-account network, PR 27 network or Inca; binance deposit 0x68c3 | REFUTED link | **SUPPORTED** |
| N-12 | REPORT.md:0 | mutualdelta (YES whale) and X34: coordinated pump-and-switch not demonstrated; 'one account buying all the NO' REFUTED | NOT DEMONSTRATED | **NOT_DEMONSTRATED** |
| N-13 | REPORT.md:0 | Pulser/Car/cashy, JamWil23, PURE698, SBET365 ledgers (b2 check) | recomputed in verify B2 | **CONFIRMED** |

## 5. Limits

- Spot check, not replay: receipts for sampled hashes; TRON, Solana, Arbitrum, Base and Relay-API legs were not re-read; the Maduro report hashes use a 1-hour time tolerance because the report gives minute-level times for mixed legs.
- Phase 8 to 14 tapes and the live-listener data are not in the repo: signal results were read, not recomputed.
- Profile text of Polymarket accounts is not reproduced in any deliverable beyond handles already printed in repo files.
- No claim of the repo was changed or annotated; this folder only reports.
