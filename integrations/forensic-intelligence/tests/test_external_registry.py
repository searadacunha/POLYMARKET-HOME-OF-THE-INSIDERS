import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import external_registry as reg


class ExternalRegistryTest(unittest.TestCase):
    def setUp(self):
        self.data = reg.load()

    def test_committed_registry_holds(self):
        self.assertEqual(reg.validate(self.data), [])

    def test_markdown_is_the_rendered_data(self):
        self.assertEqual(reg.DOC.read_text(encoding="utf-8"), reg.render(self.data))

    def test_a_missing_file_or_an_unchecked_integration_is_refused(self):
        bad = copy.deepcopy(self.data)
        s4 = next(e for e in bad["entries"] if e["state"] == "S4_INTEGRATED_VALIDATED")
        s4["our_files"] = ["integrations/forensic-intelligence/no_such_file.py"]
        s4["check"] = "none"
        errors = reg.validate(bad)
        self.assertTrue(any("absent" in e for e in errors))
        self.assertTrue(any("without a passing check" in e for e in errors))

    def test_an_adapted_method_must_name_a_file_of_ours(self):
        bad = copy.deepcopy(self.data)
        s3 = next(e for e in bad["entries"] if e["state"] == "S3_METHOD_ADAPTED")
        s3["our_files"] = []
        self.assertTrue(any("without a file of ours" in e for e in reg.validate(bad)))


if __name__ == "__main__":
    unittest.main()
