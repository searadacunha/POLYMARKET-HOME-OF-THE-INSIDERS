# Audit summary

Four read-only agents, all instances of the same model family, so this is no independent review in the strong sense. None read `tables/` or computed anything with `win`. Numbers below are theirs and were not all re-verified by the author.

## Before the freeze: silent-failure-hunter

Fixed before freezing: the cluster key was the market and not the event (2,097 markets, 648 events). Truncated files sat in the primary test. The volume field was always zero. A resampling null had almost no bursts at short windows. Controls covered one window of six.

## After the freeze, blind: protocol-auditor

- Blocking: a trap passes against the plan's "must fail all four" (`controles_positifs.md`, combined news-day trap, 300 s, seed 1).
- Blocking until checked: the frozen table predates the last edit of `lib_bursts.py`. Rebuild check below.
- Major: rows in a burst during cooldown leave the base without being events. `crowd` counts the row itself and same-second rows. The jitter at 3600 s spreads over 10 hours and inverts H2. The stricter threshold promised by the plan is not written and cannot be met. The power text is contradicted by its own table.
- Minor: no partial-file run for H2, effective n absent in some register lines, catalogue peers narrower than "every other token", uncomputable placebo lets a verdict through, controls at reduced draws, windows 90 and 900 without controls.

## After the freeze, blind: leakage-auditor

- Blocking: `total` descends from the outcome. Blocking: the same trap as above.
- Major: base membership uses later rows. The burst price is a VWAP, not the trigger-row price, so momentum returns. The $250,000 filter is lifetime volume read after resolution, and the plan calls the universe neutral. `closedTime` lags the public event, 2.9 hours on Maduro, 85 hours on Khamenei, so stale-ask sweeps enter. Jitter inverts at long windows. One world fact spans many events, and an event's deadline ladder can sit in two splits.
- Cleared: `win` never enters a feature. Partial files do not touch clean keys. Truncation shows no clump under page multiples.

## After the freeze, blind: stats-auditor

- Blocking: same trap. Matching does not stop the news confound: H1 positive in 6 of 24 news runs against a nominal 0.42%. The stricter threshold cannot be met.
- Major: H2 is not monotone. The gates add little on confounds. The placebo keeps the cell, so it cannot see a confounder, and it can veto a true effect. 1 of 72 is not a false-pass rate: 18 tables, and the design was tuned on these scenarios, so it is closer to training error. Power is low. Clusters are too fine. No influence check, and about 6 events could carry a pass. 15 of 75 cells cannot hold a burst, matched loss is not random, no floor. Multiplicity is 114 registered, 120 counting pre-freeze looks.
- Its reading of each verdict is adopted in amendment 001.
