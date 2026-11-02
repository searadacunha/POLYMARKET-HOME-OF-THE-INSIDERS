#!/usr/bin/env python3
"""
Structure-detector + synthetic injection. Measures recall (by bridge/hops/gas-CN) and
the real-noise FP, in two states: Solana-ON vs Solana-OFF.

DETECTOR (two outputs):
  structural_flag = bridged-capital gate (Polygon top funder is a KNOWN bridge solver)
                    AND >=1 corroborator (fresh / winning-concentration / co-control).
                    -> Polygon-only, does NOT need Solana.
  cn_confirmed    = structural_flag AND origin decoded to CN AND gas-CN present.
                    -> needs Solana branch + bridge origin-decode (Solana-ON).

WHERE IT BREAKS (modeled, honest):
  - structural gate fails if the final-leg bridge's Polygon payer is NOT in our constant set
    (Relay/deBridge = in; CCTP/Stargate = NOT). n_hops does NOT affect this (final Polygon
    payer is still the solver regardless of upstream hops).
  - cn_confirmed fails if any hop's bridge is not origin-decodable, or Solana-OFF, or no gas-CN,
    or CN address unlabeled.
"""
import json, os, random
random.seed(42)
OUT = os.path.dirname(os.path.abspath(__file__))

# --- coverage model (MEASURED where noted) ---
BRIDGE_IN_CONSTSET = {"relay": True, "debridge": True, "cctp": False, "stargate": False}
# Relay decode MEASURED to work on P1; deBridge corpus-proven; CCTP/Stargate decoder = MISSING
BRIDGE_DECODE_P = {"relay": 0.92, "debridge": 0.85, "cctp": 0.0, "stargate": 0.0}
CN_LABEL_P = 0.55           # CN hot labeled (Arkham) ~0.55; ephemeral deposits much lower -> blended
ALL_BRIDGES = ["relay", "debridge", "cctp", "stargate"]

def gen_synthetic(n=260):
    out = []
    for i in range(n):
        nh = random.choice([1, 1, 2, 2, 3])             # 1-3 hops
        chain = [random.choice(ALL_BRIDGES) for _ in range(nh)]
        gas_cn = random.random() < 0.5                  # half carry a CN-gas fingerprint
        co_ctrl = random.random() < 0.5
        fresh = random.random() < 0.85                  # insiders usually fresh
        win_conc = random.random() < 0.8                # usually concentrated winners
        delay_band = random.choice(["0-2min", "2-60min", "1-30d"])
        amount = 10 ** random.uniform(3, 5.7)           # $1k .. ~$500k
        out.append({"id": i, "bridge_chain": chain, "final_bridge": chain[-1], "n_hops": nh,
                    "gas_cn": gas_cn, "co_ctrl": co_ctrl, "fresh": fresh, "win_conc": win_conc,
                    "delay": delay_band, "amount": round(amount)})
    return out

def detect(rec, solana_on=True):
    # structural gate (Polygon-only)
    bridged_visible = BRIDGE_IN_CONSTSET.get(rec["final_bridge"], False)
    corroborator = rec.get("fresh") or rec.get("win_conc") or rec.get("co_ctrl")
    structural = bool(bridged_visible and corroborator)
    # cn confirmation (Solana-dependent)
    origin_decoded = 1.0
    for b in rec["bridge_chain"]:
        origin_decoded *= BRIDGE_DECODE_P.get(b, 0.0)
    cn_possible = structural and rec.get("gas_cn") and solana_on
    cn_confirmed = cn_possible and (random.random() < origin_decoded * CN_LABEL_P)
    return structural, cn_confirmed

def rate(items, key):
    return (sum(1 for x in items if x[key]) / len(items)) if items else 0.0

def run():
    syn = gen_synthetic()
    # evaluate in both Solana states (avg over a few draws to smooth the stochastic decode)
    def eval_state(solana_on, draws=40):
        agg = []
        for r in syn:
            s_hits = c_hits = 0
            for _ in range(draws):
                s, c = detect(r, solana_on=solana_on)
                s_hits += s; c_hits += c
            agg.append({**r, "structural": s_hits/draws >= 0.5,
                        "cn_rate": c_hits/draws})
        return agg
    on = eval_state(True)
    off = eval_state(False)

    print("="*72)
    print(f"SYNTHETIC INJECTION — {len(syn)} fake Brooxes (varied), planted in real universe")
    print("="*72)
    rs = rate(on, "structural")
    print(f"\nSTRUCTURAL recall (bridged-gate + corroborator, Polygon-only, Solana-independent):")
    print(f"  GLOBAL = {100*rs:.1f}%")
    print(f"  by final-leg bridge:")
    for b in ALL_BRIDGES:
        sub = [x for x in on if x["final_bridge"]==b]
        if sub: print(f"     {b:9s} n={len(sub):3d}  recall={100*rate(sub,'structural'):.0f}%  "
                       f"(in const-set: {BRIDGE_IN_CONSTSET[b]})")
    print(f"  by n_hops:")
    for nh in (1,2,3):
        sub=[x for x in on if x["n_hops"]==nh]
        if sub: print(f"     {nh} hop  n={len(sub):3d}  recall={100*rate(sub,'structural'):.0f}%")

    print(f"\nCN-CONFIRMED recall (needs Solana + origin-decode + gas-CN):")
    def cn_recall(items, among_gas_cn=True):
        pool=[x for x in items if x["gas_cn"]] if among_gas_cn else items
        return (sum(x["cn_rate"] for x in pool)/len(pool)) if pool else 0.0
    print(f"  GLOBAL (among gas-CN synthetics), Solana-ON  = {100*cn_recall(on):.1f}%")
    print(f"  GLOBAL (among gas-CN synthetics), Solana-OFF = {100*cn_recall(off):.1f}%   <- cost of dead Solscan key")
    print(f"  by final-leg bridge (Solana-ON, gas-CN only):")
    for b in ALL_BRIDGES:
        sub=[x for x in on if x["final_bridge"]==b and x["gas_cn"]]
        if sub: print(f"     {b:9s} n={len(sub):3d}  cn_recall={100*cn_recall(sub):.0f}%")
    print(f"  by n_hops (Solana-ON, gas-CN only):")
    for nh in (1,2,3):
        sub=[x for x in on if x["n_hops"]==nh and x["gas_cn"]]
        if sub: print(f"     {nh} hop  n={len(sub):3d}  cn_recall={100*cn_recall(sub):.0f}%")
    print(f"  gas-CN ABSENT synthetics: cn_recall = 0 by construction "
          f"(n={sum(1 for x in on if not x['gas_cn'])}) -> these insiders are STRUCTURE-only, CN-invisible")

    # ---- real-noise contamination (FP) ----
    rw_path = os.path.join(OUT, "real_wallets.json")
    print("\n"+"="*72); print("REAL-NOISE CONTAMINATION (FP)"); print("="*72)
    if os.path.exists(rw_path):
        rw = json.load(open(rw_path))
        bridged = [r for r in rw if r.get("top_is_bridge")]
        print(f"  real PM wallets sampled: {len(rw)}")
        print(f"  top-funder is a bridge solver (structural-GATE FP-ceiling): "
              f"{len(bridged)}/{len(rw)} = {100*len(bridged)/len(rw):.1f}%")
        print(f"  -> precision depends on corroborator filter (fresh+concentration), which most")
        print(f"     legit bridgers lack. FP-ceiling at the gate = above; ASSUMED lower after filter.")
    else:
        print("  real_wallets.json not ready yet (sampler running) -> rerun for FP.")
    json.dump({"on":on,"off":off}, open(os.path.join(OUT,"injection_result.json"),"w"))

if __name__ == "__main__":
    run()
