"""Offline checks of experiment C's collection guards and scoring categories, on synthetic data only.

python3 -I -B test_experiment_c.py      (no network, no key, writes only to a temporary folder)
"""
import hashlib, io, json, os, sys, tempfile, time, urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment_c as C  # noqa: E402

N = 0


def check(name, cond):
    global N
    if not cond:
        raise SystemExit(f"FAIL {name}")
    N += 1
    print("ok", name)


def raises(f, exc=SystemExit):
    try:
        f()
    except exc:
        return True
    return False


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def wj(p, o):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o))


nosleep = mock.patch.object(C.time, "sleep")
nosleep.start()

# 1. HTTP guards: 429, 529, unreachable and an HTML page never become an empty list
with tempfile.TemporaryDirectory() as t:
    g = C.Get(Path(t))
    for code in (429, 529):
        err = urllib.error.HTTPError("u", code, "x", {}, io.BytesIO(b""))
        with mock.patch.object(C.urllib.request, "urlopen", side_effect=err):
            check(f"HTTP {code} stops the step after its retries", raises(lambda: g("http://x", "t", tries=3)))
    with mock.patch.object(C.urllib.request, "urlopen", side_effect=urllib.error.URLError("down")):
        check("unreachable endpoint stops the step", raises(lambda: g("http://x", "t", tries=2)))
    with mock.patch.object(C.urllib.request, "urlopen", side_effect=lambda *a, **k: Resp(b"<html>Just a moment...</html>")):
        check("Cloudflare HTML page raises, is not parsed as data", raises(lambda: g("http://x", "t"), json.JSONDecodeError))
    with mock.patch.object(C.urllib.request, "urlopen", side_effect=lambda *a, **k: Resp(b'{"a": 1}')):
        g("http://x", "t")
        before = sorted(os.listdir(t))
        g2 = C.Get(Path(t))
        g2("http://x", "t")
    check("a resumed Get never overwrites an archived response and counts only its own calls",
          set(before) < set(os.listdir(t)) and g2.n == 1 and g2.base == len(before) // 2)

# 2. Etherscan: rate limit is retried then fatal; only the exact empty and unsupported messages are accepted
rl = lambda *a, **k: {"status": "0", "message": "NOTOK", "result": "Max calls per sec rate limit reached (3/sec)"}  # noqa: E731
check("Etherscan rate limit is never an empty list", raises(lambda: C.es(rl, "k", 137, "module=account&action=txlist", "t")))
empty = lambda *a, **k: {"status": "0", "message": "No transactions found", "result": []}  # noqa: E731
check("Etherscan 'No transactions found' is the only empty list", C.es(empty, "k", 137, "module=account&action=txlist", "t") == [])
uns = lambda *a, **k: {"status": "0", "message": "NOTOK", "result": "Free API access is not supported for this chain. Upgrade"}  # noqa: E731
check("Etherscan unsupported chain is reported, not empty", C.es(uns, "k", 56, "module=account&action=txlist", "t") == "UNSUPPORTED")

# 3. Relay ground truth: a bad envelope stops the step and writes nothing; a resumed step does not refetch
with tempfile.TemporaryDirectory() as t:
    out = Path(t)
    wj(out / "c_deposits.json", {"deposits": [{"sample": "S2", "tx": "0xa"}, {"sample": "S2", "tx": "0xb"}]})
    for name, bad in (("rate-limit body", {"message": "Too many requests"}), ("truncated page", {"requests": [], "continuation": "c1"}),
                      ("non-object body", ["x"])):
        check(f"Relay {name} is never 'no request'", raises(lambda: C.step_truth(lambda *a, **k: bad, out, "S2")))
    check("nothing written after a bad envelope", not (out / "c_truth_S2.json").exists())
    calls = []

    def flaky(url, *a, **k):
        calls.append(url)
        if len(calls) == 2:
            raise SystemExit("429 after retries")
        return {"requests": []}
    check("a stopped truth step keeps what it fetched", raises(lambda: C.step_truth(flaky, out, "S2"))
          and list(json.loads((out / "c_truth_S2.json").read_text())) == ["0xa"])
    C.step_truth(lambda u, *a, **k: calls.append(u) or {"requests": []}, out, "S2")
    check("the resumed truth step fetches only the missing hash", len(calls) == 3 and calls[-1].endswith("0xb"))

# 4. EVM search: a full page of 1,000 is followed, never taken as the end
ID = "0x" + "ab" * 32
pages = {1: [{"input": "0x00", "hash": f"0x{i}", "timeStamp": "1", "to": "0xt", "isError": "0"} for i in range(1000)],
         2: [{"input": "0xdeadbeef" + ID[2:], "hash": "0xHIT", "timeStamp": "2", "to": "0xT", "isError": "0"}]}


def fake_es(get, key, chain, q, label):
    return "100" if "getblocknobytime" in q else pages[int(q.split("page=")[1].split("&")[0])]


with mock.patch.object(C, "es", fake_es):
    cost = C.defaultdict(int)
    hits = C.evm_window(None, "k", {"address": "0xs"}, 137, 0, 1, {ID}, cost)
check("EVM search pages past a full page", cost["evm_pages_etherscan_137"] == 2 and [h["hash"] for _, h in hits] == ["0xhit"])

# 5. Solana: a search stopped by MAX_PAGES is counted, and scored as incomplete coverage, never as a miss
with tempfile.TemporaryDirectory() as t:
    out, raw = Path(t) / "out", Path(t) / "raw"
    wj(out / "c_deposits.json", {"windows": {"S2_1": {"t_first": 0, "t_last": 1}}, "duplicate_ids": {},
                                 "deposits": [{"id": ID, "sample": "S2", "window": "S2_1", "tx": "0xd", "depositor": "u", "token": "t", "amount": 1}]})
    wj(out / "c_keys.json", {"solana_solver_keys": {"SOLKEY": 1}, "evm_solvers": []})
    net = SimpleNamespace(n=0, bytes=0, post=lambda *a: {"data": [{"transaction": {"message": {"instructions": []}}}], "paginationToken": "p"})
    C.step_search(net, SimpleNamespace(n=0, bytes=0), out)
    s = json.loads((out / "c_search.json").read_text())
    check("MAX_PAGES truncation is counted", s["cost"]["solana_windows_truncated"] == 1 and s["cost"]["helius_pages"] == C.MAX_PAGES)
    wj(out / "c_truth_S2.json", {"0xd": [{"in_txs": ["0xd"], "status": "success", "dest_chain": C.SOLANA, "recipient": "R", "referrer": None,
                                          "out_txs": [{"hash": "sig", "chain": C.SOLANA}]}]})
    exp = Path(t) / "x.SHA256"
    exp.write_text(hashlib.sha256((out / "c_search.json").read_bytes()).hexdigest() + "  c_search.json\n")
    r = C.step_score(raw, out, exp)
    check("truncated Solana window is coverage_incomplete, out of the denominator",
          r["S2"]["tally"] == {"coverage_incomplete": 1} and r["S2"]["summary"]["covered"] == 0 and r["S2"]["summary"]["hit_rate_on_covered"] is None)

# 6. Every scoring category, collisions, recipient agreement, denominators and the order proof
with tempfile.TemporaryDirectory() as t:
    out, raw = Path(t) / "out", Path(t) / "raw"
    rec_b, rec_n = "0x" + "11" * 20, "0x" + "22" * 20
    dep, truth = [], {"S1": {}, "S2": {}}

    def op(k, sample="S2", window="S2_1", reqs=None, tx=None):
        tx = tx or f"0x{k}tx"
        dep.append({"id": f"0x{k}id", "sample": sample, "window": window, "tx": tx, "depositor": "u", "token": "t", "amount": 1})
        if reqs is not None:
            truth[sample][tx] = reqs

    def rq(k, status="success", chain=137, out_hash=None, recipient="0xr", tx=None):
        return {"in_txs": [tx or f"0x{k}tx"], "status": status, "dest_chain": chain, "recipient": recipient, "referrer": None,
                "out_txs": [] if out_hash == "" else [{"hash": out_hash or f"0x{k}out", "chain": chain}]}
    op("a", reqs=[rq("a", chain=C.SOLANA, out_hash="solA", recipient="RECA")])                     # hit, recipient credited
    op("b", reqs=[rq("b", out_hash="0xfb", recipient=rec_b)])                                       # hit, recipient in calldata
    op("c", reqs=[rq("c", out_hash="0xright")])                                                     # wrong fill, collision
    op("d", reqs=[rq("d")])                                                                         # miss
    op("e", reqs=[rq("e", chain=56)])                                                               # provider refused the window
    op("f", reqs=[rq("f", chain=8453)])                                                             # no learned solver on Base
    op("g", reqs=[rq("g", status="refund")])                                                        # not success, fill found
    op("h", reqs=[rq("h", status="failure")])                                                       # not success, no fill
    op("i", reqs=[])                                                                                # no Relay request
    op("j")                                                                                         # ground truth missing
    op("k", reqs=[rq("k"), rq("k")])                                                                # two requests
    op("l", reqs=[rq("l", out_hash="")])                                                            # success, no fill hash
    op("m", reqs=[rq("m", tx="0xother")])                                                           # request for another tx
    op("n", reqs=[rq("n", out_hash="0xshared", recipient=rec_n)])                                   # hit, recipient not in the call
    op("o", reqs=[rq("o", out_hash="0xelse")])                                                      # wrong: the fill of n
    op("p1", tx="0xmulti", reqs=[rq("p1", tx="0xmulti")]); op("p2", tx="0xmulti")                   # two deposits in one tx
    op("s", sample="S1", window="S1_1", reqs=[rq("s", out_hash="0xs1")])                            # in-sample hit
    fill = lambda h, c=137, **x: {"chain": c, "hash": h, "solver": "0xs", "time": 1, "err": False, **x}  # noqa: E731
    found = {"0xaid": [fill("solA", C.SOLANA, lamport_credited=["RECA"], token_owner_credited=[])], "0xbid": [fill("0xfb")],
             "0xcid": [fill("0xw1"), fill("0xw2")], "0xgid": [fill("0xg")], "0xnid": [fill("0xshared")], "0xoid": [fill("0xshared")],
             "0xsid": [fill("0xs1")]}
    wj(out / "c_deposits.json", {"windows": {}, "deposits": dep, "duplicate_ids": {}})
    wj(out / "c_keys.json", {"solana_solver_keys": {"SOLKEY": 1}, "evm_solvers": [{"address": "0xs", "chain": 137}, {"address": "0xs", "chain": 56}]})
    wj(out / "c_search.json", {"found": found, "cost": {}, "uncovered": [["S2_1", 56, "0xs", "no explorer serves this chain"]],
                               "calls": {"rpc": 0, "get": 0}, "bytes": 0})
    for s in ("S1", "S2"):
        wj(out / f"c_truth_{s}.json", truth[s])
    call = "0xa9059cbb" + "0" * 24 + rec_b[2:] + "0" * 63 + "1" + "ab" * 32  # transfer(rec_b, 1) followed by an id
    wj(raw / "http" / "0001_search_evm.json", {"result": [{"hash": "0xfb", "to": "0xtoken", "input": call},
                                                          {"hash": "0xshared", "to": "0xrouter", "input": "0x12345678" + "0" * 64}]})
    exp = Path(t) / "x.SHA256"
    exp.write_text(hashlib.sha256((out / "c_search.json").read_bytes()).hexdigest() + "  c_search.json\n")
    later = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() + 3600))
    wj(raw / "http" / "0002_relay_S2.meta.json", {"fetched_utc": later, "bytes": 10})
    r = C.step_score(raw, out, exp)
    want = {"hit": 3, "wrong_fill": 2, "miss": 1, "chain_not_covered": 2, "not_success_found_fill": 1, "not_success_no_fill": 1,
            "no_relay_request": 2, "truth_missing": 1, "multiple_requests": 1, "success_without_fill_hash": 1, "multi_deposit_tx": 2}
    check("each operation lands in its own category", r["S2"]["tally"] == want)
    sm = r["S2"]["summary"]
    check("denominator holds only hit, wrong and miss with full coverage",
          sm["covered"] == 6 and sm["with_usable_truth"] == 8 and sm["coverage_rate"] == 0.75 and sm["hit_rate_on_covered"] == 0.5)
    check("not-covered reasons are named", r["S2"]["not_covered_by_reason"] == {"provider_refused_window:56": 1, "no_learned_solver_on_chain:8453": 1})
    check("collisions are counted", sm["collisions"] == {"ids_with_several_fills": 1, "fills_matching_several_ids": 1, "duplicate_deposit_ids": 0})
    check("recipient agreement on hits", sm["recipient_on_hits"] == {"agrees": 2, "differs": 1})
    check("S1 is labelled in-sample", r["S1"]["role"].startswith("in-sample") and r["S1"]["summary"]["exact"] == 1)
    check("order proof holds when the truth comes after the search", r["order"]["search_before_s2_truth"] is True)
    wj(raw / "http" / "0003_relay_S2.meta.json", {"fetched_utc": "2000-01-01T00:00:00+00:00", "bytes": 10})
    check("order proof fails when a truth request came first", C.step_score(raw, out, exp)["order"]["search_before_s2_truth"] is False)
    exp.write_text("0" * 64 + "  c_search.json\n")
    check("a search file other than the hashed one is refused", raises(lambda: C.step_score(raw, out, exp)))

print(f"{N}/{N} checks passed")
