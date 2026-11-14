# Blind audit of the frozen study, 14 November 2026

Four auditors read the plan, the frozen code and the frozen tables without seeing any result: leakage, statistics,
silent failures, conformity to the plan. The outcome column was dropped on load and no win rate was computed. Each
finding rated major was then handed to a fresh agent whose only job was to refute it. All auditors and all six
refuters declared that they opened no forbidden file.

**Outcome.** No finding puts the verdict in doubt in the direction that matters: nothing found could turn
NOT_SUPPORTED into a missed SUPPORTED with any confidence, and nothing makes the computed numbers wrong. Five major
findings limit what the verdict means. None was refuted; three were confirmed with a smaller reach than first stated.
The method is unchanged: every correction below that touches the method is a proposal for a later, separately frozen
study.

## Major findings

| # | Finding | Found by | Refuter | What it changes |
|---|---|---|---|---|
| 1 | **The sample is conditioned on the closing date.** Prices are read for the 14 days before `closedTime` (`col_20_prices.py:27`), and a market "by date X" closes early when the event happens. An ignition is therefore kept only if the market closed within 14 days of it | leakage, statistics, silent failures (each independently) | Not refuted. Reach reduced: 33.9 % of Yes-side alerts and 33.1 % of No-side alerts fall within 24 h of the close, almost the same; and the tested class is further from the close than the rest (median 3.0 days against 2.2) | The exact test compares the win rate with the price inside a population selected partly on the future. The comparison with the other ignitions shares the selection and is less exposed. The sentence "the market is calibrated after an ignition" holds for this sample only |
| 2 | **Rows are treated as independent.** The plan says dependence can only be negative. That is true inside a negative-risk event; 363 of the 570 validation rows are outside one, and nested "by date" markets win together | leakage, statistics, conformity | Not refuted | Little for the tested class (45 rows, 44 events, 45 initiators). The p-values of the two larger secondary classes (lonely, all ignitions) are too small by an unknown amount. They are not part of the verdict |
| 3 | **The price at the alert is the last buy, whatever its size.** For 22 of the 45 alerts that buy is under 10 USD, for 34 under 50 USD; for 8 it is more than 0.20 below the highest price the leading account paid | statistics, conformity | Not refuted. Reach reduced: the error goes both ways (a five-minute volume-weighted price differs from it by -0.12 to +0.05), and inside each price band of the comparison the class and the others have close mean prices (0.161 against 0.176 in the lowest band) | The excess of +3.5 points is conditional on this definition. Worst case, 6 points of excess could come from it |
| 4 | **The positive controls do not plant any of the above.** Synthetic tables have exact prices, no closing-date selection, no correlated events | statistics | Not sent to a refuter (follows from 1 to 3) | The controls show the code finds a planted effect; they do not show it is immune to these biases |
| 5 | **Power.** With 45 alerts, a real excess of 15 points would have passed in about one table in four (frozen controls: 13 of 60 at 40 alerts; two re-simulations by auditors on the real prices: 19 of 60 and about 30 %). One of 25 points: 49 of 60. One of 30 points: 48 of 60 in the frozen controls, 58 of 60 on the real prices | statistics, conformity | Not refuted | NOT_SUPPORTED means "not detected at this size". It says nothing about an excess under about 25 points. It is not "refuted" and not "the market is efficient" |

## Minor findings

- The plan promises to report initiators present in both discovery and validation. No code does. Counted by two
  auditors on the table: 2.
- The threshold sweep is declared in the plan but written to the registry as undeclared; the comparison lines carry
  the wrong label for their effective size. The count of comparisons (18) is right.
- The leave-one-event-out cells (44 exact tests) and the bootstrap are computed outside the registry. They are
  descriptive and never enter the verdict.
- Two rules were added to the plan during collection, before the freeze and before any outcome was read. They are
  dated in the plan, not in an amendment file. The lock is not immutable and not tied to a commit.
- `first_activity` is read without a time bound, so `first_activity_age_h` can be negative for a brand-new account.
  It is used by no class and no test, and should not be quoted as an account age.
- The history of the leading account is read before the first buy of the burst, not before its own first buy (up to
  14 minutes later in four alerts).
- The tag filter leaves three or four alerts on events played out in public (a football final, a golf tournament, a
  half-time show).
- Events that are siblings of a documented case (Iran, Venezuela) stay in validation, three alerts of the class
  among them. Registry slugs and conditions not found in the universe are not counted anywhere.
- A tape that starts after the window is stored as complete: 108 markets, 83 of them with no row. Their ignitions
  are counted as "no trade confirmation", so the effect is lost sample, not bias.
- Counters of HTTP errors cover the last launch of each collector only. The final states are clean (0 error),
  the history of retries is not kept.
- When several buys share the last second, the price at the alert depends on storage order: 2 alerts, 0.06 and 0.018.
- The catalogue counts 23 events and 150 markets twice after a restart; markets are de-duplicated by identifier.
- Raw databases are outside the lock; the derived tables are inside it.
- The 10-minute price point at the alert could carry a little of what follows it; the measurement is ambiguous.
- `too_deep` never fired (deepest tape 257 pages of 300).

## Checked and sound

Features use only rows dated at or before the alert; the alert is at least 15 minutes after the first buy on all
587 rows. The outcome comes from a separate file read by one script, last. The exact test and the permutation
formula are right; 200,000 draws resolve the threshold. The registry holds 10 lines on real data, all written by
frozen code after the freeze, 18 comparisons. The verdict is computed by code from wording fixed before. The 30
frozen files match the lock. The price at the alert recomputes exactly on all 48 alerts of the class. No thin
account reached the 500-row history cap.

## Reproduction

`ana_50_tests.py` rerun twice from fresh copies of the frozen files: see `REPRODUCTION.txt` in this folder.
The verdict script reads the registry, which a fresh copy does not carry, so it was not rerun; it is a deterministic
function of the reproduced file and of the count of 18.

## Not done

- The completeness review that closes this kind of audit was cut off with the session and was not rerun.
- Nothing that needs the outcome was measured: the size of finding 1 by side, the calibration of the price at the
  alert.
- No placebo alerts.

## Proposed for a later study, to be decided before any of it is run

1. Anchor the price window on the scheduled end date, known in advance, or stratify by time to close.
2. Use a robust price at the alert (volume-weighted over the last minutes, or last buy of 50 USD or more).
3. Permute whole events; group nested markets of one story.
4. Plant the three biases above in the positive controls.
5. Size the sample for the smallest excess worth detecting: at 15 points, about 80 alerts give one chance in two.
