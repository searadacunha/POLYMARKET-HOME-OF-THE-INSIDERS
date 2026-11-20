"""Part A of PLAN.md: C4 and C5 recomputed with each payer described at the block of its payment.

    python3 -I -B pit_classify.py STUDY_DIR STATE_DB OUT_DIR [HOPS_DB]

The grouping logic is the published, unmodified `feat_40_groups.classify` of the frozen study. `build_links` describes an
address by one row read on 14 November 2026; `links()` below is the same procedure with a description that depends on
the block. Run with the frozen description, it must return exactly the frozen links (checked on every run, the run
stops otherwise). Run with the block description, tags are not used (no historical tag exists) and an address whose
state could not be read is UNRESOLVED: it never links, and it is counted.

Outputs in OUT_DIR: `strict_c4.json` (entry id -> c4, c5 flags, for entries flagged by either version),
`strict_summary.json` (counts). Wallet addresses other than the documented case are not written."""
import collections, json, os, sqlite3, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "research_notes", "realtime-intelligence-2026-11-14", "study", "code"))
import feat_40_groups as G  # noqa: E402  (frozen, published, imported read-only)

EMPTY = ("0x", "0x0")


def is_7702(code):
    return isinstance(code, str) and len(code) == 48 and code.lower().startswith("0xef0100")


def load(study):
    ro = lambda p: sqlite3.connect(f"file:{study}/{p}?mode=ro&immutable=1", uri=True)
    fun, ent = ro("data/funding.sqlite"), ro("derived/entries.sqlite")
    payers = {r[0]: r[1:] for r in fun.execute("select address, is_contract, nonce_today, tags, tags_status from payers")}
    hops = collections.defaultdict(list)
    for payer, block, rows in fun.execute("select payer, block, rows from hops where status='ok'"):
        for r in json.loads(rows):
            if r not in hops[payer]:
                hops[payer].append(r)
    todo = [json.loads(l) for l in open(os.path.join(study, "derived", "funding_todo.jsonl"))]
    current = {(e["wallet"], d[2]) for e in todo for d in e["deposits"]}
    dep = collections.defaultdict(list)
    for wallet, tx, ts, payer, block in fun.execute("select wallet, tx, ts, payer, block from deposits where status='ok' and payer is not null"):
        if (wallet, tx) in current:
            dep[wallet].append((ts, tx, payer, block))
    inflows = {(r[0], r[1]): json.loads(r[2]) for r in fun.execute("select wallet, tx, rows from inflows where status='ok'") if (r[0], r[1]) in current}
    event = dict(ent.execute("select id, event_id from entries where tier1=1"))
    entries = [{"id": e["id"], "wallet": e["wallet"], "t": e["t"], "event": event[e["id"]], "txs": {d[2] for d in e["deposits"]}} for e in todo]
    groups = ro("derived/groups.sqlite")
    frozen = {r[0]: (r[1], r[2]) for r in groups.execute("select id, c4, c5 from groups")}
    return payers, dict(hops), dep, inflows, entries, frozen


def links(deposits, person_like, pass_through, hops, inflows):
    """feat_40_groups.build_links with person_like(a, block) and pass_through(a, block). Same order, same windows."""
    out = []

    def add(ts, wallet, tx, sender, block, kind):
        if sender == wallet or not person_like(sender, block):
            return
        out.append((ts, wallet, sender, kind, tx))
        if pass_through(sender, block):
            for h in hops.get(sender, []):
                s = h.get("from", "").lower()
                if s and block - G.WINDOW <= h["block"] <= block and s not in (wallet, sender) and person_like(s, h["block"]):
                    out.append((ts, wallet, s, 1, tx))
    for wallet, ds in deposits.items():
        for ts, tx, payer, block in ds:
            add(ts, wallet, tx, payer, block, 0)
            for r in inflows.get((wallet, tx), []):
                if r["tx"] != tx and block - G.WINDOW <= r["block"] <= block:
                    add(ts, wallet, tx, r["from"].lower(), r["block"], 2)
    return sorted(set(out))


class BlockState:
    """State of an address at a block, from the answers stored by pit_state.py, using only chain-true monotonicity."""
    def __init__(self, path, today):
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        self.v = {(a, b, w): (v, s) for a, b, w, v, s in con.execute("select address, block, what, value, status from st")}
        self.need = {}
        self.today = today                       # {address: (is_contract, nonce_today, tags, tags_status)}
        self.unresolved = collections.Counter(); self.reasons = collections.Counter()

    def _get(self, a, b, w):
        v, s = self.v.get((a, str(b), w), (None, None))
        return v if s == "ok" else None

    def code(self, a, b, first):
        now = self._get(a, "latest", "code")
        if now is None:
            return None
        if now not in EMPTY and not is_7702(now):
            c0 = self._get(a, first, "code")
            if c0 is None:
                return None
            if c0 not in EMPTY:
                return c0                         # a contract at the earliest block stays one
        c = self._get(a, b, "code")
        if c in EMPTY and now not in EMPTY:              # amendment 2: deployed or delegated in the block of the payment
            end = self._get(a, b, "code_end")
            return end if end is not None else None
        return c

    def nonce(self, a, b, first):
        t = self.today.get(a)
        n_today = t[1] if t else None
        if n_today is not None and n_today >= G.BUSY_NONCE:
            n0 = self._get(a, first, "nonce")
            if n0 is not None and int(n0, 16) >= G.BUSY_NONCE:
                return int(n0, 16)                # busy at the earliest block, hence later
        n = self._get(a, b, "nonce")
        if n is not None:
            return int(n, 16)
        if n_today is not None and n_today <= 5:
            return n_today                        # at most 5 today, hence at most 5 at every earlier block
        return None


def main(study, state_db, out_dir, hops_db=None):
    payers, hops, dep, inflows, entries, frozen = load(study)
    # 1. the frozen description through links() must give exactly the frozen links
    today_like = lambda a, b: (lambda k: k is not None and k[0] == 0 and k[3] == "ok" and k[2] == "[]" and k[1] < G.BUSY_NONCE)(payers.get(a))
    today_pass = lambda a, b: payers[a][1] <= G.PASS_THROUGH_NONCE
    ref = G.build_links(dep, payers, hops, collections.Counter(), inflows)
    mine = links(dep, today_like, today_pass, hops, inflows)
    assert mine == ref, f"links() differs from the frozen build_links: {len(mine)} vs {len(ref)}"
    res_ref, _ = G.classify(entries, ref)
    assert all(int(res_ref[i][0] is not None) == frozen[i][0] and int(res_ref[i][1] is not None) == frozen[i][1] for i in frozen), "frozen groups not reproduced"
    print(f"frozen links reproduced: {len(ref)} links, c4 {sum(v[0] is not None for v in res_ref.values())}, c5 {sum(v[1] is not None for v in res_ref.values())}")
    # 2. the block description
    need = json.load(open(os.path.join(os.path.dirname(state_db), "need.json")))
    first = {a: bs[0] for a, bs in need.items()}
    st = BlockState(state_db, {a.lower(): v for a, v in payers.items()})
    extra_hops = collections.defaultdict(list)
    if hops_db:
        for payer, rows in sqlite3.connect(f"file:{hops_db}?mode=ro", uri=True).execute("select payer, rows from hops where status='ok'"):
            for r in json.loads(rows):
                if r not in extra_hops[payer]:
                    extra_hops[payer].append(r)
    all_hops = {k: list(v) for k, v in hops.items()}
    for k, v in extra_hops.items():
        all_hops.setdefault(k, []).extend(x for x in v if x not in all_hops.get(k, []))
    pass_unread = set()

    def plain(a, b):
        a = a.lower()
        c = st.code(a, b, first.get(a, b))
        if c is not None and c not in EMPTY:       # code at the block: a contract, or a key delegated through EIP-7702
            st.reasons["delegated_7702_at_block" if is_7702(c) else "contract_at_block"] += 1
            return False
        n = st.nonce(a, b, first.get(a, b))
        if n is not None and n >= G.BUSY_NONCE:
            return False                           # busy settles it whatever the code
        if c is None or n is None:
            st.unresolved["code" if c is None else "nonce"] += 1
            return False
        return True

    def pas(a, b):
        a = a.lower(); n = st.nonce(a, b, first.get(a, b))
        if n is None:
            st.unresolved["nonce_pass"] += 1; return False
        if n <= G.PASS_THROUGH_NONCE and a not in hops and a not in extra_hops:
            pass_unread.add((a, b))
        return n <= G.PASS_THROUGH_NONCE
    tagged_today = {a.lower() for a, k in payers.items() if k[2] not in ("[]", None)}
    plain_tags = lambda a, b: a.lower() not in tagged_today and plain(a, b)
    variant = {}
    for name, fn in (("block_state_today_tags", plain_tags),):        # amendment 2, decomposition only
        lk = links(dep, fn, pas, all_hops, inflows); r2, _ = G.classify(entries, lk); ev2 = {e["id"]: e["event"] for e in entries}
        variant[name] = {"links": len(lk), "c4_entries": sum(v[0] is not None for v in r2.values()), "c5_entries": sum(v[1] is not None for v in r2.values()),
                         "c4_events": dict(collections.Counter(ev2[i] for i, v in r2.items() if v[0] is not None))}
    st.unresolved.clear(); st.reasons.clear(); pass_unread.clear()
    strict = links(dep, plain, pas, all_hops, inflows)
    res, cnt = G.classify(entries, strict)
    ref_set, strict_set = set(ref), set(strict)
    roots_ref = {x[2] for x in ref}; roots_new = {x[2] for x in strict}
    why = collections.Counter()
    for x in strict_set - ref_set:
        k = payers.get(x[2])
        why["undescribed_in_frozen" if k is None else "tagged_today" if k[2] not in ("[]", None) else "busy_today" if (k[1] or 0) >= G.BUSY_NONCE
            else "contract_today" if k[0] else "hop_through_new_pass_through" if x[3] == 1 else "other"] += 1
    flagged = {i: {"c4": int(res[i][0] is not None), "c5": int(res[i][1] is not None), "frozen_c4": frozen[i][0], "frozen_c5": frozen[i][1]}
               for i in res if res[i][0] is not None or res[i][1] is not None or frozen[i][0] or frozen[i][1]}
    ev = {e["id"]: e["event"] for e in entries}
    c4_events = collections.Counter(ev[i] for i, v in flagged.items() if v["c4"])
    summary = {
        "links_frozen": len(ref), "links_strict": len(strict), "links_added": len(strict_set - ref_set), "links_removed": len(ref_set - strict_set),
        "added_by_reason": dict(why), "roots_frozen": len(roots_ref), "roots_strict": len(roots_new),
        "unresolved_reads": dict(st.unresolved), "delegated_7702_checks": dict(st.reasons),
        "pass_through_at_block_hops_unread": len(pass_unread),
        "c4_entries_frozen": sum(v["frozen_c4"] for v in flagged.values()), "c4_entries_strict": sum(v["c4"] for v in flagged.values()),
        "c5_entries_frozen": sum(v["frozen_c5"] for v in flagged.values()), "c5_entries_strict": sum(v["c5"] for v in flagged.values()),
        "c4_events_strict": dict(c4_events), "classify_counters": dict(cnt),
        "pass_through_keys_unread": len({a for a, _ in pass_unread}), "decomposition": variant,
    }
    # every strict C4 event, described; the root's state read TODAY is context for the reader, never used by the class
    ro = lambda q: sqlite3.connect(f"file:{study}/{q}?mode=ro&immutable=1", uri=True)
    erow = {r[0]: r[1:] for r in ro("derived/entries.sqlite").execute("select id, t, price, cash from entries where id in (%s)" % ",".join(
        str(i) for i, v in flagged.items() if v["c4"]) or "0")}
    events = {}
    for i, v in flagged.items():
        if not v["c4"]:
            continue
        e = events.setdefault(ev[i], {"event_id": ev[i], "alerts": [], "roots_today": {}})
        t, price, cash = erow[i]
        e["alerts"].append({"t": t, "price": round(price, 4), "entry_usd": round(cash, 2), "frozen_c4": v["frozen_c4"]})
        root = res[i][0][1]; k = payers.get(root)
        label = e.setdefault("_labels", {}).setdefault(root, "documented funder" if root == "0xe206961002feebd9edb152eed9b630a351874043"
                                                        else f"root {len(e['_labels']) + 1}")
        e["roots_today"][label] = {"code_today": bool(k and k[0]), "sent_transactions_today": k and k[1],
                                   "public_tags_today": json.loads(k[2]) if k and k[2] else None}
    for e in events.values():
        e.pop("_labels", None); e["alerts"].sort(key=lambda a: a["t"]); e["alert_entries"] = len(e["alerts"])
    summary["c4_events_described"] = sorted(events.values(), key=lambda e: e["alerts"][0]["t"])
    ends = [v for (a, b, w), (v, s_) in st.v.items() if w == "code_end" and s_ == "ok"]
    summary["code_at_end_of_payment_block"] = {"pairs": len(ends), "delegated_7702": sum(map(is_7702, ends)),
                                               "deployed": sum(1 for c in ends if c not in EMPTY and not is_7702(c)),
                                               "still_no_code": sum(1 for c in ends if c in EMPTY)}
    summary["archive_reads"] = sum(1 for (a, b, w), (v, s_) in st.v.items() if b != "latest" and s_ == "ok")
    summary["reads_of_code_today"] = sum(1 for (a, b, w), (v, s_) in st.v.items() if b == "latest" and s_ == "ok")
    summary["reads_left_in_error"] = sum(1 for (a, b, w), (v, s_) in st.v.items() if s_ != "ok")
    os.makedirs(out_dir, exist_ok=True)
    json.dump({str(i): v for i, v in sorted(flagged.items())}, open(os.path.join(out_dir, "strict_c4.json"), "w"), indent=0, sort_keys=True)
    json.dump(summary, open(os.path.join(out_dir, "strict_summary.json"), "w"), indent=1, sort_keys=True)
    with open(os.path.join(out_dir, "strict_roots.local.json"), "w") as f:          # addresses: kept local, not published
        json.dump({str(i): {"c4": res[i][0], "c5": res[i][1], "roots": {r: list(x) for r, x in res[i][2].items()}} for i in flagged}, f, indent=0)
    with open(os.path.join(out_dir, "pass_through_unread.local.json"), "w") as f:   # addresses: kept local, not published
        json.dump(sorted(pass_unread), f)
    print(json.dumps(summary, indent=1, sort_keys=True))


def _selftest():
    deps = {"w1": [(100, "t1", "0xk", 50)], "w2": [(200, "t2", "0xk", 60)]}
    hops = {"0xk": [{"from": "0xh", "block": 55}]}
    pl = lambda a, b: a in ("0xk", "0xh")
    assert links(deps, pl, lambda a, b: a == "0xk" and b >= 60, hops, {}) == [(100, "w1", "0xk", 0, "t1"), (200, "w2", "0xh", 1, "t2"), (200, "w2", "0xk", 0, "t2")]
    assert is_7702("0xef0100" + "ab" * 20) and not is_7702("0x6080")
    print("pit_classify selftest ok")


if __name__ == "__main__":
    _selftest() if sys.argv[1:] == ["selftest"] else main(*sys.argv[1:5])
