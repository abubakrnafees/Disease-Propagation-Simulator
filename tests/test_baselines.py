import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent


class BaselineTests(unittest.TestCase):
    def test_baseline_snapshots_match_manifest(self):
        folder = ROOT / 'docs/baselines'
        manifest = json.loads((folder / 'manifest.json').read_text())
        for filename, key in [('grade12_main.py.txt', 'original_sha256'),
                              ('pre_refactor_main.py.txt', 'pre_refactor_sha256')]:
            digest = hashlib.sha256((folder / filename).read_bytes()).hexdigest()
            self.assertEqual(digest, manifest[key])

    def test_historical_functions_are_verbatim(self):
        original = (ROOT / 'docs/baselines/grade12_main.py.txt').read_text(encoding='utf-8-sig')
        extracted = (ROOT / 'benchmarks/legacy_collision.py').read_text(encoding='utf-8-sig')
        for name in ('distance', 'collisions'):
            nodes = []
            for source in (original, extracted):
                node = next(node for node in ast.parse(source).body
                            if isinstance(node, ast.FunctionDef) and node.name == name)
                nodes.append(ast.get_source_segment(source, node))
            self.assertEqual(*nodes)
