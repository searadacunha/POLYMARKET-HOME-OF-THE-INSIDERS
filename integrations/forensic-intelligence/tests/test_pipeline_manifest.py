import ast
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from pipeline_manifest import render  # noqa: E402

DATA = json.loads((HERE / 'pipeline.json').read_text())


class PipelineManifest(unittest.TestCase):
    def test_eight_stages_with_every_part(self):
        self.assertEqual([s['stage'][0] for s in DATA['stages']], list('12345678'))
        for s in DATA['stages']:
            for key in ('modules', 'entry_points', 'input', 'output', 'tests', 'gap'):
                self.assertTrue(s[key], (s['stage'], key))

    def test_every_path_exists_and_every_function_is_defined_there(self):
        for s in DATA['stages']:
            for t in s['tests']:
                self.assertTrue((REPO / t).is_file(), t)
            for m in s['modules']:
                tree = ast.parse((REPO / m['path']).read_text())   # parsed, never imported
                defined = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                for f in m['functions']:
                    self.assertIn(f, defined, f"{m['path']}:{f}")

    def test_markdown_is_the_rendering_of_the_json(self):
        self.assertEqual((HERE / 'PIPELINE.md').read_text(), render(DATA))


if __name__ == '__main__':
    unittest.main()
