"""Self-check of the fill model on hand-built transactions (run: python3 test_replay.py)."""
from replay import tx_ask_levels, fill, pnl

# taker BUY Yes 150 vs makers SELL Yes 100@0.40 and BUY No 50@0.55 (mint -> ask 0.45)
tx = [(10, "t", "BUY", "Yes", 150.0, 0.4167), (10, "m1", "SELL", "Yes", 100.0, 0.40),
      (10, "m2", "BUY", "No", 50.0, 0.55)]
assert tx_ask_levels(tx, "Yes") == [(0.40, 100.0), (0.45, 50.0)]
# 1:1 match is ambiguous and never used
assert tx_ask_levels(tx[:2][:1] + [(10, "m1", "SELL", "Yes", 150.0, 0.40)], "Yes") is None
# fill starts after the trigger: an earlier tx is ignored, a tx past the window too
txs = [(5, [(5, "a", "BUY", "Yes", 20, .1), (5, "b", "SELL", "Yes", 10, .1), (5, "c", "SELL", "Yes", 10, .1)]),
       (10, tx), (2000, tx)]
f = fill(txs, "Yes", 8, 50.0)
assert abs(f["cost"] - 50.0) < 1e-9 and abs(f["shares"] - (100 + 10 / 0.45)) < 1e-9 and f["first_ask"] == 0.40
f2 = fill(txs, "Yes", 8, 1000.0)               # more than the evidence: partial, never invented
assert abs(f2["cost"] - (40.0 + 22.5)) < 1e-9
net, cost, fs = pnl(f, 0, "politics")          # losing trade still pays fees
assert net < -50.0 and fs > 0
print("ok")
