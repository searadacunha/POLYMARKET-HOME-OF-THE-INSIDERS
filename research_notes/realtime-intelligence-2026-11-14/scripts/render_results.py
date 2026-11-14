"""Write the tables of RESULTS.md from the outputs of the frozen study (study/derived/), between the markers
<!-- table:NAME --> and <!-- /table:NAME -->. Nothing is typed by hand: verify.py checks that the page is this rendering.

    python3 -I scripts/render_results.py            (rewrites RESULTS.md in place)
    python3 -I scripts/render_results.py --check    (exit 1 if RESULTS.md is not the rendering)"""
import json, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(HERE, "study", "derived", *p)
PAGE = os.path.join(HERE, "RESULTS.md")
pts = lambda x: "" if x is None else f"{100 * x:+.1f}"
pv = lambda x: "" if x is None else (f"{x:.2g}" if x < 0.01 else f"{x:.2f}")


def tables():
    v = json.load(open(D("verdict.json"))); r = json.load(open(D("results_tests.json")))
    out = {}
    rows = ["| Class | Verdict | Alerted entries | Alert events | Won | Wallets | Excess, points | 95 % interval | T1 p | T2 difference, points | T2 p | Negative control T1 p |",
            "|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|"]
    for cls, x in v["classes"].items():
        p = r["primary"][cls]; lo, hi = x["excess_ci"]
        rows.append(f"| {cls} | {x['verdict']} | {p['entries_alerted']} | {x['alert_events']} | {p['t1']['wins'] if x['alert_events'] else ''} | {p['wallets']} | {pts(x['excess'])} | "
                    f"{'' if lo is None else pts(lo) + ' to ' + pts(hi)} | {pv(x['t1_p'])} | {pts(x['t2_diff'])} | {pv(x['t2_p'])} | {pv(x['negative_control_t1_p'])} |")
    out["primary"] = "\n".join(rows)
    rows = ["| Class | VALIDATION x PUBLIC_PROCESS: events, excess, p | DISCOVERY x INFO: events, excess, p |", "|---|---|---|"]
    for cls in r["negative_control"]:
        a, b = r["negative_control"][cls]["t1"], r["discovery"][cls]["t1"]
        f = lambda t: f"{t['n']}, {pts(t['excess'])}, {pv(t['p'])}" if t["n"] else "0"
        rows.append(f"| {cls} | {f(a)} | {f(b)} |")
    out["other"] = "\n".join(rows)
    rows = ["| Variant | " + " | ".join(c.split("_")[0] for c in ("C1_FRESH_FUNDED_BET", "C2_DORMANT_REACTIVATION", "C3_OUT_OF_CHARACTER", "R1_S_FRESH_REPLICATION")) + " |",
            "|---|---:|---:|---:|---:|"]
    rb = r["robustness"]; cs = ("C1_FRESH_FUNDED_BET", "C2_DORMANT_REACTIVATION", "C3_OUT_OF_CHARACTER", "R1_S_FRESH_REPLICATION")
    lines = [("Excess, one alert per event", lambda x: f"{pts(x['excess'])} (n {x['n']})"),
             ("Weeks resampled, 95 % interval", lambda x: f"{pts(x['week_block_ci'][0])} to {pts(x['week_block_ci'][1])}"),
             ("Any single event left out, range", lambda x: f"{pts(x['leave_one_event_out'][0])} to {pts(x['leave_one_event_out'][1])}"),
             ("Strictly before the scheduled end", lambda x: f"{pts(x['before_scheduled_end_date']['excess'])} (n {x['before_scheduled_end_date']['n']})"),
             ("At least 24 h before the real close", lambda x: f"{pts(x['lead_24h']['excess'])} (n {x['lead_24h']['n']})"),
             ("Entry of 5,000 USD or more", lambda x: f"{pts(x['cash_5000']['excess'])} (n {x['cash_5000']['n']})"),
             ("At the price a follower paid", lambda x: f"{pts(x['follower']['excess_at_follow_price'])} (n {x['follower']['n']})"),
             ("First half, second half", lambda x: f"{pts(x['halves']['first']['excess'])}, {pts(x['halves']['second']['excess'])}"),
             ("Alert events a week", lambda x: f"{x['alert_events_per_week']}"),
             ("Median hours from alert to real close", lambda x: f"{round(x['lead_to_close_h']['median'])}")]
    for name, fn in lines:
        rows.append(f"| {name} | " + " | ".join(fn(rb[c]) for c in cs) + " |")
    out["robustness"] = "\n".join(rows)
    sw = r["sweep_c1"]; pl = r["placebo_c1"]
    out["sweep"] = ("| Cell of C1 | Events | Excess, points | p |\n|---|---:|---:|---:|\n" +
                    "\n".join(f"| {k} | {x['n']} | {pts(x['excess'])} | {pv(x['p'])} |" for k, x in sw.items() if isinstance(x, dict)) +
                    f"\n\nPlacebo: {pl['placebos']} random classes of the size of C1 inside its strata, share with p < 0.05: {pl['share_p_below_0.05']}, median p {pv(pl['median_p'])}.")
    out["header"] = (f"Comparisons on real data counted in the registry: {v['comparisons_on_real_data']}; corrected threshold 0.05 / "
                     f"{v['comparisons_on_real_data']} = {v['alpha_corrected']:.5f}. Population sizes (eligible entries): "
                     + ", ".join(f"{k} {n:,}" for k, n in r["populations"].items()) + f". M3 was fitted on {r['m3']['trained_on']:,} discovery entries.")
    return out


def render(text):
    for name, body in tables().items():
        text = re.sub(rf"(<!-- table:{name} -->\n)(?:.*?\n)?(<!-- /table:{name} -->)", lambda m: m.group(1) + body + "\n" + m.group(2), text, flags=re.S)
    return text


if __name__ == "__main__":
    page = open(PAGE).read(); new = render(page)
    if sys.argv[1:] == ["--check"]:
        sys.exit(0 if new == page else 1)
    open(PAGE, "w").write(new)
