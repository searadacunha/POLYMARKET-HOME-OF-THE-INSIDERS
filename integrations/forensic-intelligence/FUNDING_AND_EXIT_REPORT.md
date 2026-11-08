# Funding and exit report — previously verified evidence

**2026-11-02; no new on-chain discovery in this run.** This report reconciles the already committed cases. The 19+ GB local raw data and the Mac/external drive are not accessible here. Three documented transfers are replayed in the new offline fixture, **without fresh node verification**.

## Ballon d'Or, 11 accounts

The audited population comprises **46 deposits ($304,137.63)** and **25 withdrawals ($493,094.76)**. Those are gross movements, **not profit**. **$129,367.79** is a scoped sum covering seven settled accounts only. [Source](../../investigations/ballon-dor-wallets/FINDINGS.md).

### A. Direct link: brace227 EOA to kraben006 EOA

Ethereum `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`, block **26,119,420**, **2026-10-04 13:54:35 UTC**: `0xc852b0938f5ad79b640d105ed11c14499454af26` paid `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65` **0.002048944 ETH** (about $5.53 then). **ONCHAIN_CONFIRMED transfer**, **NOT** evidence of a common owner. [Flow trace F-003](../../investigations/ballon-dor-flow-trace/FINDINGS.md).

The upstream Ethereum Relay payout `0xb17e1c4627ad8914f98f48a4fa7f5916953d3286e60cf3d80c6508257f46ce3c` has a message identifier also read in the Solana payment instruction. **Protocol-order linkage** in the older findings, not proof that identical coins traversed the solver; a solver pays its own inventory. [Wallets F-014](../../investigations/ballon-dor-wallets/FINDINGS.md).

### B. Additional funded key and Polymarket trading wallet

`brace227` EOA paid `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`:

- **2,210 USDC** on Ethereum, `0x7e3aecb9b41e6d3f92f25b8760228f15e9b55e798cd27977eb7170445cf64349`, block 26,157,246, **2026-10-09 20:28:35 UTC**.
- **2,960 USDC** on Ethereum, `0xb07c3c53a713d98aea1d1bd5d6facf849b6edc675c0fe2cfd3df5b791db20add`, block 26,158,556, **2026-10-10 00:51:11 UTC**.

The earlier investigator read `owner()` for proxy trading account `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` and associated it with that key. Wallet creation is separately documented on Polygon tx `0xa6e229972cef372f1efd5dbb24fe2459c4d279b49d1789a1093f7c1dad215d7b`. Reported 16 Kane Yes buys ($5,164.99) and withdrawal ($8,061.90). **Funding is confirmed; common operator is UNRESOLVED.** [Flow trace F-001](../../investigations/ballon-dor-flow-trace/FINDINGS.md).

### Exit findings

- On November 2 approximately **74%** of the $493,094.76 withdrawal value remained at, or returned to, first destinations; the reported snapshot includes $299,565.17 in stablecoins and 26.97 ETH across 7 accounts, with ETH valued at withdrawal time. It does not establish final destinations or customers. [Flow trace F-008](../../investigations/ballon-dor-flow-trace/FINDINGS.md).
- `OuldLm3alem`: conversion to Hyperliquid, loss on HYPE perpetual, then **73,001.19 USDC** back to the key. [F-011](../../investigations/ballon-dor-flow-trace/FINDINGS.md).
- `WenZhuanBuPei`: one downstream address separates **1%** and combines 3 pieces. No demonstrated mixer or owner. [F-012](../../investigations/ballon-dor-flow-trace/FINDINGS.md).

### Offline fixture check

`fixtures/ballon_dor_documented.json` contains exactly the 3 ETH/USDC transfer records above (not the upstream Relay claim): **3 financial edges and 3 nodes**. `pair_links` gives **one direct money link** among the two named signer keys, **zero proven common ownership links**. This checks serialization, decimals, duplicate handling and export integrity only.

## ChangeNOW

On February 23 2026, `kraben006` received **654.466304 USDC** (tx `0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219`) and **180.382489 USDC** (tx `0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80`) from `0xdd3d72c53ff982ff59853da71158bf1538b3ceee`, **834.848793 USDC total**.

The receipts are confirmed by the older inquiry. **ChangeNOW service attribution is SUPPORTED, not an individually proven order**. The funds later went to a platform-like deposit before Polymarket activity, with a **220-day** gap. No source-to-bet path, individual swap order, shared beneficiary or Monero transfer was established. The October 4 ETH send followed by a sweep to a labeled service remains only a deposit hypothesis. [ChangeNOW proof](../../investigations/changenow-proof/FINDINGS.md) and [false-positive controls](../../investigations/changenow-proof/sources/reports/FALSE_POSITIVES.md).

## Maduro/Iran

The original investigation identifies **8 accounts connected by funds**, with **$151,084.40** external capital, **$660,708.94** external outflows and **$509,993.25** scope-specific PnL. Discovery among large winners introduces selection bias. **Control, collusion and access to private information are not established**. Original raw data is not available to this run, so **no recomputation or extra wallet discovery**. [Findings](../../investigations/maduro-iran/FINDINGS.md).

## Visibility stops

| Boundary | What is visible | What is not proven |
|---|---|---|
| EVM receipts | Specific transactions and amounts already documented | Full chain histories, all logs and earliest-ever activity |
| Polygon deposits/redeems | Previously reconciled aggregate sources | All fees, positions, real PnL or customer identity |
| BSC, Base | Partial previous receipts | Complete inflows/internal traces |
| Solana, Tron | Individual protocol paths in prior reports | Full upstream/downstream coverage |
| Custodial exchange | Public entry or exit to labeled address | Its internal customer ledger or linked payout |
| ChangeNOW | Public service transfers/labels | Unique payin-payout order match |
| Monero/privacy protocols | No confirmed instance in these cases | Any private transfer by implication |

**Disposition:** prior verified observations restated; **zero new chain-verified financial links**. A source label does not prove beneficial ownership and a tracing boundary does not prove obfuscation.


## Addendum: archived ChangeNOW receipt recheck, not a new funding proof

Reading the actual version-controlled `investigations/changenow-proof/sources/data/verified_transfers.csv` through GitHub shows **30 documented transactions** (22 ERC-20, 8 native). Three ERC-20 transfer rows lack the original log index, so event-level coverage is **not certifiable** from those rows alone. `source_ingest.py` now reports the missing indices instead of silently presenting the table as a complete chain scan.

For `kraben006`, the two previously documented incoming Ethereum USDC transfers from `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` on 2026-02-23 are:

- Tx `0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219`, block 24,520,622, log 82, 654.466304 USDC.
- Tx `0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80`, block 24,520,663, log 598, 180.382489 USDC.

Total **834.848793 USDC**, independently recomputed from the stored raw integers. The original table reports node receipts and hashes; this pass **did not refetch those receipts from live Ethereum**. The sender's ChangeNOW attribution remains at the original `SUPPORTED` level, and there is still **no proven order-level mapping into Polymarket bets, payout wallet, Monero trail or common ownership**.

**Interoperable documentary graph:** the second-pass adapter combines the three reported Ballon d'Or transfers and the two cited ChangeNOW-related incoming payments in five financial edges across four addresses, with separate source strings. This is neither five new findings nor a provider-complete history. No account ownership or payin/payout link is inferred from the ChangeNOW sender.
