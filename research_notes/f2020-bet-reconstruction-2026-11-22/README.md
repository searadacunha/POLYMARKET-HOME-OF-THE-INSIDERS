# Funded bets of four f2020 payees

A follow-up to [PR 110](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/110). Four Polymarket trading addresses bought after a credit from the commingled `0xf2020c…c423` route. This note reconstructs each bet from Polygon receipts: the outcome bought, price, fees, sales, redemptions, the official result and the net profit. It then covers every later position of the same addresses, with controls and three separate scores. PR 110's files are not modified.

**[Read the report](results/REPORT.md)**

| Wallet | Bet | Result | Net on that market |
|---|---|---|---:|
| W1 `0x9fed…1d1b` | Down at 0.65, BTC 5 min, 25 Oct | Down won; first lot sold early, re-bought, redeemed | +2.824012 |
| W2 `0xd74d…ccf3` | Down at 0.40, BTC 5 min, 1 Oct ET | Down won; sold after 36 s | +0.560130 |
| W3 `0x569c…741d` | Down at 0.33, BTC 5 min, 24 Sep | Up won | −2.407870 |
| W4 `0xadd9…8df9` | No at 0.03, Busan 22 °C, 26 Sep | Yes won | −0.149839 |

None of the four shows an apparent informational advantage. The mission's wallet 4 address has 39 hex digits; the report explains why `0xadd9ab62…8df9` is the address meant.

## Files

| Path | Content |
|---|---|
| `results/REPORT.md` | Results first, then method and limits (generated) |
| `results/focus_bets.csv` | One row per studied bet: position, stake, fees, result, PnL, delay, links |
| `results/focus_operations.csv` | Every on-chain operation on the four markets, decoded from receipts |
| `results/positions_after_funding.csv` | Every later position: 2,548 markets |
| `results/controls.csv` | 60 control traders, same test |
| `results/results.json` | Everything above, plus ledgers, reconciliations and scores |
| `data/raw/` | Captures: activity, Gamma, receipts, ledgers, payouts, balances, Binance, METAR, controls |
| `data/inputs/` | PR 110 inputs copied from Git objects of its head, with original SHA-256 |
| `scripts/` | `collect.py` (network), `reconstruct.py` and `report.py` (offline), decoders |
| `tests/`, `verify.py` | Regression tests; offline byte-for-byte replay with sockets blocked |

## Reproduce

From the repository root:

```bash
python3 -I research_notes/f2020-bet-reconstruction-2026-11-22/tests/test_reconstruct.py
python3 -I research_notes/f2020-bet-reconstruction-2026-11-22/verify.py
```

The capture can be repeated from the note folder with `python3 -I scripts/collect.py <step>` (network, public endpoints, no key). A new capture belongs in a new folder: later activity changes the open positions.
