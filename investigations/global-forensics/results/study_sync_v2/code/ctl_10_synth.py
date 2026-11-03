"""Positive and negative controls on synthetic tables, through the same functions and the same verdict as the real run. No real row and no real outcome is read here.

Structure taken from counts of the first study: entrants per token and tokens per event, never its outcomes. Usage: ctl_10_synth.py <out.json> [--quick]. Lines go to the register as synthetic.
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_v2 as lib  # noqa: E402

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAY = 86400.0
SIZES = (200, 400, 800)


def make(seed, facts=400, planted=0.0, delta=0.0, informed_share=1.0, trap=None, wallet_pool=200):
    """Tapes, not features: each market's rows go through lib.entrants_of_market, as real tapes do, so momentum, the guard and prior volume are read as in the real run.

    Calibrated by construction: a token wins with the probability of its start price, unless a scenario says otherwise. `planted`: share of tokens with a tight group. `delta`: added chance of winning on tokens whose group is informed. A group's wallets come from a small pool, so the same wallets act in many markets, and they trade before any public move, at the stale price.
    """
    rng = np.random.default_rng(seed)
    columns = {k: [] for k in ('token', 'fact', 'wallet', 'ts', 'price', 'usd', 'prior_volume', 'mom', 'tte_s', 'guard_ok', 'strict_ok', 'part', 'win')}
    token_id, wallet_id, base = 0, 1000, lib.HOLDOUT_FROM + 86400
    for fact in range(facts):
        part = int(rng.random() < 0.3)
        for _ in range(int(rng.integers(1, 5))):
            token_id += 1
            n = min(1500, int(rng.lognormal(np.log(10), 1.4)) + 1)
            life = float(rng.uniform(3, 60) * DAY)
            start = base + float(rng.uniform(0, 120) * DAY)
            close = start + life
            scheduled = close + float(rng.uniform(0, 30) * DAY) if rng.random() < .4 else close
            p0 = float(rng.uniform(0.02, 0.33))
            p_win, drift, news, ramp_s, jump = p0, 0.0, None, 1800.0, 0.0
            times = list(start + life * rng.random(int(n * 0.6)))
            for _ in range(3):
                centre = start + life * rng.random()
                times += list(centre + rng.normal(0, 3 * 3600, int(n * 0.4 / 3) + 1))
            if trap == 'crowded_win' and n > 20:
                p_win = min(0.95, p0 + 0.15)
            elif trap == 'momentum' and rng.random() < 0.3:
                drift, p_win = 1.0, min(0.95, 2 * p0 + 0.10)
            elif trap == 'rising_exit' and rng.random() < 0.3:
                drift, p_win = 2.5, min(0.95, p0 + 0.30)
            elif trap in ('news_day', 'news_day_bots', 'slow_news', 'slow_news_bots') and rng.random() < 0.3:
                news = start + life * float(rng.uniform(.3, .9))
                ramp_s, jump = (12 * 3600.0, 0.15) if trap in ('slow_news', 'slow_news_bots') else (1800.0, 0.30)
                times += list(news + rng.uniform(0, 6 * 3600, 2 * n + 10))
                p_win = min(0.95, p0 + jump + 0.15)

            def path(ts):
                value = p0 * (1 + drift * (ts - start) / life)
                if news is not None and ts >= news:
                    value += jump * min(1.0, (ts - news) / ramp_s)
                return value
            groups = []
            if planted and rng.random() < planted:
                at = float(start + life * rng.random())
                groups.append((min(at, close - 200), int(rng.integers(3, 6))))
                if rng.random() < informed_share:
                    p_win = min(0.95, p_win + delta)
            elif trap in ('news_day_bots', 'slow_news_bots') and news is not None:
                groups.append((min(news + float(rng.uniform(0, 6 * 3600)), close - 200), int(rng.integers(3, 6))))
            win = float(rng.random() < p_win)
            tape = []
            if rng.random() < 0.9:  # a market already traded: the volume floor does not bite, in nine in ten
                tape.append(dict(wallet=-token_id, side='SELL', token=token_id, size=30000 / max(p0, .01), price=p0, ts=int(start)))
            ordinary = [t for t in times if start <= t <= close]
            for ts in ordinary:
                wallet_id += 1
                price = float(np.clip(path(ts) * rng.lognormal(0, 0.05), 0.005, 0.99))
                usd = float(max(100.0, rng.lognormal(np.log(400), 0.8)))
                tape.append(dict(wallet=wallet_id, side='BUY', token=token_id, size=usd / price, price=price, ts=int(ts)))
                if rng.random() < 0.3:  # the same wallet again later: not an entrant
                    later = ts + float(rng.uniform(60, 86400))
                    if later <= close:
                        tape.append(dict(wallet=wallet_id, side='BUY' if rng.random() < .5 else 'SELL', token=token_id, size=usd / price, price=float(np.clip(path(later), .005, .99)), ts=int(later)))
            for at, k in groups:
                for w in rng.choice(wallet_pool, size=k, replace=False):
                    ts = at + float(rng.uniform(0, 120))
                    price = float(np.clip(path(ts) * rng.lognormal(0, 0.02), 0.005, 0.99))
                    tape.append(dict(wallet=int(w), side='BUY', token=token_id, size=500 / price, price=price, ts=int(ts)))
            if win:  # the public end of a winner: the price runs up on the last day, and the guard must see it
                for j in range(5):
                    ts = close - 3600 * (5 - j)
                    wallet_id += 1
                    tape.append(dict(wallet=wallet_id, side='BUY', token=token_id, size=2000, price=0.92 + .01 * j, ts=int(ts)))
            for e in lib.entrants_of_market(tape, scheduled, close):
                for key, value in (('token', token_id), ('fact', fact), ('wallet', e['wallet']), ('ts', e['ts']), ('price', e['price']), ('usd', e['usd']), ('prior_volume', e['prior_volume']), ('mom', e['mom']), ('tte_s', e['tte_s']), ('guard_ok', e['guard_ok']), ('strict_ok', e['strict_ok']), ('part', part), ('win', win)):
                    columns[key].append(value)
    arrays = {k: np.array(v) for k, v in columns.items()}
    arrays['guard_ok'] = arrays['guard_ok'].astype(bool)
    arrays['strict_ok'] = arrays['strict_ok'].astype(bool)
    return lib.sort_table(arrays)


SCENARIOS = {
    'null': dict(),
    'bots_no_information': dict(planted=0.25, delta=0.0),
    'plant_0.05': dict(planted=0.25, delta=0.05),
    'plant_0.10': dict(planted=0.25, delta=0.10),
    'plant_0.25': dict(planted=0.25, delta=0.25),
    'plant_0.40': dict(planted=0.25, delta=0.40),
    'subset_quarter_0.40': dict(planted=0.25, delta=0.40, informed_share=0.25),
    'trap_crowded_win': dict(trap='crowded_win'),
    'trap_news_day': dict(trap='news_day'),
    'trap_news_day_bots': dict(trap='news_day_bots'),
    'trap_slow_news': dict(trap='slow_news'),
    'trap_slow_news_bots': dict(trap='slow_news_bots'),
    'all_tokens_informed_0.25': dict(planted=1.0, delta=0.25),
    'few_wallets_0.25': dict(planted=0.25, delta=0.25, wallet_pool=5),
    'trap_momentum': dict(trap='momentum', planted=0.25, delta=0.0),
    'trap_rising_exit': dict(trap='rising_exit', planted=0.25, delta=0.0),
}


def run(name, config, facts, seed, boot, h2_draws, window=lib.PRIMARY):
    t = make(seed, facts=facts, **config)
    result = lib.analyse_window(t, window, boot, h2_draws, seed)
    label, reasons = lib.verdict(result)
    return dict(scenario=name, facts=facts, seed=seed, window=window, verdict=label, reasons=reasons, diff=result['h1']['diff'], ci=result['h1']['ci'], p=result['h1']['p'], matched_share=result['h1']['matched_share'], triggers=result['h1']['n_triggers'], facts_triggers=result['h1']['facts_triggers'], nce_diff=result['nce']['diff'], nce_rows=result['nce']['matched'], week_p=result['by_week']['p'], kish=result['h1']['kish_facts'], raw=result['raw']['mean'], raw_upper=result['raw']['ci'][1], strict_diff=result['strict']['diff'], strict_p=result['strict']['p'], without_top_wallets=result['without_top_wallets'], h1_positive=bool(result['h1']['p'] is not None and result['h1']['p'] < lib.ALPHA and result['h1']['diff'] > 0), h2_p=result['h2']['p'], h2_obs=result['h2']['observed'], h2_null=result['h2']['null_median'], influence=result['influence'], rows=result['counts']['rows'], eligible=result['counts']['eligible'])


def _task(args):
    name, facts, seed, boot, h2_draws, window = args
    return run(name, SCENARIOS[name], facts, seed, boot, h2_draws, window)


def main(out, quick=False):
    boot, h2_draws = (200, 49) if quick else (400, 49)
    tasks = []
    for facts, seeds in (((400, range(3)),) if quick else ((400, range(20)), (200, range(10)), (800, range(10)))):
        tasks += [(name, facts, 1000 + seed, boot, h2_draws, lib.PRIMARY) for name in SCENARIOS for seed in seeds]
    if not quick:
        # false passes at the stopping size need more than 20 seeds: 2 of 20 accepts a true rate of 20% one time in five
        tasks += [(name, 400, 1000 + seed, boot, h2_draws, lib.PRIMARY) for name in SCENARIOS if name.startswith('trap') or name in ('null', 'bots_no_information') for seed in range(20, 100)]
        tasks += [(name, 400, 2000 + seed, boot, h2_draws, window) for window in lib.WINDOWS if window != lib.PRIMARY for name in ('null', 'bots_no_information', 'plant_0.25', 'trap_news_day_bots', 'trap_slow_news_bots') for seed in range(10)]
    lines, started = [], time.time()

    def flush():
        tmp = out + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(dict(lines=lines, boot=boot, h2_draws=h2_draws, tasks=len(tasks), code_note='written by ctl_10_synth.py'), f, indent=0)
        os.replace(tmp, out)
    with ProcessPoolExecutor(max_workers=3) as pool:
        for i, line in enumerate(pool.map(_task, tasks, chunksize=4)):
            lines.append(line)
            if i % 100 == 99:
                print(i + 1, 'of', len(tasks), round(time.time() - started), flush=True)
                flush()
    flush()
    print('done', len(lines), round(time.time() - started), flush=True)
    if not quick:
        from registre import enregistrer
        enregistrer(ETUDE, test='controls_all_scenarios', declare=True, n=len(lines), agent='etude-sync-v2', donnees='synthetiques', n_comparaisons=len(lines), sortie=os.path.relpath(out, ETUDE), note='synthetic only')


if __name__ == '__main__':
    main(sys.argv[1], '--quick' in sys.argv)
