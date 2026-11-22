import hashlib
from pathlib import Path
import tempfile
import unittest
from scripts.verify_package import verify_package_integrity


class PackageIntegrityTest(unittest.TestCase):  # exercise the outer launcher and nested project checksum contract
    def fixture(self, directory):
        base = Path(directory)
        names = ["main.py", "RUN_PROJECT.cmd", "README.md", "requirements.txt",
                 "project/requirements-lock.txt", "project/scripts/verify_package.py",
                 "project/scripts/reproduce_full.py", "project/src/hw3_evaluator.py"]
        for name in names:
            path = base / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fixture")
        manifest = base / "project/SHA256SUMS.txt"
        manifest.write_text("\n".join(f"{hashlib.sha256((base / name).read_bytes()).hexdigest()}  {name}"
                                       for name in names) + "\n", encoding="utf-8")
        return base, manifest

    def test_nested_package_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            base, _ = self.fixture(directory)
            verify_package_integrity(base / "project")
            (base / "project/work").mkdir()  # generated runtime folders do not invalidate the original submission
            verify_package_integrity(base / "project")

    def test_outer_launcher_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base, _ = self.fixture(directory)
            (base / "RUN_PROJECT.cmd").write_bytes(b"altered")
            with self.assertRaisesRegex(ValueError, "Package file changed"):
                verify_package_integrity(base / "project")

    def test_invalid_or_incomplete_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base, manifest = self.fixture(directory)
            original = manifest.read_text(encoding="utf-8")
            for content in (original + original.splitlines()[0] + "\n",
                            original + "0" * 64 + "  project/../main.py\n",
                            "\n".join(original.splitlines()[1:]) + "\n"):
                with self.subTest(content=content):
                    manifest.write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        verify_package_integrity(base / "project")


if __name__ == "__main__":
    unittest.main()
