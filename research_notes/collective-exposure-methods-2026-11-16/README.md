# Collective exposure: external-method crosscheck (16 November 2026)

**Original research synthesis, read-only follow-up.** This note compares public methodological implementations with *our own pre-existing archives*. No external empirical finding is attributed to this repository, and no third-party source code or dataset has been imported.

**No predictive alpha is established by this note.** It is an additive crosscheck for the separate investigation currently in progress; it is not an attempt to execute or change that investigation.

## The important distinction

The archive says all **36** accounts created 22–25 February 2026 bought **NO before YES across multiple Iran deadline markets**. On the **single February 28 market**, the separately archived 42,000-row trade-band analysis instead says **20/36** followed NO-before-YES; **15/36** only bought YES in that band and **1/36** had no BUY. Those statements are consistent because their market scope differs.

For the **733 other** accounts in the February-28 archived comparison, **16/733** followed NO-before-YES. Fresh arithmetic on the two documented counts gives a **25.45× descriptive frequency ratio**. The group was selected retrospectively, accounts may be dependent, the trade band may be censored and NO-before-YES does **not** prove a change of net exposure. Neither a causal interpretation, an inferential p-value, nor an actionable trading signal follows.

[Recalculated JSON](results/feb28_descriptive_recheck.json) | [Case scope reconciliation](CASE_CROSSCHECK.md)

## Methods integrated

- [External-method assessment](EXTERNAL_METHODS.md) differentiates tested negative findings, tools and plans, and data coverage gaps.
- [Exposure and deadline-ladder semantics](INTERVAL_LOGIC.md) makes the NO-by-earlier-date + YES-by-later-date position explicit using scenario payoffs.
- [Proposed decisive experiment](BACKTEST_SPEC.md) specifies where a future study needs actual net inventory, prospective groups, negative controls, latency and executable order book data.
- [Offline reproducer](recompute.py) recomputes descriptive archive ratios and checks consistency with the original 38-wallet roster. This is **not** a blockchain replay.

## Run

From repository root with Python 3.10+ and no external dependencies:

    python3 research_notes/collective-exposure-methods-2026-11-16/recompute.py --check
    python3 -m unittest discover -s research_notes/collective-exposure-methods-2026-11-16/tests -v

The main README, original cases, prior statistical verdicts and publication controls remain unchanged. The old LONELY_THIN class was **NOT_SUPPORTED** by its frozen test, and that null result is not overridden.

## Evidence policy

Original contributions in this note: the controlled mapping between published methods and our archival questions; the explicit scenario-payoff decomposition; code for arithmetic consistency and named limitations; and the next-test decision gates.

External contributions: independently published implementations and findings. They are described as such, with links and methodological limits in [EXTERNAL_METHODS.md](EXTERNAL_METHODS.md). They are not new findings by us.
