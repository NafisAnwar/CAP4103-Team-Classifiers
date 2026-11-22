from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from src.fusion import accepted_scores
from src.evaluation import evaluate_labeled


def run_python(*args):
    subprocess.run(
        [sys.executable, "-B", *args],
        cwd=root,
        check=True
    )


def verify_package_integrity():
    manifest = root / "SHA256SUMS.txt"

    if not manifest.exists():
        raise FileNotFoundError("Package checksum manifest is missing.")

    count = 0

    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = root / relative

        actual = hashlib.sha256(path.read_bytes()).hexdigest()

        if actual != expected:
            raise ValueError(f"Package file changed: {relative}")

        count += 1

    print(f"PASS: {count} packaged file checksums", flush=True)


def verify_baseline_metrics():
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


def main():
    work = root / "work"
    work.mkdir(exist_ok=True)

    output = Path(tempfile.mkdtemp(prefix="verification_", dir=work))

    print("\nCAP4103 Submission Verification", flush=True)

    verify_package_integrity()
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
    main()
