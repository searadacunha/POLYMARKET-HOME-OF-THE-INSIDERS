# Polymarket, Home of the Insiders

## Did these bettors know something the market did not?

Polymarket lets people buy and sell positions on the outcomes of real-world events.

This investigation follows the money behind bets on **the 2026 Ballon d'Or ranking**, **Nicolás Maduro leaving power**, and **U.S. strikes on Iran**.

The questions being traded were concrete:

| Case | What people were betting on |
|---|---|
| **Ballon d'Or 2026** | Who would win football's individual award, which players would finish in specific places, and whether **Kylian Mbappé would finish ahead of Lamine Yamal**. |
| **Maduro** | Whether Nicolás Maduro would be out of power **by 31 January 2026**, alongside related Venezuela markets. |
| **Iran** | Whether the United States would strike Iran **by 28 February 2026**, alongside other deadlines and related markets. |

Some positions attracted attention because of their size, timing or eventual returns.

I reconstruct what the accounts actually bought. I trace their funding. I follow the withdrawals. Then I test whether the apparent connections survive comparison with other traders and ordinary platform behaviour.

**The research has established financial links between accounts, reconstructed their results and resolved specific routes across blockchains. Access to non-public information remains unproven.**

The Ballon d'Or accounts and the Maduro/Iran network are separate case studies.

---

## Act I: The Ballon d'Or Ranking

### Why these bets attracted attention

On **23 October 2026**, three days before the ceremony, [Upside reported](https://www.upside24.com/articles/ballon-d-or-2024-264-000-mises-sur-polymarket-suggerent-une-fuite-du-top-5-avant-596165) that accounts on Polymarket were backing the same scenario:

**Harry Kane first. Kylian Mbappé second. Lamine Yamal third. Rodri fourth. Lionel Messi fifth.**

That was also the order in the [result published by UEFA on 26 October](https://www.uefa.com/uefachampionsleague/news/02aa-21ec47378e70-b29defb43769-1000--harry-kane-wins-2026-mens-ballon-d-or/).

The report raised a specific suspicion: had somebody obtained the ranking before it became public?

That is the claim this case examines. It requires rebuilding the trades, the information available at the time and the financial relationships between accounts.

### From a public screenshot to eleven accounts

The original screenshot highlighted **nine accounts** holding the Mbappé side of the market asking who would finish higher, Mbappé or Yamal. Two more accounts were named in the subsequent reporting.

I reconstructed the screenshot against the trading history: **all fifteen displayed positions matched in the same order**, within half a share. The account inventory links the eleven public labels to wallets, with the confidence of each match recorded.

All eleven held **Mbappé ahead of Yamal**. Their other positions differed. The evidence does not show that every account bought the entire top five.

These accounts were selected through public reporting, so the study is retrospective. The first documented public report is an important cutoff: bets after that report may follow information already available to everyone.

[Account identification and screenshot reconstruction](investigations/ballon-dor-wallets/sources/reports/inventaire_adresses.md) · [Corrected case report](investigations/ballon-dor-wallets/sources/reports/rapport_final.md)

### What the money trail revealed

The tracing found two direct financial connections involving the account called `brace227`.

| Finding | What is established |
|---|---|
| **A connection to another named account** | On 4 October, the owner address associated with `brace227` sent **0.002048944 ETH** to the owner address associated with `kraben006`. |
| **A further account outside the eleven** | On 9–10 October, the same `brace227` owner address sent **5,170 USDC** in two transfers to the recorded owner of another Polymarket wallet, `0xa8e6…74a5`. |

The additional account matters because the funding trail found something the screenshot did not show.

Its observed trading was concentrated on **Kane to win**. The published history records **16 purchases costing $5,164.99**, followed by **$8,061.90 withdrawn**. Those withdrawals include returned capital. This account is outside the eleven-account totals below.

Funding another account establishes a financial relationship. A loan, an arrangement between acquaintances or shared operation can produce that relationship; the transfers alone do not identify the controller or the source of the betting decision.

[Classified wallet findings](investigations/ballon-dor-wallets/FINDINGS.md) · [Funding paths and the additional account](investigations/ballon-dor-flow-trace/sources/reports/COMMON_FUNDERS.md)

### Reconstructing the results

The reconciliation dated **2 November 2026** records:

| Measure | Published result |
|---|---:|
| Deposits across the eleven accounts | **$304,137.63**, in 46 deposits |
| Withdrawals across the eleven accounts | **$493,094.76**, in 25 withdrawals |
| Net cash flow across the eleven | **$188,957.12**, calculated before rounding |
| Net cash flow across the seven settled accounts | **$129,367.79** |

The seven settled accounts are a subset of the eleven. Four accounts were not classified as settled. These are wallet-level cash flows, with costs outside the observed wallets excluded; gross withdrawals are not trading profit.

[Full-precision reconciliation](investigations/ballon-dor-wallets/sources/evidence/contre_verification_20261102/reconciliation_montants.json)

### What did not survive checking

Several initially suspicious patterns had ordinary explanations.

Funding shortly before a first purchase was also common among other new accounts. Apparently simultaneous Kane payouts belonged to a payout batch involving **2,711 accounts**. Shared exchanges and bridge contracts did not establish a relationship between their customers.

The original comparison sample also contained **48 unusable histories out of 78 wallets**, invalidating its base-rate estimate.

The present finding is specific: **financial connections are documented; coordinated betting and access to the ranking are not established.** The early public-information timeline and parts of the comparison coverage remain incomplete.

[Corrected findings and rejected signals](investigations/ballon-dor-wallets/FINDINGS.md) · [Counter-verification](investigations/ballon-dor-wallets/sources/reports/CONTRE_VERIFICATION.md)

---

## Act II: Following a Later Payment Beyond Polymarket

The owner address of the additional Kane account appears again in a later transaction.

On **29 October 2026**, it sent **2,969.568353 mUSD** through **Relay**, a service that routes transfers between blockchains, from **Ethereum to Monad**.

The destination transaction deposited the funds into a vault and credited **2,904.308540 vmUSD shares** to:

`0xea1a3f324c5ee313bb04d9e642c39c8b29e7454b`

One archived Relay request explicitly connects the two transaction hashes. Both receipts succeed. The transactions are **29 seconds apart**, and the destination logs identify the address that received the shares.

That last distinction matters: a router address and the beneficiary of a vault deposit have different roles. The destination receipt resolves the beneficiary.

**mUSD and vmUSD are different units.** The difference between the token amount and the number of vault shares is not a measured loss.

This route is reproducible from the included archives. Connecting the entire later payment to Polymarket winnings requires a separate reconciliation of the withdrawal, intermediate balances and USDC-to-mUSD conversion. The beneficiary's human controller and current holdings are not established.

[Complete trace, transaction hashes, archived responses and verifier](research_notes/relay-followup-2026-11-04/REPORT.md)

---

## Act III: Maduro and Iran

### The events behind the markets

This case follows accounts trading on **Maduro being out of power by 31 January 2026** and **U.S. strikes on Iran by 28 February 2026**.

The Maduro analysis includes purchases on **3 January** before a sharp increase in the market price. The Iran analysis includes purchases on **26–28 February**, some before the largest price move and some after the market had already started moving.

The question is how those purchases relate to public information, and whether the accounts were financially connected.

A price move provides a market timestamp. It does not establish the moment when information first became public.

[Market-by-market account history](investigations/maduro-iran/sources/phase2/TABLE2_polymarket_accounts.csv) · [Trade timing and the information question](investigations/maduro-iran/sources/RAPPORT_2026-09-29.md)

### Eight accounts connected by funds

The investigation documents **eight accounts linked by transfers across Polygon, Ethereum and TRON**.

The links include money moving from one Polymarket account into another account's funding path:

- `chileno777` funded `TacticalInsiderNews`.
- `Mrs.Joker` funded `Planktonbets`.
- Funds withdrawn by `X34` contributed to the funding of `Mrs.Joker` through an intermediate Ethereum address.

Other addresses received withdrawals from several accounts and funded several members of the network.

The published graph distinguishes those connections from common services. It does not identify a single source financing all eight accounts, and common control remains a hypothesis.

[Transaction-level links and comparisons](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md) · [Funding, withdrawals and tracing boundaries](investigations/maduro-iran/sources/phase3/RAPPORT_PHASE3_2026-09-29.md)

### What the eight accounts earned

| Measure | Published result |
|---|---:|
| Aggregate trading PnL, including remaining position value | **$509,993.24** |
| External capital entering the network | **$151,084.40** |
| External outflows | **$660,708.94** |
| External outflows minus external capital | **$509,624.54** |

These figures cover the **eight accounts' published trading histories**, including other markets and losing positions. They are not a total attributed only to the two headline events, or a measurement of profits from inside information.

The accounting snapshot is dated **29 September 2026**. The **4 November arithmetic audit** aggregates the eight accounts before rounding. Trading PnL and external net cash flow are different measures.

[Accounting formula and source tables](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md) · [Eight-account arithmetic audit](investigations/maduro-iran/results/accounting_audit_2026-11-04.json)

### Comparing them with everyone else

The main event windows contained **21 Maduro YES buyers** and **128 Iran YES buyers**.

Within those windows, the linked accounts stood out principally by position size. Their timing and entry prices did not establish that they had an exceptional informational advantage. Their histories also contain losing bets, including earlier Maduro and Iran deadlines.

The financial network is documented. The first public information at the relevant moments, the operators' identities and any access to non-public information remain unresolved.

[Population comparisons and alternatives](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md) · [Current classified findings](investigations/maduro-iran/FINDINGS.md)

---

## Act IV: Could the Behaviour Be Detected and Used?

The investigation also tests whether observable activity can produce a useful signal for future trades.

None of the **eight initial preregistered signals** met the out-of-sample exploitation criteria.

A later signal anticipated price moves in held-out data. The execution studies did not establish an executable profitable strategy from it. Predicting a move and obtaining a fill before that move are separate problems.

The published live audit also found implementation defects requiring correction and revalidation. Historical replay does not establish prospective detection accuracy.

[Maduro/Iran signal and infrastructure findings](investigations/maduro-iran/FINDINGS.md) · [PolySentinel findings](investigations/polysentinel/FINDINGS.md)

## What the Research Still Needs to Resolve

| Question | Work still required |
|---|---|
| Were the Ballon d'Or positions unusual before relevant public information? | Complete the early public-information timeline and resolve the remaining comparison and protocol-coverage limits. |
| How much of the later mUSD payment can be attributed to the additional account's Polymarket withdrawal? | Reconcile the withdrawal, intermediary movements, conversion and competing inflows. |
| Did the Maduro/Iran trades precede information available to other traders? | Verify the earliest public reports independently, then compare them with the recorded trades and market prices. |
| Who controlled the accounts or used a shared service? | Additional attribution evidence; where the trail ends at a service's private customer records, public-chain data cannot settle the question alone. |

Findings are recorded as `CONFIRMED`, `SUPPORTED`, `HYPOTHESIS`, `REFUTED` or `UNRESOLVED`. Corrections and rejected explanations remain part of the research.

[METHODOLOGY.md](METHODOLOGY.md) explains the evidence rules.

## Reproduce and Validate

Replay the resolved Relay route from the included archived responses, without network access:

```bash
python3 research_notes/relay-followup-2026-11-04/verify.py
```

Run the repository checks:

```bash
python3 scripts/test_publication.py
python3 scripts/test_phi.py
python3 scripts/test_integrity_regressions.py
python3 scripts/test_parallel_publication.py
python3 scripts/validate_evidence.py
python3 scripts/build_master_report.py --check
```

These checks cover publication safeguards, central utilities, evidence integrity and generated reports. Each investigation documents its own analytical replay requirements. Some raw inputs are local-only or require RPC access; a repository check does not replay every study.

## Explore the Research

| Topic | Where to read |
|---|---|
| Ballon d'Or | [Wallet study](investigations/ballon-dor-wallets/README.md), [audit](investigations/ballon-dor-audit/README.md), [funding and exits](investigations/ballon-dor-flow-trace/README.md), [market census](investigations/ballon-dor-census/README.md) |
| Maduro and Iran | [Research overview](investigations/maduro-iran/README.md), [findings](investigations/maduro-iran/FINDINGS.md), [status](investigations/maduro-iran/STATUS.md) |
| ChangeNOW | [Evidence for the named accounts](investigations/changenow-proof/README.md), [payout analysis](investigations/changenow-outflows/README.md), [Polymarket payees](investigations/changenow-polymarket/README.md) |
| Monitoring | [PolySentinel](investigations/polysentinel/README.md), [recovery harness](investigations/polysentinel-harness/README.md), [publication copy](investigations/polysentinel-public/README.md) |
| Other investigations | [Security incidents](investigations/hacks-parallel/README.md), [search for an edge](investigations/edge-polymarket/README.md), [historical corpus](investigations/corpus-historique/README.md) |

The [master report](MASTER_REPORT.md) collects classified findings and contradictions. The [inventory](INVENTORY.md) records each investigation's published state. Original source snapshots retain their history; subsequent findings record corrections. [CONTRIBUTING.md](CONTRIBUTING.md) describes the publication workflow.
