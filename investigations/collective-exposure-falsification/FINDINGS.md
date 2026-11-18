# Findings: collective-exposure-falsification

## F-001 | UNRESOLVED | Collective shifts add no measurable information beyond price and public information on TEST; the study is underpowered for moderate effects
- Sources: sources/FALSIFICATION_REPORT.md ; sources/out/models/results_test.json ; sources/out/models/verdict.json
- Method: Nested logistic models M0-M3, frozen before the hold-out; T1 = ΔLL(M1→M3) on 724 COL units, −0.0050, 95 % CI [−0.0110, +0.0008], p = 0.98; Holm over 7 tests, none rejected
- Limits: Power gate G1 failed (STRONG 4/5 seeds); a MEDIUM-size effect is not excluded; T4 matched excess +2.4 points, CI −1.0 to +5.8, p = 0.079
- Links: none

## F-002 | REFUTED | An improvement of the size of the STRONG synthetic injection (+0.036 nats per unit) is excluded on TEST
- Sources: sources/FALSIFICATION_REPORT.md ; sources/controles/positive_controls.md
- Method: One-sided 95 % upper bound of T1 ≈ 0 (+0.0010 after the NULL overfitting correction)
- Limits: Holds only for markets under 1 M USD volume, fills only
- Links: none

## F-003 | UNRESOLVED | Funding relations between contributing wallets (M4) could not be tested
- Sources: sources/out/models/results_test.json ; sources/controles/positive_controls.md
- Method: T5 = ΔLL(M3→M4); 8 TEST units with a direct USDC link or a common non-hub funder, 30 required
- Limits: Funding window = first 100 ERC-20 transfers per wallet; FUNDLINK control shows the test works when links are frequent
- Links: none

## Missing to conclude

- A larger hold-out (more bands of the hash space) for power against a MEDIUM-size effect.
- An order-book recorder at alert time for any execution claim.
