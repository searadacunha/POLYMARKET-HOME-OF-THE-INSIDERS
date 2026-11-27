"""Graded links and clusters on small hand-built cases, including the traps recorded in this repository."""
import unittest

from phi_forensics import cluster, stats

W = {name: "0x" + f"{i:040x}" for i, name in enumerate(("a", "b", "c", "d", "e", "f"), start=1)}
KEY, HOT, PERSON, DEST, UNKNOWN = ("0x" + c * 40 for c in "1789f")
CLASSES = {KEY: {"kind": "key"}, PERSON: {"kind": "key"}, DEST: {"kind": "key"},
           HOT: {"kind": "labelled_service", "label": "exchange hot wallet"}}


def move(n, sender, receiver, amount=1_000_000):
    return {"tx": "0x" + f"{n:064x}", "log_index": n, "block": 100 + n, "token": "0xusdc", "amount_raw": amount, "from": sender, "to": receiver}


def grades(found):
    return [(l["a"], l["b"], l["type"], l["grade"]) for l in found]


class Links(unittest.TestCase):
    def test_a_direct_transfer_is_a_demonstrated_financial_relation(self):
        found = cluster.links(W.values(), [move(1, W["a"], W["b"], 5_530_000)], CLASSES)
        self.assertEqual(grades(found), [(W["a"], W["b"], "DIRECT_TRANSFER", cluster.FINANCIAL)])
        self.assertEqual(found[0]["evidence"][0]["amount_raw"], 5_530_000)
        self.assertEqual(found[0]["evidence_count"], 1)

    def test_a_personal_address_paying_two_wallets_links_them(self):
        found = cluster.links(W.values(), [move(1, PERSON, W["a"]), move(2, PERSON, W["b"])], CLASSES)
        self.assertEqual(grades(found), [(W["a"], W["b"], "COMMON_FUNDER", cluster.FINANCIAL)])
        self.assertEqual(found[0]["via"], PERSON)

    def test_a_shared_exchange_wallet_is_reported_and_is_not_a_link(self):
        found = cluster.links(W.values(), [move(1, HOT, W["a"]), move(2, HOT, W["b"])], CLASSES)
        self.assertEqual(grades(found), [(W["a"], W["b"], "SHARED_SERVICE", cluster.NOT_A_LINK)])
        self.assertIn("exchange hot wallet", found[0]["note"])
        self.assertEqual(cluster.clusters(W.values(), found), [])

    def test_an_address_of_unknown_kind_never_carries_a_link(self):
        for classes in (CLASSES, {**CLASSES, UNKNOWN: {"kind": "unknown"}}, {**CLASSES, UNKNOWN: {}}):
            found = cluster.links(W.values(), [move(1, UNKNOWN, W["a"]), move(2, UNKNOWN, W["b"])], classes)
            self.assertEqual([l["grade"] for l in found], [cluster.NOT_A_LINK])
            self.assertIn("kind not established", found[0]["note"])

    def test_every_service_kind_is_refused(self):
        for kind in ("protocol", "contract", "high_volume_key", "mint", "labelled_service"):
            found = cluster.links(W.values(), [move(1, PERSON, W["a"]), move(2, PERSON, W["b"])], {PERSON: {"kind": kind}})
            self.assertEqual([l["grade"] for l in found], [cluster.NOT_A_LINK], kind)

    def test_a_key_that_pays_many_wallets_is_a_service_by_behaviour(self):
        many = {f"w{i}": "0x" + f"{i + 100:040x}" for i in range(11)}
        found = cluster.links(many.values(), [move(i, PERSON, w) for i, w in enumerate(many.values())], CLASSES)
        self.assertEqual({l["grade"] for l in found}, {cluster.NOT_A_LINK})
        self.assertEqual(len(found), 55)
        ten = list(many.values())[:10]
        found = cluster.links(ten, [move(i, PERSON, w) for i, w in enumerate(ten)], CLASSES)
        self.assertEqual({l["grade"] for l in found}, {cluster.FINANCIAL})

    def test_popularity_measured_on_a_wider_population_overrides_the_local_count(self):
        rows = [move(1, PERSON, W["a"]), move(2, PERSON, W["b"])]
        self.assertEqual(cluster.links(W.values(), rows, CLASSES, population_fanout={PERSON: 2})[0]["grade"], cluster.FINANCIAL)
        popular = cluster.links(W.values(), rows, CLASSES, population_fanout={PERSON: 574})[0]
        self.assertEqual(popular["grade"], cluster.NOT_A_LINK)
        self.assertIn("574", popular["note"])

    def test_a_shared_destination_links_and_a_shared_service_destination_does_not(self):
        found = cluster.links(W.values(), [move(1, W["a"], DEST), move(2, W["b"], DEST), move(3, W["c"], HOT), move(4, W["d"], HOT)], CLASSES)
        self.assertEqual(grades(found), [(W["a"], W["b"], "COMMON_DESTINATION", cluster.FINANCIAL),
                                         (W["c"], W["d"], "SHARED_SERVICE", cluster.NOT_A_LINK)])

    def test_the_same_owner_key_is_common_control(self):
        found = cluster.links(W.values(), [], CLASSES, owners={W["a"]: [KEY.upper().replace("0X", "0x")], W["b"]: [KEY], W["c"]: [PERSON]})
        self.assertEqual(grades(found), [(W["a"], W["b"], "SAME_OWNER_KEY", cluster.CONTROL)])
        self.assertEqual(found[0]["via"], KEY)

    def test_a_transfer_between_owner_keys_is_a_transfer_between_their_wallets(self):
        found = cluster.links(W.values(), [move(1, KEY, PERSON)], CLASSES, owners={W["a"]: [KEY], W["b"]: [PERSON]})
        self.assertEqual(grades(found), [(W["a"], W["b"], "DIRECT_TRANSFER", cluster.FINANCIAL)])
        self.assertEqual((found[0]["evidence"][0]["from"], found[0]["evidence"][0]["to"]), (KEY, PERSON))

    def test_a_log_read_from_both_ends_counts_once(self):
        row = move(1, W["a"], W["b"])
        self.assertEqual(cluster.links(W.values(), [row, dict(row)], CLASSES)[0]["evidence_count"], 1)

    def test_a_wallet_paying_itself_or_a_stranger_creates_nothing(self):
        self.assertEqual(cluster.links(W.values(), [move(1, W["a"], W["a"]), move(2, PERSON, W["a"]), move(3, W["a"], DEST)], CLASSES), [])

    def test_order_is_stable_and_addresses_are_normalised(self):
        rows = [move(2, PERSON, W["b"].upper().replace("0X", "0x")), move(1, PERSON, W["a"]), move(3, W["c"], W["a"])]
        first = cluster.links(W.values(), rows, CLASSES)
        self.assertEqual(first, cluster.links(list(W.values())[::-1], rows[::-1], CLASSES))
        self.assertEqual([l["type"] for l in first], ["COMMON_FUNDER", "DIRECT_TRANSFER"])


class Clusters(unittest.TestCase):
    def test_links_chain_into_one_group_and_a_service_joins_nobody(self):
        rows = [move(1, W["a"], W["b"]), move(2, PERSON, W["b"]), move(3, PERSON, W["c"]), move(4, HOT, W["c"]), move(5, HOT, W["d"])]
        found = cluster.clusters(W.values(), cluster.links(W.values(), rows, CLASSES))
        self.assertEqual(len(found), 1)
        self.assertEqual((found[0]["members"], found[0]["grade"], found[0]["types"]),
                         (sorted([W["a"], W["b"], W["c"]]), cluster.FINANCIAL, ["COMMON_FUNDER", "DIRECT_TRANSFER"]))
        self.assertIn("not demonstrated", found[0]["statement"])

    def test_only_a_group_held_by_one_key_is_stated_as_common_control(self):
        owners = {W["a"]: [KEY], W["b"]: [KEY], W["c"]: [KEY]}
        held = cluster.clusters(W.values(), cluster.links(W.values(), [], CLASSES, owners=owners))
        self.assertEqual((held[0]["grade"], held[0]["size"]), (cluster.CONTROL, 3))
        self.assertIn("One key can sign", held[0]["statement"])
        mixed = cluster.clusters(W.values(), cluster.links(W.values(), [move(1, W["c"], W["d"])], CLASSES, owners={W["a"]: [KEY], W["b"]: [KEY]}))
        self.assertEqual([c["grade"] for c in mixed], [cluster.CONTROL, cluster.FINANCIAL])
        joined = cluster.clusters(W.values(), cluster.links(W.values(), [move(1, W["b"], W["c"])], CLASSES, owners={W["a"]: [KEY], W["b"]: [KEY]}))
        self.assertEqual((joined[0]["size"], joined[0]["grade"]), (3, cluster.FINANCIAL))
        self.assertIn("not demonstrated", joined[0]["statement"])

    def test_weaker_grades_join_only_on_request(self):
        guess = [{"a": W["a"], "b": W["b"], "type": "SYNCHRONISED_TRADING", "grade": cluster.COORDINATION, "evidence": [], "evidence_count": 0}]
        self.assertEqual(cluster.clusters(W.values(), guess), [])
        asked = cluster.clusters(W.values(), guess, grades=(cluster.CONTROL, cluster.FINANCIAL, cluster.COORDINATION))
        self.assertEqual((asked[0]["size"], asked[0]["grade"]), (2, cluster.COORDINATION))

    def test_the_partition_feeds_the_agreement_measure(self):
        rows = [move(1, W["a"], W["b"]), move(2, W["c"], W["d"]), move(3, HOT, W["e"]), move(4, HOT, W["f"])]
        found = cluster.clusters(W.values(), cluster.links(W.values(), rows, CLASSES))
        truth = {W["a"]: 1, W["b"]: 1, W["c"]: 2, W["d"]: 2, W["e"]: 3, W["f"]: 4}
        score = stats.pair_confusion(truth, cluster.partition(W.values(), found))
        self.assertEqual((score["precision"], score["recall"], score["adjusted_rand_index"]), (1.0, 1.0, 1.0))
        naive = stats.pair_confusion(truth, {**cluster.partition(W.values(), found), W["e"]: "hot", W["f"]: "hot"})
        self.assertLess(naive["precision"], 1.0)

    def test_the_graph_text_names_wallets_and_never_breaks_on_quotes(self):
        found = cluster.links(W.values(), [move(1, W["a"], W["b"]), move(2, HOT, W["c"]), move(3, HOT, W["d"])], CLASSES)
        text = cluster.mermaid(found, names={W["a"]: 'trader "one"'})
        self.assertEqual(text.splitlines()[0], "graph LR")
        self.assertIn("trader 'one'", text)
        self.assertIn("---|DIRECT_TRANSFER|", text)
        self.assertNotIn("SHARED_SERVICE", text)
        self.assertEqual(text.count("["), 2)


if __name__ == "__main__":
    unittest.main()
