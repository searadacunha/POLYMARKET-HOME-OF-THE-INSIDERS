# Code-level audit: helius-sdk, wallet-forensics, tracer (2026-11-06)
Method: source read only (shallow clones under clones/<owner>__<repo>), nothing executed or installed. Test files are counted, not run. Paths below are relative to each clone.

## 1. helius-labs/helius-sdk
- Pin: e4214462335b2b85269550619045ee9695b296d2, 2026-11-05T17:39:07-05:00, v3.4.0 (package.json:3). 3.2 MB.
- License: LICENSE = MIT (Helius Blockchain Technologies, 2025); package.json:146 "MIT". Consistent.
- Nature: TypeScript SDK. The two methods are 26-line and 17-line pass-throughs (src/rpc/methods/getTransactionsForAddress.ts:22-26, getTransfersByAddress.ts:11-17) that call JSON-RPC `getTransactionsForAddress` / `getTransfersByAddress` via src/rpc/caller.ts. All semantics live server-side at Helius; the SDK only supplies types (src/types/types.ts) and JSDoc. Nothing is decoded locally.

### getTransactionsForAddress (types.ts:274-398)
- Params: commitment, minContextSlot, encoding json|jsonParsed|base64|base58, maxSupportedTransactionVersion (0|1), limit (no max in SDK; docs example uses 100), paginationToken (:287), sortOrder asc|desc (:289), transactionDetails signatures (default) | full (:353-363).
- Filters (:291-345): status succeeded|failed|any (:293); tokenAccounts none|balanceChanged|all (:300; semantics in AGENTS.md:254-262); tokenTransfer {with, direction, mint, amount} (:303-312, added in CHANGELOG #381); slot and blockTime with eq/gte/gt/lte/lt (:326); signature lexicographic range.
- Pagination: result `{data, paginationToken: string|null}` (:390-398). Comment at :286: "null when no more pages". Last page = null token; the SDK adds no truncation flag. Opaque token, not a slot+index cursor, but each row carries slot and transactionIndex (:373,383), so ordering can be checked offline.
- Full mode returns `transaction` and `meta` (:380-386), which is the raw getTransaction shape. Inner instructions, pre/post token balances and logs are available to re-verify offline. This is what we already archive.
- Credit cost: NOT documented in the SDK for this method (grep of README/AGENTS/llms.txt finds credit figures only for parsedEvents, README:305-307). Not verified.
- Default status filter when omitted: not stated in SDK. Not verified. Our collector sets it explicitly.

### getTransfersByAddress (types.ts:401-503)
- Params: address, `with` (counterparty), direction in|out|any, mint, solMode merged|separate, filters {amount, blockTime, slot} (gt/gte/lt/lte; raw amount), limit, paginationToken, commitment finalized|confirmed, sortOrder.
- Result TokenTransfer (:470-497): signature, slot, blockTime, type (transfer|mint|burn|wrap|unwrap|changeOwner|withdrawWithheldFee), fromUserAccount/toUserAccount (owner wallets), fromTokenAccount/toTokenAccount, mint, amount (raw string), decimals, uiAmount, Token-2022 feeAmount/feeAccount, confirmationStatus, transactionIdx (:492), instructionIdx (:494), innerInstructionIdx (:496, 0 = top-level).
- So a decoded transfer CAN be tied to signature + instruction index + inner index, but only per the Helius server's own parse. Whether inner/CPI transfers and token-account transfers are included is implied by innerInstructionIdx and by the owner fields, but the SDK has no statement of coverage and no failed-tx flag. Not verified from source.
- Last page: paginationToken null. Credit cost: not documented in the SDK.
- Related (README:305-307): parsedEvents.getTransactionHistory with `rawTransaction` json/jsonParsed/base64 returning parsed and original tx together, 10 credits/request; scan() 10 credits + 1 per 1000-tx page. Enhanced Transactions API is marked Deprecated (README:311-). wallet-forensics uses that deprecated API.

Tests: 2 files (getTransfersByAddress.test.ts 114 lines, getTransactionsForAddress.test.ts 130 lines); they check request shaping. Cannot say they pass.
Risks: key in URL/header as with any Helius call (not our code path); a server-side parse is a black box, so a transfer list can not substitute for the raw archive; no documented truncation signal besides token null.
Advantage over our system: none for getTransactionsForAddress (we already call it with full details and archive pages). getTransfersByAddress gives a cross-check: a server-decoded list with instruction and inner index to compare against flows.py.
Cost: unknown for these two methods (not in SDK). Decision: REFERENCE. Optional use: `getTransfersByAddress` as a second, independent decoder for spot-checks. Offline test on archived data: take 20 signatures from the archive, diff flows.py transfers (from/to/mint/amount, instruction index) against that API's rows. That needs a live call, so it is not offline, and costs credits. The parameter list in types.ts:274-345 is worth diffing against our collector config once.

## 2. Xda1Dan/wallet-forensics
- Pin: 540a5be65fbdf953b1e0691af6cbf3613640f7f0, 2026-09-21T00:40:43+03:00. 444 KB, ~4,650 lines incl. tests. v0.1.0 (pyproject.toml).
- License: LICENSE = MIT, "Copyright (c) 2026 wallet-forensics contributors"; pyproject.toml license text "MIT". User belief confirmed.
- Nature: a small agent-driven CLI (kit.py -> forensics/cli.py) built for "tracing how a wallet was drained". Python, single dependency `requests`.

### What is real
- EVM transfer history: forensics/evm.py:203-231 `Alchemy.transfers` calls `alchemy_getAssetTransfers` (categories external, internal, erc20, erc721, erc1155; evm.py in abi.py:40), fromBlock 0x0, maxCount 0x3e8, pageKey loop. Requires ALCHEMY_KEY (paid-tier product with free quota).
- Silent truncation: evm.py:219 `while len(results) < cap` with cap default 5000 and NO flag when the cap stops the loop. evm.py:221-222 a failed page ends the loop and returns the partial list (`supported=True` -> returned at :229-230). The CLI exposes last_error only for the latest call (cli.py:117-125). A partial history looks complete.
- Solana (forensics/solana.py): Helius path uses the legacy, deprecated Enhanced API `api.helius.xyz/v0/addresses/<a>/transactions` with `before` cursor (:252-261), 100 per page. Stops silently at 100 pages or `cap` 2000 rows (:297); any error or empty page breaks the loop with no marker (:299-300). Rows come from Helius' pre-digested `nativeTransfers`/`tokenTransfers` (:313-334), which carry no instruction index. Keyless path: getSignaturesForAddress limit<=1000, then one getTransaction per signature (:217-239); flattens System transfer and SPL transfer/transferChecked from top-level plus inner instructions (:337-385) but does not read failed status and drops instruction indices. Does NOT handle createAccount funding transfers (flows.py does).
- Fund following: `flow` = same query as `transfers --dir from`, one hop only (cli.py:135-137). No recursion, no stop rules. We are ahead (bounded walk with labelled stops).
- Bridge detection: forensics/bridges.py only resolves a Relay request by origin tx hash through `GET api.relay.link/requests/v2?hash=` (:101) and matches inTxs hash strictly (:75-79, 115). Our notes say requests/v2 is retired 24/11, so this call is going stale. Selector table abi.py:16-18 knows Relay depositNative/depositErc20 only. Only one provider (RESOLVERS = (relay_request,), :163).
- Counterparty search: no function. grep "counterpart" finds nothing. Only direction filtering (from/to).
- Address poisoning: forensics/spam.py:29-33 THRESHOLDS: hex prefix 8, suffix 6, vanity 4; base58 prefix 6, suffix 5, vanity 4 (shared run lengths of leading/trailing characters; hex compared case-insensitively without 0x, base58 case-sensitive, :49-75). `lookalike_flags` (:78-92): flag if prefix >= prefix threshold OR suffix >= suffix threshold, else "vanity_suffix" if suffix >= 4. The references (known real addresses) are supplied by the user via `--ref name=addr` (cli.py `_parse_references`), not derived. No value threshold, no token allowlist, no time-proximity or "same-direction mirror" test on addresses. Token-side extras: non-ASCII symbol homoglyphs (:35-46), `no_dex_pair` via DexScreener (:137; unlisted real tokens flag as false positive), `mirror_amount` (a token amount equal to some native amount, :142). Everything is a flag, no verdict.
- Labels/identify: small hand curated knowledge base (labels.py, identify.py); Solscan/Orb best-effort.
- Chain coverage: eth, bnb, hyper, robinhood, arc, sol (chains.py:20-90). NO Polygon PoS, Base, Arbitrum. Our Polymarket path (Polygon) is not covered.
- HTTP (http.py): retry on 429/5xx with Retry-After, regex redaction of keys in errors (:30-34). Reasonable, but keys still sit in URLs.
- Tests: 14 test files, 152 test functions (tests/), covering spam, bridges, evm, solana, providers, cli. Not run.

Risks: silent partial history (above); false-positive poisoning flags from short thresholds and DexScreener; Relay endpoint deprecation; Helius legacy API.
Advantage over our system: none on data; one idea only: symbol-homoglyph flag and prefix/suffix thresholds as a documented lookalike metric. Our rule (official contracts only, manual exclusion) is stricter and avoids the threshold tuning.
Cost: Alchemy/Helius free tiers; no code adoption cost if only read.
Decision: REFERENCE for `spam._shared_runs`/`THRESHOLDS` (spam.py:29-75). Offline test: run the 20-line function on archived Polygon sender addresses against the known official counterparties and compare flags with our manual look-alike exclusions. REJECT as a tool (shallow, silent caps, no Polygon).

## 3. shottah/tracer
- Pin: 3a8a03c45c5b5c92fa886fda44b8d1ffa98a9177, 2026-09-27T19:51:42-04:00. v0.1.1 (Cargo.toml). 1.5 MB.
- License: GitHub metadata says Apache-2.0; Cargo.toml says "MIT OR Apache-2.0" and the repo has BOTH LICENSE-APACHE and LICENSE-MIT (copyright "The tracer contributors"). Discrepancy is metadata only; dual license, either is permissive.
- Nature: real Rust workspace (alloy 2), 5 crates: core, trace, analysis, client, cli, plus a Next.js example not in the workspace. Design doc (docs/design.md) is candid about scope.

### RPC methods needed (crates/tracer-client/src/artifacts.rs)
- eth_getTransactionByHash, eth_getTransactionReceipt, eth_getBlockByNumber, eth_chainId (:27-44).
- debug_traceTransaction with callTracer withLog (:78-87, 118-134); prestateTracer diffMode (:89-100, 139-151, optional); struct logs with memory (:102-114, 155-167, only under --deep).
- Backend auto (tracer.rs:100-113): if debug_ is unsupported, falls back to a local anvil fork (anvil.rs): fork at block-1 and replay preceding same-block txs via impersonated eth_sendTransaction. That needs eth_getStorageAt / state at the historical block (archive for old blocks, README:120-124) but no debug_ on the remote.
- No trace_replayTransaction (design.md out of scope: Parity trace_*). No eth_call at historical block as a trace method.
- Requires an external `anvil` binary (Foundry) for the fallback and e2e tests. That is arbitrary code on our box, so run only after review.

### Chain support
- Chain-agnostic EVM. Labels (tracer-core/src/labels.rs:9-30): native symbol for 137 (POL), wrapped-native for 1, 10/8453 (Base), 42161, 137, 56. Polygon PoS and Base and Arbitrum are therefore recognised, but nothing is tested on them. The example app lists Ethereum, Base, Arbitrum only (README:167-169). Polygon replays via anvil are unproven: Bor state-sync/system transactions and Polygon's block env are not modelled. A fidelity check (status, gasUsed, log count) is embedded in the report (design.md), which is the right safeguard.

### What it catches that ERC-20 Transfer logs miss
- Native value in internal calls: yes. Sources are tx value, CALL value, CREATE endowment and SELFDESTRUCT (analysis/src/transfers.rs header lines 3-5), skipping reverted subtrees (:70-77, "effective" flag).
- Wrapped native Deposit/Withdrawal from the canonical wrapper only (:182-192).
- Exact native balance deltas incl. gas from prestate diff (design.md "Balance changes").
- EIP-7702: only passes authorization_list through when replaying (anvil.rs:218-219). No decoding of delegated execution. The call tree shows what callTracer shows, nothing 7702-specific.
- ERC-4337: no code (grep for 4337/userop/entrypoint finds nothing). An EntryPoint.handleOps would appear as a generic call tree.
- Tokens without events: NOT handled. Token flows are event-only (ERC-20/721/1155); no balanceOf diffs, no storage diffs for tokens.

Tests: 38 test attributes in crates (unit and e2e needing anvil; e2e auto-skips without it). Not run.
Risks: replay divergence on non-Ethereum chains; needs a debug-capable or archive RPC for old blocks; subprocess spawning; results are single-transaction only (no address history, no pagination).
Advantage over our system: yes, one gap: our Polygon decoder sees only ERC-20 Transfer logs and the last 32 bytes of calldata, so internal native POL value and delegated call structure are invisible. tracer's native-internal-transfer logic is the missing piece, but only if a debug/archive Polygon RPC is available.
Cost: Rust build plus Foundry; RPC needs debug_traceTransaction (paid on most providers for Polygon).
Decision: REFERENCE, with a conditional ADOPT-CANDIDATE on `tracer_analysis::transfers::collect_transfers` (crates/tracer-analysis/src/transfers.rs:28). Offline test without any network: it takes a `Frame` tree, so feed it a callTracer JSON captured once for a Polygon tx and compare transfers with our log decoder; only the capture step needs a node. Do not use the anvil-fork backend for Polygon without a fidelity pass on known txs.

## Summary table
| Repo | SHA | Date | License file | Decision |
|---|---|---|---|---|
| helius-sdk | e421446 | 2026-11-05 | MIT | REFERENCE |
| wallet-forensics | 540a5be | 2026-09-21 | MIT | REFERENCE (spam.py thresholds), reject as tool |
| tracer | 3a8a03c | 2026-09-27 | MIT OR Apache-2.0 (both files) | REFERENCE, conditional adopt of collect_transfers |
Not checked: live API behaviour, credit prices of the two Helius methods, whether tests pass, git history beyond the shallow commit.
