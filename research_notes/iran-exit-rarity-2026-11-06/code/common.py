"""Shared definitions of the exit-rarity study (analysis_plan.md). Standard library only.

Everything that decides a number lives here: constants, the withdrawal rule, the graph
statistics, the degree-preserving null and the verdict. Collectors and the analysis import it.
"""
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

ETUDE = Path(__file__).resolve().parents[1]
DATA = ETUDE / "data"
RAW = Path("/Volumes/TravailExterne/Enquetes-Crypto/iran_exit_rarity_20261106/raw")  # third-party pages, outside git

# Population and shock rule (plan, "Population")
WINDOW_S = 22_500          # 6 h 15 min, the reference window 00:00-06:15 UTC
JUMP_PRICE = 0.90          # first Yes taker row at or above this price ...
PRE_VWAP = 0.50            # ... whose preceding window has a Yes VWAP at or below this
MIN_USDC = 1_000.0         # Yes bought in the window, sum of size * price over BUY rows
MIN_POP = 10               # smaller populations are excluded and counted
SHOCK_GAP_S = 6 * 3600     # two shocks closer than this are one shock
CATALOG_GAP_S = 6 * 3600   # markets jumping within this of a catalogued (alleged) event are not comparators
MAX_TRADE_PAGES = 1500     # 1.5 M rows back from the last trade; beyond, the population is incomplete

# Exit data (plan, "Data")
PM_REF = "funxyz|su4gnoxz14"
POLYGON = 137
MAX_RELAY_PAGES = 100

# Recipient classes (plan, "Recipient classes")
SERVICE_USERS = 25         # distinct Relay users paying the recipient, read on at most 5 pages
SERVICE_PAGES = 5
DELEGATION_PREFIX = "0xef0100"   # EIP-7702 delegation designator: still an EOA
SYSTEM_PROGRAM = "11111111111111111111111111111111"

# Inference (plan, "Tests")
SEED = 20261106
PERMUTATIONS = 2000
TRADES_PER_WALLET = 5      # curveball trades per visible wallet, per permutation
ALPHA = 0.01
MIN_COMPARATORS = 10
POWER_G, POWER_R = 9, 3    # planted benchmark: 9 visible wallets holding 3 new CUSTOMER recipients
POWER_SEEDS, POWER_MIN = 3, 2  # a comparator counts only if the benchmark is found in >= 2 of 3 seeds


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_atomic(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)


def fetch(url, out: Path, counters, body=None, redact=None, tries=8, wait=15):
    """GET (or POST when body is given), archived with its SHA-256. Returns the parsed JSON.

    429, 5xx, dropped connections and truncated JSON are retried and counted; any other HTTP status
    stops the run. A response is never turned into an empty result here: callers check its shape."""
    import http.client
    import time
    import urllib.error
    import urllib.request
    from datetime import datetime, timezone
    hdr = {"user-agent": "exit-rarity-research/1.0", "accept": "application/json", "content-type": "application/json"}
    shown = url.replace(redact, "<KEY>") if redact else url
    for i in range(tries):
        counters["requests"] = counters.get("requests", 0) + 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=hdr), timeout=90) as r:
                raw = r.read()
            parsed = json.loads(raw)
        except urllib.error.HTTPError as e:
            k = "http_429" if e.code == 429 else ("http_5xx" if e.code >= 500 else f"http_{e.code}")
            counters[k] = counters.get(k, 0) + 1
            if e.code == 429 or e.code >= 500:
                time.sleep(wait * (i + 1)); continue
            raise SystemExit(f"{shown}: HTTP {e.code}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException, json.JSONDecodeError) as e:
            counters["network_or_json_errors"] = counters.get("network_or_json_errors", 0) + 1
            if redact:
                e = type(e).__name__
            time.sleep(wait * (i + 1)); continue
        write_atomic(out, raw)
        write_atomic(out.with_suffix(".meta.json"), json.dumps(
            {"url": shown, "body": body.decode() if body else None, "sha256": sha256(raw), "bytes": len(raw),
             "fetched_utc": datetime.now(timezone.utc).isoformat()}, indent=1).encode())
        counters["ok"] = counters.get("ok", 0) + 1
        return parsed
    raise SystemExit(f"{shown}: failed after {tries} tries")


def relay_page(b, where):
    """Shape of one Relay requests/v2 page: a list of requests, and no continuation on an empty page."""
    if not isinstance(b, dict) or not isinstance(b.get("requests"), list):
        raise SystemExit(f"{where}: Relay page without a list of requests: {str(b)[:200]}")
    if not b["requests"] and b.get("continuation"):
        raise SystemExit(f"{where}: empty Relay page with a continuation")
    return b["requests"], b.get("continuation")


def low(a):
    return a.lower() if isinstance(a, str) and a.startswith("0x") else a


def flat(r):
    """Same reading of a Relay request as the PR 27 rarity test (netlib.flat)."""
    d = r.get("data") or {}
    m = d.get("metadata") or {}
    ci, co = m.get("currencyIn") or {}, m.get("currencyOut") or {}
    return {"id": r["id"], "status": r["status"], "created": r["createdAt"], "user": low(r["user"]),
            "recipient": low(r["recipient"]), "referrer": r.get("referrer"),
            "o": (ci.get("currency") or {}).get("chainId"), "d": (co.get("currency") or {}).get("chainId")}


def is_withdrawal(o, wallet):
    """PLAN_RARITY.md definition, unchanged: a Polymarket withdrawal through Relay to another address."""
    return (o["user"] == wallet and o["o"] == POLYGON and o["status"] == "success"
            and o["referrer"] == PM_REF and o["recipient"] != wallet)


def recipients(orders, wallet):
    """Set of withdrawal recipients of one wallet, from its own reduced Relay orders."""
    return {o["recipient"] for o in orders if is_withdrawal(o, wallet)}


# ---------- graph statistics on a population ----------

def shared_customer(D, cls):
    """Recipients held by two or more visible wallets and not classed SERVICE."""
    holders = defaultdict(set)
    for w, rs in D.items():
        for r in rs:
            holders[r].add(w)
    return {r: ws for r, ws in holders.items() if len(ws) >= 2 and cls.get(r, "CUSTOMER") != "SERVICE"}


def components(D, shared):
    parent = {w: w for w in D}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for ws in shared.values():
        ws = sorted(ws)
        for v in ws[1:]:
            parent[find(v)] = find(ws[0])
    g = defaultdict(set)
    for ws in shared.values():
        for w in ws:
            g[find(w)].add(w)
    return sorted((sorted(x) for x in g.values()), key=lambda x: (-len(x), x))


def multi_wallets(shared):
    """M: wallets that share at least two distinct non-service recipients with one same other wallet."""
    pair = defaultdict(int)
    for ws in shared.values():
        ws = sorted(ws)
        for i, a in enumerate(ws):
            for b in ws[i + 1:]:
                pair[(a, b)] += 1
    return sorted({w for (a, b), k in pair.items() if k >= 2 for w in (a, b)})


def stats(D, cls):
    """Descriptive and test statistics of one population. D: visible wallet -> set of recipients."""
    sh = shared_customer(D, cls)
    comp = components(D, sh)
    m = multi_wallets(sh)
    return {"visible": len(D), "S1": sum(len(c) for c in comp), "groups": [len(c) for c in comp],
            "L": len(comp[0]) if comp else 0, "M": len(m), "k_max": max((len(v) for v in sh.values()), default=0),
            "shared_recipients": len(sh)}


# ---------- degree-preserving null ----------

def curveball(D, cls, rng, trades):
    """One draw: wallet degrees and recipient degrees kept exactly, within each recipient class.

    Each trade picks two wallets and reshuffles the recipients that only one of them holds,
    separately for each class, so a SERVICE recipient never moves into a CUSTOMER slot.
    """
    ws = sorted(D)
    cur = {w: set(D[w]) for w in ws}
    if len(ws) < 2:
        return cur
    for _ in range(trades):
        a, b = rng.sample(ws, 2)
        A, B = cur[a], cur[b]
        for c in ("CUSTOMER", "SERVICE"):
            only_a = sorted(r for r in A - B if cls.get(r, "CUSTOMER") == c)
            only_b = sorted(r for r in B - A if cls.get(r, "CUSTOMER") == c)
            if not only_a or not only_b:
                continue
            pool = only_a + only_b
            rng.shuffle(pool)
            na = len(only_a)
            A.difference_update(only_a); B.difference_update(only_b)
            A.update(pool[:na]); B.update(pool[na:])
    return cur


def permutation_test(D, cls, seed, permutations=PERMUTATIONS):
    """One-sided p for M, (1 + draws >= observed) / (1 + draws). Also returns the null mean of L."""
    obs = stats(D, cls)
    rng = random.Random(seed)
    trades = TRADES_PER_WALLET * len(D)
    ge, l_sum, m_sum = 0, 0, 0
    for _ in range(permutations):
        s = stats(curveball(D, cls, rng, trades), cls)
        ge += s["M"] >= obs["M"]
        l_sum += s["L"]; m_sum += s["M"]
    return {**obs, "p_M": (1 + ge) / (1 + permutations), "hits": ge, "draws": permutations,
            "null_mean_M": m_sum / permutations, "null_mean_L": l_sum / permutations}


def population_seed(key):
    return SEED ^ int(sha256(key.encode())[:8], 16)


def power(D, cls, key):
    """How often the test finds the planted benchmark added to this population's own structure.

    Uses only the population's degrees and recipients, never its observed M or p."""
    if len(D) < POWER_G + 1:
        return 0
    found = 0
    for s in range(POWER_SEEDS):
        rng = random.Random(population_seed(f"{key}|power|{s}"))
        planted = {w: set(v) for w, v in D.items()}
        c = dict(cls)
        for j in range(POWER_R):
            c[f"__plant{j}"] = "CUSTOMER"
        for w in rng.sample(sorted(planted), POWER_G):
            planted[w] |= {f"__plant{j}" for j in range(POWER_R)}
        found += permutation_test(planted, c, population_seed(f"{key}|power-test|{s}"))["p_M"] <= ALPHA
    return found


# ---------- between-population summary and verdict ----------

def clopper_pearson(k, n, a=0.05):
    """Exact two-sided interval, by bisection on the binomial tail (no scipy)."""
    def tail_ge(p):  # P(X >= k)
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))

    def tail_le(p):  # P(X <= k)
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))

    def solve(f, target, increasing):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if (f(mid) < target) == increasing:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else solve(tail_ge, a / 2, True)
    upper = 1.0 if k == n else solve(tail_le, a / 2, False)
    return lower, upper


def verdict(ref, comparators):
    """ref and comparators: permutation_test outputs, comparators with a "power" field.
    Only comparators where the planted benchmark is found (power >= POWER_MIN) enter n and k.
    Fixed in analysis_plan.md, section Verdict."""
    eligible = [c for c in comparators if c["power"] >= POWER_MIN]
    n = len(eligible)
    k = sum(1 for c in eligible if c["p_M"] <= ALPHA)
    r = k / n if n else None
    ci = clopper_pearson(k, n) if n else None
    if n < MIN_COMPARATORS:
        v = "UNDETERMINED"
    elif ref["p_M"] > ALPHA:
        v = "REFERENCE_NOT_DISTINCT"
    elif r <= 0.10:
        v = "RARE"
    elif r > 0.25:
        v = "COMMON"
    else:
        v = "UNCOMMON"
    return {"verdict": v, "n_comparators": n, "comparators_with_excess": k, "rate": r, "rate_ci95": ci,
            "comparators_without_power": len(comparators) - n,
            "comparators_with_excess_without_power": sum(1 for c in comparators if c["power"] < POWER_MIN and c["p_M"] <= ALPHA),
            "reference_p_M": ref["p_M"], "reference_M": ref["M"]}


def load_json(p):
    return json.loads(Path(p).read_text())


REF_T = 1772259300  # 28 February 2026 06:15 UTC, the reference event time (catalog_markets.json)


def known_groups():
    return set((DATA / "known_groups.txt").read_text().split())


def select_comparators():
    """One market per shock: complete tape, not alleged, the most wallets once known groups are removed
    (ties: smaller condition id). Kept if that count is at least MIN_POP. Ordered by distance to REF_T."""
    shocks = load_json(DATA / "shocks.json")
    known = known_groups()
    best, excluded = {}, defaultdict(int)
    for m in shocks["markets"]:
        if m["alleged"]:
            excluded["alleged"] += 1; continue
        p = DATA / "populations" / f'{m["condition"]}.json'
        if not p.exists():
            excluded["population_not_collected"] += 1; continue
        d = load_json(p)
        if d["window"] != m["window"]:
            raise SystemExit(f'{m["condition"]}: population window differs from shocks.json')
        if not d["complete"]:
            excluded["tape_incomplete"] += 1; continue
        ws = [w for w in d["wallets"] if w not in known]
        key = (-len(ws), m["condition"])
        if m["shock"] not in best or key < best[m["shock"]][0]:
            best[m["shock"]] = (key, m, ws, d["wallets"])
    kept = []
    for key, m, ws, full in best.values():
        if len(ws) >= MIN_POP:
            kept.append({**m, "wallets": ws, "wallets_with_known": full})
        else:
            excluded["population_below_min"] += 1
    n_markets = sum(1 for m in shocks["markets"] if not m["alleged"])
    excluded["same_shock_duplicate"] = n_markets - excluded["population_not_collected"] - excluded["tape_incomplete"] - len(best)
    return sorted(kept, key=lambda m: (abs(m["T"] - REF_T), m["condition"])), dict(excluded)
