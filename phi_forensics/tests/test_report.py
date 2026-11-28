"""The Markdown report of a wallet, built from the real overview of tests/world.py: what it states and what it cannot be made to say."""
import json
import re
import unittest

from phi_forensics import investigate, report
from phi_forensics.tests import world
from phi_forensics.tests.world import F, K, V, W, tx

NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")
UNESCAPED_PIPE, UNESCAPED_TICK = re.compile(r"(?<!\\)\|"), re.compile(r"(?<!\\)`")


def leaves(value):
    """Every scalar of the overview as text, and every number written inside its texts."""
    if isinstance(value, dict):
        return set().union(*map(leaves, value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*map(leaves, value)) if value else set()
    text = value if isinstance(value, str) else json.dumps(value)
    return {text, *NUMBER.findall(text)}


class Report(unittest.TestCase):
    def setUp(self):
        self.world = world.World()
        world.offline(self, self.world)

    def render(self, wallet):
        overview = investigate.wallet_overview(self.world.sources(), wallet)
        return overview, report.wallet_markdown(overview)

    def table(self, markdown):
        lines = markdown.split("\n")
        start = lines.index("| Market | Result | Cash | State | Flags |")
        return lines[start + 2:lines.index("", start)]

    def test_a_complete_wallet(self):
        # V: 2 rows on C1, net 75 (cash 75, nothing left); 200 from F and 50 from the Relay solver, 150 to D; first deposit tx 4,
        # block 88 050 000, 2 200 000 seconds before the first trade (block 89 150 000).
        _, text = self.render(V)
        self.assertTrue(text.startswith(f"# Wallet report: `{V}`\n"))
        for line in ("- Public profile: none found.",
                     "- Smart-wallet owner keys: not a Safe that lists its owners, or none read.",
                     "- Trading history: 2 rows over 1 markets, first trade 2026-05-09T04:13:20Z.",
                     "- Net trading result: **75.000000** (cash 75.000000, remaining inventory 0.000000; realised 75.000000, unrealised 0.000000).",
                     f"- Deposits: 2 transfers, 250.000000 of token `{world.USDC_E}`.",
                     f"- Withdrawals: 1 transfers, 150.000000 of token `{world.USDC_E}`.",
                     "- Deposits by kind of sender: key 200.000000, labelled_service 50.000000.",
                     f"- First deposit: 200.000000 from `{F}` (key), transaction `{tx(4)}`, log 0, block 88050000; "
                     "first trade 2200000 seconds later.",
                     "| Market one resolved Yes | 75.000000 | 75.000000 | FLAT |  |",
                     f"python3 -m phi_forensics verify_transfer --transaction {tx(4)} --recipient {V} --log_index 0"):
            self.assertIn(line + "\n", text)
        self.assertNotIn("not stated", text)

    def test_a_wallet_whose_net_result_cannot_be_stated(self):
        # W: the market of the converted shares (C3) is not valued, so only the cash 42.5 is given.
        _, text = self.render(W)
        self.assertIn("- Trading cash: **42.500000**. The net result is not stated: 1 markets hold an inventory that could not be valued.\n", text)
        self.assertNotIn("Net trading result", text)
        self.assertIn(f"- Smart-wallet owner keys: `{K}`.\n", text)
        self.assertIn("- Public profile: name `tester-one`, created 2026-04-10T09:00:00Z.\n", text)
        self.assertEqual(self.table(text), [
            "| Market one resolved Yes | 140.000000 | 140.000000 | FLAT | API_AMOUNTS_MAY_BE_GROSS_OF_FEES |",
            "| Event outcome A | not valued | -30.000000 | INVENTORY_NOT_VALUED | IN_A_CONVERTED_NEG_RISK_EVENT |",
            "| Market two still open | 15.000000 | -67.500000 | INVENTORY_VALUED | API_AMOUNTS_MAY_BE_GROSS_OF_FEES |",
            "| Event of A and B | 0.000000 | 0.000000 | FLAT | CONVERSION_INVENTORY_NOT_RECONSTRUCTED |"])
        self.assertIn("- This wallet converted neg-risk shares", text)

    def test_no_figure_appears_that_is_not_in_the_overview(self):
        for wallet in (V, W):
            overview, text = self.render(wallet)
            known = leaves(overview)
            body = text.replace(f"phi-forensics {report.__version__}", "phi-forensics")
            for number in NUMBER.findall(body):
                self.assertIn(number, known, f"{number} in the report of {wallet}")
            for amount in re.findall(r"-?\d+\.\d{6}\b", body):
                self.assertIn(amount, known)

    def test_a_pipe_or_a_newline_in_a_title_cannot_break_the_table(self):
        self.world.row(W, 14)["title"] = "Evil | cell\n| injected | row |"
        _, text = self.render(W)
        rows = self.table(text)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(len(UNESCAPED_PIPE.findall(row)) == 6 for row in rows), rows)
        self.assertIn("| Evil \\| cell \\| injected \\| row \\| | not valued |", text)

    def test_a_carriage_return_in_a_title_cannot_break_the_table(self):
        self.world.row(W, 14)["title"] = "Evil\r| injected | row |"
        _, text = self.render(W)
        self.assertNotIn("\r", text)

    def test_markdown_in_a_title_is_not_rendered(self):
        self.world.row(W, 14)["title"] = "[open](https://evil.example) **now** <img src=x>"
        _, text = self.render(W)
        row = next(r for r in self.table(text) if "not valued" in r)
        for raw in ("[open](", "**now**", "<img"):
            self.assertNotRegex(row, r"(?<!\\)" + re.escape(raw))

    def test_a_backtick_in_a_public_name_cannot_leave_its_code_span(self):
        self.world.profiles[W]["name"] = "x` **loud** `y"
        _, text = self.render(W)
        line = next(l for l in text.split("\n") if l.startswith("- Public profile"))
        spans = UNESCAPED_TICK.split(line)
        self.assertEqual(len(spans) % 2, 1, line)
        self.assertFalse(any("**loud**" in outside for outside in spans[::2]), line)

    def test_a_creation_date_from_the_api_cannot_add_lines(self):
        self.world.profiles[W]["createdAt"] = "2026-04-10\n## Injected heading"
        _, text = self.render(W)
        self.assertNotIn("\n## Injected heading", text)


if __name__ == "__main__":
    unittest.main()
