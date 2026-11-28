"""Links between trading wallets, each graded by what it actually shows, and the clusters they form.

Four grades, never merged:

  COMMON_CONTROL_DEMONSTRATED      the same key can sign for both wallets (public smart-wallet owner)
  FINANCIAL_RELATION_DEMONSTRATED  money moved between them, or both paid or were paid by one non-service address
  PROBABLE_COORDINATION            a pattern rarer than its measured base rate; no money link shown
  NOT_A_LINK                       a shared service, a common amount or a co-occurrence: reported, never joined

A cluster is a set of wallets joined by links of the first two grades. Even then, one person behind the wallets is
not demonstrated unless the grade is COMMON_CONTROL_DEMONSTRATED: a transfer is a movement of money.

Pure functions over plain rows; nothing here reads a network.
"""
from collections import defaultdict
from itertools import combinations

CONTROL, FINANCIAL, COORDINATION, NOT_A_LINK = ("COMMON_CONTROL_DEMONSTRATED", "FINANCIAL_RELATION_DEMONSTRATED",
                                                "PROBABLE_COORDINATION", "NOT_A_LINK")
JOINING = (CONTROL, FINANCIAL)
RANK = {CONTROL: 0, FINANCIAL: 1, COORDINATION: 2, NOT_A_LINK: 3}
# A payer is a service when it is a contract, a labelled address, a key with a long transaction history, or a key that
# pays many wallets: the thresholds are those of the repository's frozen studies.
SERVICE_KINDS = {"protocol", "labelled_service", "contract", "high_volume_key", "mint"}
MAX_PERSONAL_FANOUT = 10
SHOWN_EVIDENCE = 12


def is_service(address, classes, fanout=None):
    """(True, reason) when an address cannot carry a link between the wallets it touches.

    An address of unknown kind is treated as a service: a link is claimed only on what was established.
    """
    info = classes.get(address)
    if info is None or info.get("kind") in (None, "unknown"):
        return True, "kind not established"
    if info["kind"] in SERVICE_KINDS:
        return True, info.get("label") or info["kind"]
    if fanout is not None and fanout > MAX_PERSONAL_FANOUT:
        return True, f"pays or is paid by {fanout} wallets of the population"
    return False, None


def _ref(row):
    return {"tx": row["tx"], "log_index": row.get("log_index"), "block": row.get("block"), "token": row.get("token"),
            "amount_raw": row.get("amount_raw"), "from": row["from"], "to": row["to"]}


def _link(a, b, kind, grade, evidence, via=None, note=None):
    a, b = sorted((a, b))
    link = {"a": a, "b": b, "type": kind, "grade": grade, "evidence_count": len(evidence), "evidence": evidence[:SHOWN_EVIDENCE]}
    if via:
        link["via"] = via
    if note:
        link["note"] = note
    return link


def links(wallets, transfers, classes, owners=None, population_fanout=None):
    """Graded links among `wallets`.

    transfers: rows {tx, log_index, block, token, amount_raw, from, to} touching the wallets (deposits and withdrawals).
    classes:   {address: {"kind": ..., "label": ...}} for every counterparty that could carry a link.
    owners:    {wallet: [owner keys]} from the smart-wallet contracts, when read.
    population_fanout: {address: number of distinct wallets it pays or is paid by in a wider population}; when absent,
               the fan-out is counted inside `wallets` only, which understates the popularity of a shared address.
    """
    wallets = {w.lower() for w in wallets}
    owners = {w.lower(): sorted({o.lower() for o in keys}) for w, keys in (owners or {}).items()}
    out, seen = [], set()

    by_key = defaultdict(set)
    for wallet, keys in owners.items():
        for key in keys:
            if wallet in wallets:
                by_key[key].add(wallet)
    for key, group in sorted(by_key.items()):
        for a, b in combinations(sorted(group), 2):
            out.append(_link(a, b, "SAME_OWNER_KEY", CONTROL, [], via=key, note="the same key is an owner of both smart wallets"))

    owner_of = {key: wallet for wallet, keys in owners.items() for key in keys if wallet in wallets and len(by_key[key]) == 1}
    paid_by, paid_to, direct = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list)), defaultdict(list)
    for row in transfers:
        identity = (row["tx"], row.get("log_index"))
        if identity in seen:
            continue  # the same log read from both of its ends is one transfer
        seen.add(identity)
        sender, receiver = row["from"].lower(), row["to"].lower()
        a, b = owner_of.get(sender, sender), owner_of.get(receiver, receiver)
        if a in wallets and b in wallets and a != b:
            direct[tuple(sorted((a, b)))].append(_ref(row))
        elif b in wallets:
            paid_by[sender][b].append(_ref(row))
        elif a in wallets:
            paid_to[receiver][a].append(_ref(row))
    for (a, b), evidence in sorted(direct.items()):
        out.append(_link(a, b, "DIRECT_TRANSFER", FINANCIAL, evidence))

    for table, kind in ((paid_by, "COMMON_FUNDER"), (paid_to, "COMMON_DESTINATION")):
        for address, group in sorted(table.items()):
            if len(group) < 2:
                continue
            fanout = max(len(group), (population_fanout or {}).get(address, 0))
            service, reason = is_service(address, classes, fanout)
            for a, b in combinations(sorted(group), 2):
                evidence = group[a][:SHOWN_EVIDENCE // 2] + group[b][:SHOWN_EVIDENCE // 2]
                if service:
                    out.append(_link(a, b, "SHARED_SERVICE", NOT_A_LINK, evidence, via=address,
                                     note=f"shared address is not evidence of a relation: {reason}"))
                else:
                    out.append(_link(a, b, kind, FINANCIAL, evidence, via=address))
    return sorted(out, key=lambda l: (RANK[l["grade"]], l["a"], l["b"], l["type"], l.get("via") or ""))


def clusters(wallets, graded_links, grades=JOINING):
    """Connected groups under the chosen grades. Each cluster carries the weakest grade that holds it together."""
    parent = {w.lower(): w.lower() for w in wallets}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    used = [l for l in graded_links if l["grade"] in grades and l["a"] in parent and l["b"] in parent]
    for link in used:
        parent[find(link["a"])] = find(link["b"])
    groups = defaultdict(list)
    for wallet in parent:
        groups[find(wallet)].append(wallet)
    out = []
    for members in groups.values():
        if len(members) < 2:
            continue
        inside = [l for l in used if l["a"] in members]
        weakest = max((l["grade"] for l in inside), key=RANK.get)
        out.append({"members": sorted(members), "size": len(members), "links": len(inside), "grade": weakest,
                    "types": sorted({l["type"] for l in inside}),
                    "statement": ("One key can sign for every wallet of this group." if weakest == CONTROL and _all_control(members, inside)
                                  else "Money moved between these wallets or through a non-service address they share. "
                                       "That one person controls them is not demonstrated.")})
    return sorted(out, key=lambda c: (-c["size"], c["members"][0]))


def _all_control(members, inside):
    """True when the control links alone connect the whole group."""
    reach, grew = {members[0]}, True
    while grew:
        grew = False
        for link in inside:
            if link["grade"] == CONTROL and (link["a"] in reach) != (link["b"] in reach):
                reach |= {link["a"], link["b"]}
                grew = True
    return len(reach) == len(members)


def partition(wallets, found):
    """{wallet: cluster label} with unclustered wallets alone, the form `stats.pair_confusion` compares."""
    labels = {w.lower(): ("alone", w.lower()) for w in wallets}
    for index, cluster in enumerate(found):
        for member in cluster["members"]:
            labels[member] = ("cluster", index)
    return labels


def mermaid(graded_links, names=None, grades=(CONTROL, FINANCIAL, COORDINATION)):
    """A Mermaid graph of the links: solid for demonstrated relations, dotted for probable coordination."""
    names, lines, nodes = names or {}, ["graph LR"], {}

    def node(address):
        if address not in nodes:
            nodes[address] = f"n{len(nodes)}"
            label = str(names.get(address) or address[:8] + "…" + address[-4:]).replace('"', "'")
            lines.append(f'  {nodes[address]}["{label}"]')
        return nodes[address]

    for link in graded_links:
        if link["grade"] in grades:
            arrow = "-.-" if link["grade"] == COORDINATION else "---"
            lines.append(f'  {node(link["a"])} {arrow}|{link["type"]}| {node(link["b"])}')
    return "\n".join(lines)
