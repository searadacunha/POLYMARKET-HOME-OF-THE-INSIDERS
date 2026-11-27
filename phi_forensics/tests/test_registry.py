"""Every address the toolkit calls a service or a protocol contract must be traceable to a file of the repository."""
import json
import unittest
from pathlib import Path

from phi_forensics import registry, repository_root

ROOT = repository_root()


class Registry(unittest.TestCase):
    def test_known_addresses(self):
        self.assertEqual(registry.known("0x" + "0" * 40)["kind"], "mint")
        exchange = registry.known("0xE111180000D2663C0091e4f400237545B87B996B")
        self.assertEqual((exchange["kind"], exchange["label"]), ("protocol", "CTF Exchange (2026)"))
        relay = registry.known("0xf70da97812cb96acdf810712aa562db8dfa3dbef")
        self.assertEqual((relay["kind"], relay["service"]), ("labelled_service", "Relay"))
        self.assertIsNone(registry.known("0x" + "ab" * 20))

    def test_the_two_lists_do_not_overlap_and_addresses_are_well_formed(self):
        protocol, services = registry.protocol_contracts(), registry.service_labels()
        self.assertFalse(set(protocol) & set(services))
        for address in list(protocol) + list(services):
            self.assertRegex(address, r"^0x[0-9a-f]{40}$")
        self.assertGreaterEqual(len(protocol), 26)

    @unittest.skipUnless(ROOT, "repository checkout not present")
    def test_every_service_label_is_recorded_in_the_file_it_cites(self):
        for address, entry in registry.service_labels().items():
            source = ROOT / entry["source"]
            self.assertTrue(source.is_file(), entry["source"])
            self.assertIn(address, source.read_text(encoding="utf-8", errors="replace").lower(), f"{address} not in {entry['source']}")

    @unittest.skipUnless(ROOT and (ROOT / registry.SEMANTICS).exists(), "verified contract registry not present")
    def test_the_packaged_copy_equals_the_verified_registry(self):
        packaged = json.loads((registry.DATA / "protocol_contracts.json").read_text(encoding="utf-8"))
        verified = json.loads((ROOT / registry.SEMANTICS).read_text(encoding="utf-8"))
        self.assertEqual(packaged["contracts"], registry._from_semantics(verified))
        self.assertEqual(packaged["source"], registry.SEMANTICS)


if __name__ == "__main__":
    unittest.main()
