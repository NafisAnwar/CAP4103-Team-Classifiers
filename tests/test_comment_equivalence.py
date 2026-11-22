import ast
import io
import json
from pathlib import Path
import shutil
import tempfile
import tokenize
import unittest
from src.files import ROOT, COMMENT_ONLY_SOURCE_TRANSITIONS, sha256, source_hash_matches


class CommentEquivalenceTest(unittest.TestCase):  # verify the documentation pass preserves the historical executable implementation
    def test_frozen_source_snapshots_match_accepted_metadata_and_current_ast(self):
        pointer = json.loads((ROOT / 'results/metrics/rq1_accepted.json').read_text())
        metadata = json.loads((ROOT / pointer['metadata']).read_text())
        self.assertEqual(len(COMMENT_ONLY_SOURCE_TRANSITIONS), 4)
        for name, (old, new) in COMMENT_ONLY_SOURCE_TRANSITIONS.items():
            with self.subTest(source=name):
                archived = ROOT / 'docs/source_history' / (Path(name).name + '.txt')
                current = ROOT / name
                self.assertEqual(sha256(archived), metadata['source_sha256'][name])  # retain the exact recorded historical bytes
                self.assertEqual(sha256(archived), old)
                self.assertEqual(sha256(current), new)  # reject even unapproved whitespace changes to a frozen implementation
                self.assertEqual(ast.dump(ast.parse(archived.read_bytes())),
                                 ast.dump(ast.parse(current.read_bytes())))  # comments must not change executable syntax
                self.assertTrue(source_hash_matches(ROOT, name, old))

    def test_unapproved_source_changes_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, (old, new) in COMMENT_ONLY_SOURCE_TRANSITIONS.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, path)
                self.assertTrue(source_hash_matches(root, name, old))
                self.assertTrue(source_hash_matches(root, name, new))  # fresh reproduction records the current exact source hash
                path.write_bytes(path.read_bytes() + b'\n')
                self.assertFalse(source_hash_matches(root, name, old))
                self.assertFalse(source_hash_matches(root, name, new))

    def test_active_python_uses_inline_comments_not_docstrings(self):
        entry = ROOT / 'main.py' if (ROOT / 'main.py').is_file() else ROOT.parent / 'main.py'
        sources = [entry] + [path for folder in ['src', 'experiments', 'scripts', 'tests'] for path in (ROOT / folder).glob('*.py')]
        for path in sources:
            code = path.read_text(encoding='utf-8')
            if not code.strip():
                continue  # the empty package marker contains no executable code to document
            with self.subTest(source=path.name):
                comments = [token for token in tokenize.generate_tokens(io.StringIO(code).readline) if token.type == tokenize.COMMENT]
                self.assertTrue(comments)
                for token in comments:
                    self.assertTrue(token.line[:token.start[1]].strip(), 'standalone comment')
                    self.assertEqual(token.string, token.string.lower(), 'comment must use lowercase')
                for node in ast.walk(ast.parse(code)):
                    if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.assertIsNone(ast.get_docstring(node), 'docstring is not an inline comment')


if __name__ == '__main__':
    unittest.main()
