"""Arithmetic of the published vsbtc wallet score, reimplemented from the formula.

The weights are the ones in that repository's src/onchain.py final assignment:
base = 0.45*base_m + 0.12*repeat + 0.22*s_calib + 0.09*s_conc + 0.12*s_fresh,
then a 0.65 penalty when realized PnL is negative, plus 0.15*s_chain and
0.08*s_exit, clipped to [0, 1]. Component definitions used for the consistency
check are the ones in src/score.py.
"""


def clip01(value: float) -> float:
    return 0.0 if value < 0 else 1.0 if value > 1 else value


def component_scores(calib_edge, n_resolved, top_event_share, n_markets):
    return {
        "s_calib": clip01(float(calib_edge) / 0.30) * clip01(float(n_resolved) / 10.0),
        "s_conc": clip01(float(top_event_share) / 0.5),
        "s_fresh": clip01((4.0 - float(n_markets)) / 3.0),
    }


def published_score(base_m, repeat, s_calib, s_conc, s_fresh, s_chain, s_exit, realized_pnl) -> float:
    base = (
        0.45 * float(base_m)
        + 0.12 * float(repeat)
        + 0.22 * float(s_calib)
        + 0.09 * float(s_conc)
        + 0.12 * float(s_fresh)
    )
    penalty = 0.65 if float(realized_pnl) < 0 else 1.0
    score = base * penalty + 0.15 * float(s_chain) + 0.08 * float(s_exit)
    return clip01(score)
