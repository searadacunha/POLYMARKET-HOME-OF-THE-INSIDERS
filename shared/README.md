# Reusable code

The code stays in its investigation so that scripts keep their relative paths and their provenance. This index points to it instead of copying it.

| Need | Where |
|---|---|
| Follow a wallet's collateral both ways, with a level of proof per relation | [signal_engine/fund_flow](../investigations/polysentinel/sources/signal_engine/fund_flow/trace.py), [its documentation](../investigations/polysentinel/sources/docs/FUND_FLOWS.md) |
| Bounded walk downstream, stopping at labels, contracts and services | [walk.py](../investigations/hacks-parallel/sources/tools/walk.py) |
| Funding graph and direct links between wallets | [funding_graph.py](../investigations/polysentinel/sources/signal_engine/funding_graph.py), [direct_links.py](../investigations/ballon-dor-wallets/sources/tools/direct_links.py), [classify_links.py](../investigations/ballon-dor-wallets/sources/tools/classify_links.py) |
| Collective behaviour and empirical comparators | [collective_behavior.py](../investigations/polysentinel/sources/signal_engine/collective_behavior.py), [comparators.py](../investigations/polysentinel/sources/signal_engine/comparators.py) |
| Frozen study code: labels, tests, positive controls | [collective/code](../investigations/ballon-dor-wallets/sources/collective/code/) |
| Polymarket PnL from activity | [pm_pnl2.py](../investigations/changenow-polymarket/sources/pm_pnl2.py) |
| Check that every hash and address in a report exists in the evidence | [selfcheck.py](../investigations/changenow-proof/sources/tools/selfcheck.py) |
| Throttled HTTP with cache, address helpers | [net.py](../investigations/ballon-dor-census/sources/code/net.py), [addr.py](../investigations/ballon-dor-census/sources/code/addr.py) |
