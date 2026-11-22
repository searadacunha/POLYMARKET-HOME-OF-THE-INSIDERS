"""Register of addresses associated with ChangeNOW: who says so, on what independent basis, and at which tier.

A label is a third party's claim and a tier is not a function. What an address did during a week (paying out,
consolidating, funding gas) is measured from that week's transfers by `roles()` and reported next to the tier.

Tiers
  A_LABELLED    an explorer or label list names the address as ChangeNOW (lineages kept apart, since lists copy one another)
  B_STRUCTURAL  no public label; S1: funded by a tier-A address within a day of its first transaction, kept by hash.
                A flow through it is confirmed only in a week where S2 also holds: its measured role is a service role.
  C_SUSPECTED   one weak source, or behaviour alone: never used for a confirmed flow
  X_NOT_SERVICE labelled with the word ChangeNOW without being a wallet the service controls: its token, a third
                party's deposit, or the service's own deposit address at an exchange (the exchange holds that key)
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from . import chainio

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LABELS = REPO / "investigations/changenow-outflows/sources/data/attribution_sources.csv"   # label snapshot of 2026-11-02
REGISTRY = HERE / "registry.csv"
EVIDENCE = HERE / "registry_evidence.json"
REFRESH = HERE / "registry_labels_refresh.json"                                               # tags read again after the snapshot
TAGS = "https://metadata.services.blockscout.com/api/v1/metadata"
STRONG_LINEAGES = ("etherscan_tag", "blockscout_name", "oli_hildobby")
NOT_SERVICE = ("upbit hacker", "now token", "(now)", "binance deposit", "htx deposit", "okx deposit")
SERVICE_ROLES = ("PAYOUT_HOT", "GAS_FUNDER", "COLLECTOR")
# Candidates without a public label. `anchors` are tier-A addresses whose first dealings with the candidate are read
# from the chain by probe(); the criteria they meet are decided by the evidence found, not by this list.
CANDIDATES = {
    "0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423": dict(chain=137, anchors=["0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a"], machinery="0x0e2ea4d1ae07cf636e6fdde4ac89891f9dd63e2b",
                                                       documented="investigations/changenow-polymarket/sources/case_03_firm_verdict.md (controlled order of June 2026 paid from this address)"),
    "0x0e2ea4d1ae07cf636e6fdde4ac89891f9dd63e2b": dict(chain=137, anchors=[], machinery="0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423", documented=""),
    "0x64cdaa89629fe003eaa31b480d8b63372d109a53": dict(chain=1, anchors=["0xeba88149813bec1cccccfdb0dacefaaa5de94cb1", "0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b"], machinery="0x300773969b499b9768267e0c5a049f7751de79e7", documented=""),
    "0x300773969b499b9768267e0c5a049f7751de79e7": dict(chain=1, anchors=["0xeba88149813bec1cccccfdb0dacefaaa5de94cb1"], machinery="0x64cdaa89629fe003eaa31b480d8b63372d109a53", documented=""),
    "0x0658cabf40b45ef538d75ae9f7ba7f410eb04ec8": dict(chain=137, anchors=["0x3a0d24d59af3a3444dc6ef12cdb0c6e38c985288"], machinery="", documented=""),
    "0x6976d8025229db5f54bc899dd3dbc9285423896b": dict(chain=137, anchors=["0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a"], machinery="", documented=""),
}


def labels():
    """{address: {"labels": {(chain, label, lineage)}, "lineages": {lineage}}} from the dated label snapshot."""
    out = defaultdict(lambda: dict(labels=set(), lineages=set()))
    with LABELS.open() as f:
        for row in csv.DictReader(f):
            address = row["address"].lower()
            if address.startswith("0x") and len(address) == 42:
                out[address]["labels"].add((row["chain"], row["label"], row["lineage"]))
                out[address]["lineages"].add(row["lineage"])
    return out


def probe(first_rows=40):
    """First transactions of each candidate and its machinery, read from Etherscan (key needed), kept with full hashes.
    Records only facts: who sent the first value, and every early row whose counterparty is an anchor or tier-A address."""
    known = labels()
    tier_a = {a for a, v in known.items() if v["lineages"] & set(STRONG_LINEAGES) and not any(w in l.lower() for _, l, _ in v["labels"] for w in NOT_SERVICE)}
    out = {}
    for address, spec in CANDIDATES.items():
        chain = spec["chain"]
        native = chainio.etherscan(chain, module="account", action="txlist", address=address, startblock=0, endblock=999999999, page=1, offset=first_rows, sort="asc")
        tokens = chainio.etherscan(chain, module="account", action="tokentx", address=address, startblock=0, endblock=999999999, page=1, offset=first_rows, sort="asc")
        rows = []
        for kind, items in (("native", native), ("token", tokens)):
            for r in items:
                other = r["from"].lower() if r["to"].lower() == address else r["to"].lower()
                if int(r["value"] or 0) == 0 or r.get("isError", "0") != "0":
                    continue
                rows.append(dict(kind=kind, ts=int(r["timeStamp"]), utc=chainio.iso(r["timeStamp"]), block=int(r["blockNumber"]), tx=r["hash"], direction="in" if r["to"].lower() == address else "out",
                                 counterparty=other, counterparty_tier_a=other in tier_a, counterparty_is_candidate=other in CANDIDATES, symbol=r.get("tokenSymbol", chainio.CHAINS[chain]["native"]),
                                 contract=r.get("contractAddress", ""), amount=int(r["value"]) / 10 ** int(r.get("tokenDecimal") or 18)))
        rows.sort(key=lambda r: (r["ts"], r["tx"]))
        born = rows[0]["ts"] if rows else None
        out[address] = dict(chain=chain, first_value_utc=chainio.iso(born) if born else None,
                            first_inflows=[r for r in rows if r["direction"] == "in"][:6],
                            early_ties=[r for r in rows if (r["counterparty_tier_a"] or r["counterparty_is_candidate"]) and r["ts"] - born <= 86400][:12],
                            rows_read=len(rows), source=f"etherscan v2 txlist and tokentx, chain {chain}, first {first_rows} rows ascending")
    EVIDENCE.write_text(json.dumps(out, indent=1) + "\n")
    return out


def refresh(counterparties=None, say=print):
    """Read today's public tags from Blockscout's metadata service: on Ethereum for every registered address, and for
    `counterparties` ({chain: addresses}, outside addresses that dealt with the service often during a week) on Ethereum
    and on the chain where they were seen. Writes registry_labels_refresh.json. build() then adds any address that
    carries a ChangeNOW name tag today and is missing from the snapshot.

    The service's own list is not walked: it holds more than 20,000 Ethereum addresses under the ChangeNOW protocol
    tag (400 pages of 50 did not reach its end on 2026-11-15), nearly all one-time deposit addresses, which are found
    each week by what they do rather than by a label."""
    import time
    from phi_monitor import net

    def tags(chain, addresses):
        out = {}
        for part in chainio.chunks(sorted(addresses), 80):
            body = net.get_json(f"{TAGS}?chainId={chain}&addresses=" + ",".join(part), timeout=60)
            for address, entry in (body.get("addresses") or {}).items():
                out[address.lower()] = sorted({(t.get("tagType") or "", t.get("name") or "") for t in entry.get("tags", []) if t.get("tagType") in ("name", "protocol", "generic")})
            time.sleep(0.25)
        return out

    def named(found):
        return sorted({name for kind, name in found if kind == "name" and "changenow" in name.lower()})

    known, reg = labels(), load()
    today = tags(1, reg)
    still = sorted(a for a in reg if named(today.get(a, [])))
    say(f"  {len(still)} of {len(reg)} registered addresses carry a ChangeNOW name tag on Ethereum today")
    fresh, checked = {}, {}
    for chain, addresses in sorted((counterparties or {}).items()):
        outside = sorted(set(addresses) - set(reg) - set(known))
        checked[str(chain)] = len(outside)
        for tagged_on in sorted({1, int(chain)}):
            for address, found in tags(tagged_on, outside).items():
                if named(found):
                    entry = fresh.setdefault(address, dict(names=[], seen_on=[], tagged_on=[]))
                    entry["names"] = sorted(set(entry["names"]) | set(named(found)))
                    entry["seen_on"] = sorted(set(entry["seen_on"]) | {int(chain)})
                    entry["tagged_on"] = sorted(set(entry["tagged_on"]) | {tagged_on})
    say(f"  {sum(checked.values())} frequent counterparties checked, {len(fresh)} carry a ChangeNOW name tag and were not in the snapshot")
    out = dict(read_utc=chainio.iso(time.time()), source=TAGS, registered=len(reg), registered_named_changenow_today=len(still),
               tier_a_without_changenow_name_on_ethereum_today={a: dict(labels=reg[a]["labels"], lineages=reg[a]["lineages"], labelled_chains=reg[a]["labelled_chains"])
                                                                for a in sorted(reg) if reg[a]["tier"] == "A_LABELLED" and a not in still and a not in fresh},
               candidate_tags={a: [list(t) for t in today.get(a, [])] for a in sorted(CANDIDATES)}, counterparties_checked=checked, new_labelled=fresh)
    REFRESH.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return out


def criteria(address, evidence):
    """Structural facts one candidate meets, from the probed rows. Returns (codes, sentences)."""
    spec, ev = CANDIDATES[address], evidence.get(address) or {}
    met, why = [], []
    seeded = [r for r in ev.get("early_ties", []) if r["direction"] == "in" and r["counterparty_tier_a"]]
    if seeded:
        senders = sorted({r["counterparty"] for r in seeded})
        met.append("S1")
        why.append(f"S1 funded within a day of its first transaction by labelled {', '.join(senders)}: {len(seeded)} transfer(s), first {seeded[0]['amount']:g} {seeded[0]['symbol']} at {seeded[0]['utc']} UTC, tx {seeded[0]['tx']}")
    cluster = [r for r in ev.get("early_ties", []) if r["counterparty_is_candidate"]]
    if cluster:
        met.append("S3")
        why.append(f"S3 early transfer with another candidate, {cluster[0]['counterparty']} (tx {cluster[0]['tx']})")
    if spec["documented"]:
        met.append("S4")
        why.append("S4 " + spec["documented"])
    return met, why


def build():
    """Write registry.csv from the label snapshot and the probed evidence. Offline once registry_evidence.json exists."""
    evidence = json.loads(EVIDENCE.read_text()) if EVIDENCE.exists() else {}
    known = labels()
    rows = []
    for address, v in sorted(known.items()):
        if address in CANDIDATES:
            continue
        names = sorted({l for _, l, _ in v["labels"]})
        strong = sorted(v["lineages"] & set(STRONG_LINEAGES))
        if any(w in " ".join(names).lower() for w in NOT_SERVICE):
            tier = "X_NOT_SERVICE"
        elif strong:
            tier = "A_LABELLED"
        else:
            tier = "C_SUSPECTED"
        rows.append(dict(address=address, tier=tier, labels=" | ".join(names), lineages="|".join(sorted(v["lineages"])), independent_lineages=len(strong),
                         labelled_chains="|".join(sorted({c for c, _, _ in v["labels"]})), basis="public label snapshot of 2026-11-02"))
    fresh = json.loads(REFRESH.read_text()) if REFRESH.exists() else dict(new_labelled={}, read_utc="")
    for address, found in sorted(fresh["new_labelled"].items()):
        if address not in known and address not in CANDIDATES:                  # named since the snapshot: one lineage, the Blockscout name tag
            tier = "X_NOT_SERVICE" if any(w in " ".join(found["names"]).lower() for w in NOT_SERVICE) else "A_LABELLED"
            rows.append(dict(address=address, tier=tier, labels=" | ".join(found["names"]), lineages="blockscout_name", independent_lineages=1,
                             labelled_chains="|".join(str(c) for c in found["tagged_on"]), basis=f"Blockscout name tag read on {fresh['read_utc'][:10]}"))
    for address in CANDIDATES:
        met, why = criteria(address, evidence)
        tier = "B_STRUCTURAL" if "S1" in met else "C_SUSPECTED"
        v = known.get(address, dict(labels=set(), lineages=set()))
        rows.append(dict(address=address, tier=tier, labels=" | ".join(sorted({l for _, l, _ in v["labels"]})) or "no public label", lineages="|".join(sorted(v["lineages"])),
                         independent_lineages=0, labelled_chains="", basis="; ".join(why) or "behaviour only"))
    with REGISTRY.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["tier"], r["address"])))
    return Counter(r["tier"] for r in rows)


def load():
    """{address: row} of the committed register."""
    with REGISTRY.open() as f:
        return {r["address"]: r for r in csv.DictReader(f)}


def usable(reg):
    """Addresses whose flows may be confirmed: labelled or structurally tied."""
    return {a for a, r in reg.items() if r["tier"] in ("A_LABELLED", "B_STRUCTURAL")}


def roles(transfers, reg):
    """Function of each registry address on one chain over the transfers read, by the rules of the 2026-11-02 plan.
    transfers: rows with src, dst, token, raw. Returns {address: dict(role, sends, recipients, once_share, top_share, receives, senders)}."""
    sends, recv = defaultdict(Counter), defaultdict(Counter)
    native_sends, sweepers = Counter(), set()
    for t in transfers:
        if t["raw"] <= 0:
            continue
        if t["src"] in reg:
            sends[t["src"]][t["dst"]] += 1
            native_sends[t["src"]] += t["token"] == "native"
        if t["dst"] in reg:
            recv[t["dst"]][t["src"]] += 1
            if t["token"] != "native":
                sweepers.add(t["src"])                # an outside address that paid a token into a registered one
    out = {}
    for a in set(sends) | set(recv):
        s, n = sends[a], sum(sends[a].values())
        once = sum(1 for c in s.values() if c == 1)
        top = max(s.values()) / n if n else 0
        if n >= 100 and len(s) >= 50 and once / len(s) >= 0.5:
            # a gas funder pays native coin to addresses that then sweep a token into the service; a payout wallet pays customers
            role = "GAS_FUNDER" if native_sends[a] / n >= 0.9 and len(set(s) & sweepers) * 2 >= len(s) else "PAYOUT_HOT"
        elif n >= 20 and (len(s) <= 20 or top >= 0.5):
            role = "CONSOLIDATION"
        elif n == 0 and sum(recv[a].values()) >= 20:
            role = "COLLECTOR"
        else:
            role = "LOW_ACTIVITY"
        out[a] = dict(role=role, sends=n, recipients=len(s), once_share=round(once / len(s), 3) if s else 0, top_share=round(top, 3),
                      receives=sum(recv[a].values()), senders=len(recv[a]))
    return out
