# GitHub tooling audit for the Polymarket investigations: what is new, what was tested, what was integrated

Date: 6 November 2026. Branch `research/github-forensic-tooling-20261106`, created from `main` at `17acd34`. No README, no investigation folder and no other session's branch is modified by this note.

Every figure below is recomputed offline by `verify.py` from this folder only: `python3 -I verify.py` (last run: 32 of 32 checks, `verification.json`). The fixtures are byte-identical copies of evidence committed in PR 27 at `cbbdd64`, listed with their SHA-256 in `fixtures/FIXTURES.json`.

## 1. Starting point

What the repository already does, read before searching:
- **Relay.** Cross-chain links were proven by the Relay API (`requests/v2?hash=` and `?user=`), the Polygon receipt and the Solana memo. Discovery of further accounts (PR 27, 19 accounts) rests on `requests/v2?user=`. That endpoint is announced as retired on **24 November 2026**.
- **Solana.** Helius `getTransactionsForAddress` with archived pages, and the offline decoder `flows.py`. Privacy Cash was read at one offset of the instruction data (`ext_amount` at byte 488), without a check of the deployed version.
- **Polymarket.** Data API v2 activity with `exclude_deposits_withdrawals=false`, then links proven by a shared transaction hash.
- **PR 11** screened 75 repositories at metadata level and shortlisted 12 at code level. **PR 12** built flow graphs and a synchronisation study. **PR 26** fixed ChangeNOW pagination. **PR 27** holds the Iran cluster E network, with a frozen rarity test (`PLAN_RARITY.md`, 17 of 115 wallets share a withdrawal recipient).

## 2. A. Audit of the repositories

All of them were read at the pinned commit, and none was executed. "Capability" means code that was found and cited, not a README claim. The detailed notes, with file and line references, are in `audit_notes/`. They are code-reading notes written by sub-agents, and only the rows marked **tested** were run against our data.

| Rank | Repository, commit | License (file) | Capability actually implemented | Limits | Decision |
|---|---|---|---|---|---|
| 1 | relayprotocol/relay-settlement `b2f3e0e` (2026-09-11) | none at the root; `package.json` has no license field | `RelayDepository.sol`: `RelayErc20Deposit(address from, address token, uint256 amount, bytes32 id)` and `RelayNativeDeposit`; production address `0x4cd00e38…bc31` in `deployments/addresses.prod.json` | Shallow history; the bytecode at that address was not compared with the source. The event signature is confirmed by its Keccak topic on 15 of 15 archived Polygon logs | **Tested, integrated as a method** (`scripts/relay_onchain.py`, own code). No code copied |
| 2 | Privacy-Cash/privacy-cash `f79b82f` (2026-09-29) | **BSL 1.1**, GPL-2.0+ on 27/12/2027 | `transact` arguments, `Proof` and `ExtDataMinified` layout, `CommitmentData{index, commitment, encrypted_output}` event, height-26 tree with 100 roots of history (`anchor/programs/zkcash/src/lib.rs`) | Non-production license: layout used as a reference, no code copied. The commit deployed in February is inferred from dates (section 4.3) | **Tested, integrated as a method** (`scripts/privacy_cash.py`, own code) |
| 3 | Privacy-Cash/privacy-cash-sdk `769e2b5` (2026-11-05) | no LICENSE file | Client and relayer calls to `api3.privacycash.org` | Off-chain service; reveals nothing the chain does not | REFERENCE |
| 4 | relayprotocol/relay-protocol-oracle `55b22de` (2026-08-12) | MIT (`package.json`) | Settlement oracle service of the newer Relay hub | Not the path used by Polymarket withdrawals in February | REFERENCE |
| 5 | relayprotocol/relay-kit | MIT | Quote and route client | Screened in PR 11, no historical identifier | REFERENCE (unchanged) |
| 6 | l2beat/l2beat interop plugins `3197d43` (2026-11-05) | MIT | Leg matching by protocol id for Mayan, deBridge DLN, CCTP v2, Across; a collector that aborts on a repeated or empty cursor | Its Relay plugin reads the retiring API; its Solana leg is one-sided | ADOPT-CANDIDATE for keys and test vectors of other bridges |
| 7 | XChainDataGen/XChainDataGen `5ab9299` (2026-09-24) | no LICENSE file (README badge only) | Mayan order-hash rebuild, Solana-to-EVM joins for Mayan and deBridge | Hard-coded instruction offsets; Postgres and Docker | REFERENCE until the license is confirmed |
| 8 | prettydeath/TornadoCash-demixer `cc30ba7` (2026-10-29) | MIT | Deposit-address classifier (Victor forwarding test) and a decoy-window baseline | EVM only, Etherscan-style paging; self-reported accuracy | ADOPT-CANDIDATE, offline test not yet run |
| 9 | Ikey168/Noesis `onchain_clustering.py` `e4ae131` (2026-11-05) | MIT | Hub-size edge weight `1/(hub-1)`, degree-preserving shuffle null with 200 permutations | Assumes exchangeable memberships; synthetic calibration | ADOPT-CANDIDATE, to re-implement for section 6 |
| 10 | shottah/tracer `3a8a03c` (2026-09-27) | MIT or Apache-2.0 | Internal native transfers from a callTracer tree; prestate balance diffs | Needs a debug or archive node; no EIP-7702 or ERC-4337 decoding; never tested on Polygon | REFERENCE, conditional pilot |
| 11 | helius-labs/helius-sdk `e421446` (2026-11-05) | MIT | `getTransactionsForAddress` (raw transactions) and `getTransfersByAddress` (server-side parse with instruction indices) | Thin pass-throughs; no completeness signal beyond a null `paginationToken` | REFERENCE; `getTransfersByAddress` is a possible second decoder |
| 12 | Polymarket/py-sdk `ddee30c` (2026-11-05) | MIT | Data API v2 wrappers with an envelope check (`has_more` against `next_cursor`) | Drops unknown fields; no proxy-to-owner resolution | REFERENCE; its docs gave the TIP finding of section 4.4 |
| 13 | enviodev/polymarket-v2-indexer `0da9e5c` (2026-08-11) | none | V2 exchange fills and pUSD events from block 84,902,320 | No V1 exchange, no USDC.e: it cannot cover February 2026 | REFERENCE |
| 14 | Xda1Dan/wallet-forensics `540a5be` (2026-09-21) | MIT | Look-alike address scoring (prefix 8, suffix 6 hex) | Silent caps at 5,000 rows and 100 pages; Relay through the retiring API | REJECT as a tool, idea kept |
| 15 | veeradittya/polymarket-insider-detection `df957ea` (2026-06-12) | none | Isolation Forest, RRF, Leiden on 5-minute co-trading buckets, GDELT GKG anchoring | Features chosen after seeing the target case, no holdout or null model, data not published | REFERENCE (ideas only); its scores are not evidence |
| 16 | Kowalskk/polyMARKET_data, Polymarket/real-time-data-client, sfrbuilds/polymarket-wallet-analyzer | GPL-3 vs MIT conflict / MIT / none | One exchange only; deprecated feed; v1 offset paging that no longer works | | REJECT |

PR 11 already covered 75 repositories. Of the rows above, only relay-kit was in it. The broad search (`audit_notes/broad_discovery.md`) found nothing usable for privacy-pool anonymity sets, temporal graph anomalies, or content-addressed evidence archives.

## 3. B. Comparison with our system

| Need | Before | Now | Gain |
|---|---|---|---|
| Link a Polymarket withdrawal to its Solana payment | Relay API record, plus receipt and memo | Depository log `id` equals the Solana memo, read on both chains | Same 11 of 11 links without the API (section 4.1) |
| Find who paid a Solana recipient through Relay | `requests/v2?user=` (retiring 24/11) | Recipient history, then memo, then Polygon `eth_getLogs` window | 11 of 11 origins found live with 43 keyless calls (section 4.2) |
| Find where a Polymarket withdrawal into Relay was paid on Solana | `requests/v2?hash=` (retiring 24/11) | Depository log `id`, then the solver's Solana transactions in the next 180 s | 11 of 11 recipients found live, 40 calls (section 4.2) |
| Read Privacy Cash | `ext_amount` at offset 488 | Full byte-exact decode of `transact`, leaf indices from events, deployed version from `programdata` | New facts on the pool sequence (section 4.3) |
| Polymarket activity completeness | default feed with deposits and withdrawals | `type=TIP` checked explicitly | Gap identified and shown empty for the case (section 4.4) |
| Relation strength vs shared services | labels, behaviour checks, manual service exclusion | unchanged; hub-size null proposed (section 6) | not yet demonstrated |

## 4. C. Tests

### 4.1 Experiment A offline: the chain-only key

`scripts/experiment_a_offline.py` decodes `RelayErc20Deposit` logs from the 20 archived Polygon receipts and the 32-byte memos from the archived history of `4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy`, joins them on `id`, then compares with the 11 archived Relay API records (`results/experiment_a_offline.json`).

| Measure | Result |
|---|---|
| Orders matched from chain data only | 11 of 11; no Relay fill to the beneficiary without an origin deposit |
| Depositor equals the API `user` | 11 of 11 |
| Solana signature equals the API `outTxs` | 11 of 11 |
| Log amount equals the USDC.e Transfer to the Depository | 11 of 11 |
| Totals | 70,065.262869 USDC.e and 856.840698827 SOL, the figures of PR 27 |
| Last 32 bytes of the Polygon calldata equal the id | **0 of 11** |
| API request `id` equals the chain `id` | **0 of 11** |
| Cost | 0 requests, 0.18 s, 3.9 MB of Python memory |

Two traps follow from the last rows:
- The calldata tail identifies a Relay *fill* on an EVM chain. It does not identify a Polymarket *withdrawal* into Relay, which goes through the proxy's own call.
- The API's request `id` is another value. A join on it finds nothing.

Tamper control: replacing one memo by zeros makes the join lose exactly that order (`verify.py`).

### 4.2 Experiment A live: discovery without the Relay API

`scripts/experiment_a_live.py` takes from the Solana side only the memo `id` and the block time of each fill, maps the time to a Polygon block, and scans `eth_getLogs` windows on the Depository backwards from it. Run on 6 November 2026 against `https://polygon.drpc.org`, keyless, one worker; every response is in `evidence/polygon_live/` with its SHA-256.

| Measure | Result |
|---|---|
| Origins found | 11 of 11, each with the archived transaction, depositor and amount |
| RPC calls | 43 (11 `eth_getLogs`, the rest block lookups) |
| Depository logs scanned | 1,142 |
| Data | 1.33 MB, 41 s |

Limits measured on that endpoint:
- The free plan refuses `eth_getLogs` over 200 blocks with a misleading message ("ranges over 10000 blocks"), so windows are 100 blocks.
- `polygon-bor-rpc.publicnode.com` refuses historical logs without a token.
- Depository traffic was about one deposit per block in February 2026, so a wide window downloads many unrelated logs.

**Forward direction**: from a Polymarket withdrawal to an unknown Solana recipient. `scripts/experiment_a_forward.py` starts from the 15 Depository logs of the archived receipts, reads each block's time from Polygon, and pages through Helius `getTransactionsForAddress` for the solver key in `[t, t + 180 s]`. It returns the account credited by the transaction whose memo is the `id`. It was run on 6 November 2026, with one worker.

| Measure | Result |
|---|---|
| Recipient found for the 11 orders to the beneficiary | 11 of 11, with the archived fill signature |
| Other orders | the 2 orders to `CCQQKc4v…` found (token owner credited); 2 not found, both Polygon-to-Polygon orders (archived API records), so their fill is not on Solana: an expected negative |
| Cost | 40 calls (15 Polygon block reads, 25 Helius pages of 100 transactions, 1,767 solver transactions scanned), 19.2 MB, 102 s |

In git, only the 16 matched transactions are kept (13 distinct, some windows overlap) and the list of pages with their SHA-256 (`evidence/forward_live/`). The full pages are third-party traffic and stay outside git.

Limits of the forward method:
- **Solver keys.** The 11 fills were all paid by one key, `F7p3dFrjRTbtRp8FRF6qHLomXbKRBzpvBLjtQcfcgmNe`. Another archived Relay fill of PR 27 (to `4H4WacXe…`) was paid by a different key, so a general search must cover several solver keys, and a miss on one key is not an absence.
- **Swaps inside the fill.** On SOL fills, token accounts of a swap route are credited too. The recipient is the account credited in lamports for SOL and the token owner for SPL tokens; reading the final transfer instruction would be stricter.
- **EVM destinations** (BSC, Polygon) are not covered: there the fill's calldata ends with the `id`, which needs a search of the solver's EVM transactions.

### 4.3 Privacy Cash: byte-exact decoder and deployed version

`scripts/privacy_cash.py` decodes `transact` field by field, refuses any instruction whose bytes are not consumed exactly, and checks that the two `CommitmentData` events echo the proof's output commitments. On the three transactions of PR 27, it consumes 694, 696 and 695 bytes out of 694, 696 and 695.

| | Beneficiary deposit 1 | Beneficiary deposit 2 | Withdrawal to the Bybit deposit address |
|---|---|---|---|
| UTC | 28/02 14:50:06 | 14:54:50 | 14:55:19 |
| `ext_amount` (lamports) | +119,021,900 | +12,328,800,200 | −990,500,000, fee 9,500,000 |
| Leaf indices | 346,804 and 346,805 | 346,814 and 346,815 | **346,816 and 346,817** |

Each SOL-pool `transact` appends exactly two leaves (`lib.rs`), so:
- **No other SOL-pool transaction ran between the 12.33 SOL deposit and the withdrawal to the beneficiary's Bybit deposit address.**
- Four other pool transactions ran between the two deposits.
- The three proofs reference three different Merkle roots.

This is not a cryptographic link. The withdrawal may spend any unspent note of value at least 1 SOL in the tree, and the tree then held 346,816 leaves. Whether its root is the one produced by inserting the 12.33 SOL deposit would show whether that note was even spendable. Answering it requires rebuilding the Poseidon tree from all 346,816 earlier commitments, which was not done (section 7).

Deployed version, read on chain (`evidence/solana_program/`):
- The program's `programdata` was last written at slot 427,378,345 (18 June 2026), after the case.
- Its previous write is slot 399,466,617 (11 February 2026, 04:11 UTC). Nothing was written between the two, so the bytecode executing on 28 February is the one deployed on 11 February.
- The closest source commit is `0bd1889` (10 February, "Support jlUSDC and jlWSOL"). Between `0bd1889` and the current head, `lib.rs` differs only in the list of allowed SPL tokens; `transact`, `Proof`, `ExtData` and `CommitmentData` are unchanged. The match between that commit and the deployed bytecode is inferred from dates, not from a verifiable build.
- The byte-exact parse of the three February transactions is the direct evidence that the layout applies to them.

### 4.4 Polymarket completeness: the TIP rows

The Data API v2 documentation states that, when `type` is omitted, "the feed returns every type except `TIP`" (user-to-user pUSD transfers). PR 27 collected activity without `type`, so direct transfers of that kind could have been missed.

Test: `scripts/collect_tip.py` queried `type=TIP&start=1` for the 25 accounts of the Iran notes and the 115 wallets of the frozen population: 125 distinct addresses, sequentially, no errors (`evidence/tip_summary/tip_summary.json`).
- **Positive control:** 9 population wallets have TIP rows (261 rows), so the query works.
- **Result: none of the 25 accounts has a TIP row.** The earliest TIP row in the sample is dated 24 July 2026. The omission therefore lost nothing for the February case.
- TIP rows carry no counterparty field. A counterparty must be read from the transaction, or from the same hash in the other wallet's rows: 0 of 261 hashes are shared between two queried wallets.
- Row-level data of third-party wallets is kept outside git; `ORIGINALS.json` lists each original page with its SHA-256.

### 4.5 Not run

- **Experiment B as specified** (on-chain reconstruction of the proxies' pUSD and USDC.e flows against the activity feed, on the network and a control set). No audited indexer covers February 2026: envio starts at block 84,902,320, after the case's Polygon block 83,584,716, and has no V1 exchange or USDC.e. The method is written down (pUSD `Transfer` logs at `0xC011a7E1…`, topic1 or topic2 equal to the proxy) but needs a log source over the whole period. With the free endpoint above, that means about 100 blocks per call.
- **Helius `getTransfersByAddress`** as a second Solana decoder: credit cost not documented, not run.
- **Polygon internal traces** (shottah/tracer): no debug-capable node available for free.

## 5. D. Integrated

Only code whose gain is shown above, all written here with the standard library:
- `scripts/keccak.py`: Keccak-256, checked on two known vectors and on 15 of 15 archived Relay logs.
- `scripts/relay_onchain.py`: Relay Depository log decoder, Solana memo extractor, join on `id`, and live origin search. It fails closed on any change of event layout.
- `scripts/experiment_a_forward.py`: the solver-window search for the forward direction (`recipient_of`).
- `scripts/privacy_cash.py`: Privacy Cash `transact` and `CommitmentData` decoder, failing closed on any change of layout.
- `scripts/collect_tip.py`: sequential collector for the activity type that the default feed omits. It checks the pagination envelope and keeps identical filters on every page.

## 6. Rarity of a shared exit: protocol proposed, not run

The frozen test of PR 27 counts groups and rules out a p-value. That is correct for a population chosen after the fact. A defensible rate needs a new plan, frozen before any data:
- **Unit.** The withdrawal recipient, not the pair of wallets. A recipient shared by k wallets is one event, so pairs are never counted as independent.
- **Populations.** For each comparator market, the wallets of the same early-buyer window and amount threshold, chosen on having traded, not on having won. The comparators are matched on period, collateral and size, and include markets where no allegation exists (negative controls).
- **Recipient classes.** These are fixed before collection: exchange customer deposit addresses, shown by the gas funder and full sweeps; per-customer wallets; shared services, which are reported but not merged. Each shared recipient is weighted `1/(k-1)`, from Noesis.
- **Null model.** Degree-preserving shuffle of wallet-recipient memberships within each market, stratified by recipient class.
  - This tests whether sharing exceeds what each recipient's popularity predicts.
  - It does not model one operator running many wallets, so a positive result is excess sharing, not common control.
- **Positive control before freezing.** A planted group of wallets sharing two recipients, inserted into a comparator market. The test must detect it.
- **Censoring.** Report wallets without any visible withdrawal as censored, never as zero sharing.
- **Deadline.** Collecting comparator markets is simplest with `requests/v2?user=` until 24 November 2026. After that, the chain-only methods of section 4.2 take over: the forward method for Solana destinations is tested, EVM destinations are not.

## 7. Limits and what would resolve them

- **Privacy Cash root.** It would be settled by rebuilding the Poseidon tree from all commitments up to leaf 346,815. That means about 173,000 pool transactions, which is heavy in credits and time, and Poseidon is not in the standard library. Until then, the relation of section 4.3 stays a supported, temporal one.
- **Relay EVM destinations and other bridges.** These need tests. l2beat's plugins hold test vectors for Mayan, DLN and CCTP.
- **Labels.** The labels of PR 27 are unchanged. A label is not proof of control.
- **Untested repositories.** Each rank in section 2 not marked "tested" is a reading of code at a commit, and its claims were not reproduced here.

## 8. Reproduction

- `python3 -I verify.py`: needs only this folder, no network.
- `python3 -I scripts/experiment_a_offline.py fixtures/iran-solana-beneficiary results/a.json`
- `python3 -I scripts/experiment_a_live.py fixtures/iran-solana-beneficiary <raw_dir> <out.json> [rpc_url]`: network, one worker, about 45 calls.
- `python3 -I scripts/experiment_a_forward.py fixtures/iran-solana-beneficiary <raw_dir> <out.json>`: network, Helius keys from the local pool (never written), about 40 calls.
- `python3 -I scripts/collect_tip.py <out_dir> <addresses.txt>`: network, one request per address.

Raw material kept outside git: TIP pages and GDELT and Wayback responses, under `/Volumes/TravailExterne/Enquetes-Crypto/tooling_audit_20261106/raw/`, plus third-party source files read for the audit.
