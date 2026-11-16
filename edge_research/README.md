# Edge research — execution gate, not a trading bot

This new directory is a **read-only evaluation** of the already frozen LONELY_THIN validation cohort. It does not amend historical files, reconstruct a new market population or place orders. In particular, a last printed price is **not** an executable order-book ask.

From the repository root:

    python3 -m unittest discover -s edge_research/tests -v
    python3 -m edge_research.cost_gate
    python3 -m edge_research.cost_gate --output /tmp/polymarket-cost-gate.json

The script reads [the frozen 587-row analytic table](../research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl) and **fails closed** if the original frozen cohort is no longer 45 observations. It reports an event-cluster bootstrap interval, optimistic settlement arithmetic using the *last printed buy price*, and adverse-entry-markup sensitivity. Neither full fills nor real return can be inferred from these quantities.

See [EDGE_VERDICT.md](EDGE_VERDICT.md), [DATA_INVENTORY.md](DATA_INVENTORY.md), and [SOURCE_AUDIT.md](SOURCE_AUDIT.md). This module is independent from the monitor and collectors. No live scanner is enabled: **no signal has passed a net-executable advantage gate.**
