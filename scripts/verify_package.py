from pathlib import Path, PurePosixPath
import argparse
import hashlib
import re
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from src.fusion import accepted_scores
from src.evaluation import evaluate_labeled


def run_python(*args):  # run verification subprocesses with the same environment and fail on nonzero exit
    subprocess.run(
        [sys.executable, "-B", *args],
        cwd=root,
        check=True
    )


def verify_package_integrity(project_root=root):  # check the stored byte hash for each submitted file including the launcher
    project_root = Path(project_root).resolve()
    base = project_root.parent
    manifest = project_root / "SHA256SUMS.txt"

    if not manifest.exists():
        raise FileNotFoundError("Package checksum manifest is missing.")

    seen = set()
    required = {"main.py", "RUN_PROJECT.cmd", "README.md", "requirements.txt",
                "project/requirements-lock.txt", "project/scripts/verify_package.py",
                "project/scripts/reproduce_full.py", "project/src/hw3_evaluator.py"}

    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        parts = PurePosixPath(relative).parts
        if (not re.fullmatch(r"[0-9a-f]{64}", expected) or not parts or "\\" in relative
                or ":" in relative or relative != PurePosixPath(relative).as_posix()
                or PurePosixPath(relative).is_absolute() or ".." in parts
                or relative in seen or relative == "project/SHA256SUMS.txt"
                or (relative not in required and parts[0] != "project")):
            raise ValueError(f"Invalid checksum entry: {relative}")
        path = base / relative
        if not path.is_file() or not path.resolve().is_relative_to(base):
            raise ValueError(f"Missing or unsafe package file: {relative}")

        actual = hashlib.sha256(path.read_bytes()).hexdigest()

        if actual != expected:
            raise ValueError(f"Package file changed: {relative}")

        seen.add(relative)

    if not required.issubset(seen):
        raise ValueError("Required package files are absent from the checksum manifest.")
    if (base / "requirements.txt").read_bytes() != (project_root / "requirements-lock.txt").read_bytes():
        raise ValueError("The visible requirements file differs from the pinned project lock.")
    print(f"PASS: {len(seen)} packaged file checksums", flush=True)


def verify_baseline_metrics():  # recalculate baseline metrics directly from accepted raw scores
    _, baseline, _, _, _, tables = accepted_scores(root)
    rows = tables["test"]

    for expected in baseline["test_metrics"]:
        modality = expected["modality"]

        calculated = evaluate_labeled(
            [row[f"{modality}_score_raw"] for row in rows],
            [row["is_genuine"] for row in rows]
        ).metrics()

        for field in ["eer", "auc", "d_prime"]:
            if abs(calculated[field] - expected[field]) > 1e-12:
                raise ValueError(f"RQ1 metric mismatch: {modality}, {field}")

        print(
            f"{modality}: "
            f"EER={calculated['eer'] * 100:.2f}%, "
            f"AUC={calculated['auc']:.4f}, "
            f"d-prime={calculated['d_prime']:.4f}",
            flush=True
        )


def main(repository=False):  # audit submitted evidence and execute the available automated tests
    work = root / "work"
    work.mkdir(exist_ok=True)

    output = Path(tempfile.mkdtemp(prefix="verification_", dir=work))

    print("\nCAP4103 Submission Verification", flush=True)

    if repository:
        if not (root / ".git").exists():
            raise ValueError("Repository mode is restricted to a Git checkout.")
        print("Development checkout: no submission ZIP checksum manifest.", flush=True)
    else:
        verify_package_integrity()  # an extracted submission must always verify its checksum manifest
    verify_baseline_metrics()

    print("\nVerifying RQ2 repeatability", flush=True)

    run_python(
        "scripts/verify_fusion.py",
        "--first", "rq2_main_verified_20261116",
        "--second", "rq2_main_repeat_20261116",
        "--output", str(output / "fusion_verification.json")
    )

    print("\nVerifying all RQ3 conditions", flush=True)

    run_python(
        "scripts/review_submission.py",
        "--rq2-run", "rq2_main_verified_20261116",
        "--rq3-run", "rq3_main_verified_20261116",
        "--repeat-run", "rq3_main_repeat_20261116",
        "--output", str(output / "score_audit")
    )

    print("\nRunning automated tests", flush=True)

    run_python(
        "-m", "unittest", "discover",
        "-s", "tests", "-v"
    )

    print("\nPASS: Submission score verification completed.", flush=True)
    print("Image-level tests require the original biometric assets.")
    print(f"Verification outputs: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", action="store_true", help="Verify a development Git checkout")
    main(parser.parse_args().repository)
