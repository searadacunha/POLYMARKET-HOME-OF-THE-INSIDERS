# FORENSIC CASE FILE — ChangeNOW (CN) → Polymarket (PM) funding attribution

You are the reasoning engine. I (the operator) have shell + Python + these on-chain data
APIs and will EXECUTE whatever runnable logic you specify, then return real results to you.
Be adversarial: falsify your own hypotheses before retaining them. Separate MEASURED /
ASSUMED / MISSING. Confidence must be PER WALLET, never a binary global verdict.

## MISSION
Robustly identify WHICH Polymarket wallets were funded via ChangeNOW, with a confidence
level per wallet, defeating the proxy / commingling obfuscation.

## WHY THIS IS HARD (the blocker to solve)
ChangeNOW is an instant non-KYC swap = a proxy/mixer. The payout to the PM wallet does NOT
come from the original depositor but from a CN hot-wallet that pays thousands of users. The
direct depositor→destination link is broken on-chain. A naive "funding-first" scan over a
KNOWN set of CN addresses produces FALSE ZEROS because (a) the CN payout set is incomplete
(hot-wallet rotation + router/proxy contracts I have not fully enumerated) and (b)
commingling drowns the "whose funds" signal. We must NOT attribute naively by "who sent the
money".

## MEASURED GROUND TRUTH (from my prior verified runs — real, on-chain, funded_by-banned)
Rails already mapped:
  1. DIRECT POLYGON: CN EVM payout hub pays USDC.e/USDC → wallet → PM.
     - Confirmed CN EVM payout hub: `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` ("f2020"),
       born ~2026-04-14. 130 PM wallets received direct payouts from it (forward flow).
     - Internal CN plumbing seen upstream of f2020: `0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a`.
  2. SOLANA-BRIDGED via Relay: solver `0xf70da978...` fills bridge legs (source→destination).
     - Solana CN hubs: `B48k...` = CN_CONFIRMED (successor of an older hub "G2Y"); `9byY...`
       = CN_CANDIDATE (no direct edge B48k↔9byY, but 71 recipients co-funded by BOTH =
       strong sibling signal). 17 PM bettors attributed via these (CN_DIRECT on Solana side).
  3. deBridge / DLN: measured 0/40 large CN recipients are DLN order-creators => this angle
     looked ~empty, but solver-obscured volume is an unattributed upper bound, not a true 0.
PM collateral token = pUSD `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb`. PM deposits also
transit an ERC-4337 EntryPoint `0x4337084d...` (included, not excluded, to raise PM sensitivity).
Polygon token addresses: USDC.e `0x2791bca1f2de4661ed88a30c99a7a9449aa84174`,
USDC native `0x3c499c542cef5e3811e1192ce70d8cc03d5c3359`, USDT `0xc2132d05d31c914a87c6611c10748aeb04b58e8f`.

## WHAT PRIOR RUNS CONCLUDED (and why it's deemed "not a success")
Tier-1 deterministic = ~130 PM wallets from f2020 (mostly tiny: 60% are crypto Up/Down
grinders + retail, median CN→ a few dollars). Verdict each time: CN→PM is REAL but RARE
(~0.03–0.07% of the PM universe) and looks like base-rate / shared infrastructure, NOT a
coordinated fleet, with NO exploitable insider edge. The dissatisfaction: the per-wallet
attribution is INCOMPLETE (false-zeros from proxy rotation + commingling were never fully
closed) and the EVM payout side was never unwound through INTERNAL traces. So coverage is a
declared lower bound, not a closed set.

## TOOLS I ACTUALLY HAVE (Flipside is ABSENT — do not design against it)
- Etherscan/Polygonscan **V2 unified API** (1 key, `?chainid=137` for Polygon). Endpoints:
  - `account&action=txlist&address=` (external txns)
  - `account&action=txlistinternal&address=` AND `&txhash=<hash>` (INTERNAL txns / traces
    of a given tx — THIS is the proxy-unwind primitive; recovers the true internal recipient
    behind a router/proxy, no archive trace node needed)
  - `account&action=tokentx&address=&contractaddress=` (ERC-20 transfers)
  - `account&action=tokentx` filtered by contract = pUSD/USDC.e to see PM-side credits
- Polygon JSON-RPC (POLYGON_RPC_URL): eth_getTransactionReceipt/logs, balanceOf. NO trace_*
  (public RPC). Use Etherscan internal-tx endpoint as the trace substitute.
- Helius keyed Solana RPC (for the Solana hubs B48k/9byY; ALT/versioned-tx aware extraction
  exists — must include meta.loadedAddresses or SPL outflows of ALT txns are missed).
- Polymarket data-api `/trades`, `/activity`, `/positions`, Gamma `/markets`, CLOB.
- Web search (you have it) for up-to-date CN infra (published hubs/gasers from chain-analysis).
  MANDATE: no invented addresses. If you need CN infra you don't have, web-search it and CITE.

## THE 5 LEADS (falsify each; tell me which survive)
1. Unwind the proxy via internal traces: if a payout passes through a router, the EXTERNAL
   transfer points to the proxy, not the final recipient — pull internal transfers
   (txlistinternal by txhash) to recover the true destination. Neutralizes obfuscation.
2. Gaser-fleet discovery by co-funding graph: from known CN gasers → all gassed wallets →
   for each, who else gassed it → bounded transitive closure to reveal rotated gasers.
   Validation: a CN gaser funds ONLY gas (~0.01–0.1 native MATIC), never capital. Any
   candidate that also sends capital is rejected.
3. Deposit↔payout pairing by correlation: CN does not publicly link deposit and payout. Over
   a time window, correlate (asset_out, amount_out, ts_payout) at the CN hub with (asset_in,
   amount_in, ts_deposit). Low cardinality → probabilistic attribution with an EXPLICIT error
   bound.
4. Behavioral payout signature: characterize nonce / gas-price / cadence of the CN hot-wallet
   fleet to filter false positives.
5. Cross-rail unification: for rails 2 (Relay) & 3 (deBridge/DLN) the "proxy" is the bridge
   solver. Decode its fills (internal traces of solver txns) to map source→destination, then
   reconnect to the upstream CN deposit.

## DELIVERABLE I NEED FROM YOU NOW (step 1 of the loop)
A. DIAGNOSIS: precisely why funding-first false-zeros happen here, and which of the 5 leads
   SURVIVE adversarial falsification (and which are dead/weak, with the killing argument).
B. RETAINED METHODOLOGY: the concrete pipeline, stage by stage, designed against the tools
   above (Etherscan V2 internal-tx + RPC + Helius; NOT Flipside). For each stage give the
   exact API calls / filters / thresholds and the runnable logic (Python) I should execute.
   Make the proxy-unwind (lead 1) and gaser-closure (lead 2) concrete and runnable.
C. PER-WALLET CONFIDENCE MODEL: how to assign a calibrated confidence to each candidate
   wallet (what evidence raises/lowers it), and the output table schema
   {wallet_pm, rail, gaser_attributed, attribution_method, confidence, status(MEASURED/ASSUMED/MISSING)}.
D. EXPECTED FALSE POSITIVES / FALSE NEGATIVES: enumerate them and their cause, so I know
   the failure modes before I run.

Return a structured, implementable answer. Where you need a specific CN address/gaser you do
not have, either web-search+cite it or mark it as a MISSING input I must supply. Prefer
runnable specificity over generality. This is step 1; I will execute and report back.

## OUTPUT CONSTRAINTS FOR THIS STEP (read carefully)
- Be CONCISE and STRUCTURED (headers + short bullets + small code blocks). Not an essay.
- No web search needed now: reason over the facts I gave. Where you'd need a CN gaser/hub
  address you don't have, list it under "MISSING INPUTS I must supply / web-search next".
- Deliver A, B, C, D as four labelled sections. For B (methodology) give runnable Python
  sketches that call: chain.tokentx, chain.erc20_transfers_in_tx(txhash) [receipt-log ERC-20
  unwind], chain.txlistinternal_by_txhash, chain.gas_funders(wallet), chain.classify_funder(addr).
  NOTE: CN payouts are ERC-20 (USDC.e/pUSD) so the unwind is receipt-log Transfer decoding,
  NOT native txlistinternal (which is only for MATIC gas). Design accordingly.
