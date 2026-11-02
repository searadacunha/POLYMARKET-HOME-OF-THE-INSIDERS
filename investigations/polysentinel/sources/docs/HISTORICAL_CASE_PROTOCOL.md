# Protocol for testing on historical cases

Publicly reported cases are useful for diagnosis and dangerous for validation. A detector built after reading about a case can always find it. This protocol keeps rankings honest.

## Rules

1. **Rankings before names.** Queues are computed from market data alone and sealed with SHA-256 before any list of reported accounts is read. The detector never receives a wallet, a date of the affair, a market identifier or an expected result.
2. **Reported accounts are not ground truth.** They are allegations from outside the system. A match says the engine agrees with a report, not that anyone is guilty. No precision or recall is computed from them.
3. **Separate development and evaluation.** Events are split by category and period before any look at results, and the split is frozen. Signals are changed only on development events. An evaluation event used once to change a rule moves to development for good.
4. **Controls in the same conditions.** Each case gets randomly drawn control events from the same period, category and activity class, with inclusion probabilities kept. The draw's seed is derived from data that cannot be chosen, such as the hash of the census file.
5. **No selection on outcome.** A case's population is every wallet that traded, winners and losers alike. Wallets are never preselected by realized profit.
6. **Same clock.** Each simulated decision reads only rows and metadata available at that time. Present-day fields that reveal the result, such as a resolution status, are removed before the replay.

## Categories

| Category | Typical decision structure | What makes a date hard |
|---|---|---|
| Airdrops and token launches | Project team | Deadline markets decay; announcements can be gradual |
| Product and company announcements | Corporate leadership | Rumours and leaks are often public first |
| Geopolitical and military decisions | Government or military | First public signals can precede official statements by hours |
| Awards and ceremonies | Jury or small group | Vote leaks and press speculation |
| Institutional decisions | Committee, court | Scheduled dates, strong public expectations |
| Media content | Production team | Trailers and early screenings |

## Steps

1. **Register** the case: category, markets, period, the source of the report, and what the report claims. Keep this local and out of the detector's reach.
2. **Check availability** before downloading: which API shapes honour time bounds, and whether the period is still served. Record each request.
3. **Freeze** the plan, code, data and synthetic controls.
4. **Replay** the case and its controls together, streaming, with a memory ceiling, checkpoints and a clean stop. Compare the incremental state with a full computation at fixed ticks.
5. **Seal** all outputs, including every wallet evaluated.
6. **Compare** with the reported accounts, in a separate exploratory step.
7. **Report** the first decision time, the rank within the queue, the number of files before it, and the rolling load over 24 and 72 hours. Report what stays unknown: the first public information, availability of the data at the time, wallet creation when unverified.

## Reading results

A case found late, or found behind many others, is a load result, not a failure of the signal. A case not found says nothing about innocence. Results from a period used to write the rules are never presented as an independent validation. Only events that resolve after a configuration is sealed can test it prospectively.
