from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]

package_name = "CAP4103_Team_Classifiers_Code"

runs = [
    "rq1_20261112T151158Z_e192d8",
    "rq1_main_verified_20261116",
    "rq2_main_verified_20261116",
    "rq2_main_repeat_20261116",
    "rq3_main_verified_20261116",
    "rq3_main_repeat_20261116"
]


def include(relative):
    if relative == "scripts/build_submission.py":
        return False

    if relative in [
        "README.md",
        "requirements.txt",
        "requirements-lock.txt",
        "requirements-alternate.txt"
    ]:
        return True

    for prefix in [
        "src/",
        "experiments/",
        "scripts/",
        "tests/",
        "docs/",
        "ppa3_legacy/",
        "data/manifests/"
    ]:
        if relative.startswith(prefix):
            return True

    for run in runs:
        for folder in ["results/metrics", "results/figures"]:
            if relative.startswith(f"{folder}/{run}/"):
                return True

    if relative in [
        "results/metrics/rq1_accepted.json",
        "results/metrics/rq1_latest.json",
        "results/metrics/rq2_latest.json",
        "results/metrics/rq3_latest.json",
        "results/metrics/legacy_regression.json"
    ]:
        return True

    prefix = "results/metrics/main_integration_20261116/"

    if relative.startswith(prefix):
        name = relative[len(prefix):]

        return name in [
            "environment.json",
            "report_clear_metrics.csv",
            "report_blur_metrics.csv",
            "reproduction_comparison.json",
            "rq2_repeatability.json",
            "verification.json",
            "score_audit/integration_audit.json",
            "score_audit/study_master_metrics.csv"
        ]

    return False


def launcher(commands):
    return (
        '@echo off\n'
        'cd /d "%~dp0"\n'
        + commands +
        '\nexit /b %ERRORLEVEL%\n'
    )


def build(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)

    stage = destination / package_name
    stage.mkdir()

    tracked = subprocess.check_output(
        ["git", "ls-files", "-z"],
        cwd=root
    ).decode("utf-8").split("\0")

    count = 0

    for relative in sorted(set(tracked)):
        if not relative or not include(relative):
            continue

        source = root / relative
        target = stage / relative

        with source.open("rb") as stream:
            if stream.read(128).startswith(
                b"version https://git-lfs.github.com/spec/v1"
            ):
                raise ValueError(f"Unresolved LFS pointer: {relative}")

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

        count += 1

    start_here = """CAP4103 FINAL PROJECT
Team: The Classifiers

SUBMISSION INSTRUCTIONS

1. Extract the entire ZIP before running any commands.

2. Install Python 3.13.2 if it is not already available.

3. Double-click SETUP.cmd or execute it from Command Prompt.
   This installs the pinned project dependencies.

4. Run VERIFY_RESULTS.cmd.

   This verifies package integrity, recalculates performance metrics,
   checks RQ2 and RQ3 repeatability, and runs the automated tests.

   The original image-dependent integration tests may be skipped
   because raw biometric images and enrolled templates are not
   redistributed in this submission.

FULL EXPERIMENTAL REPRODUCTION

5. Obtain the original datasets from their authorized sources.

   Olivetti Faces:
   https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_olivetti_faces.html

   Birjand University Mobile Palmprint Database:
   https://www.kaggle.com/datasets/mahdieizadpanah/birjand-university-mobile-palmprint-databasebmpd

   The supplied scripts/download_data.py can obtain the datasets
   when the original services permit access and download.

   Alternatively, place the right-palm JPG files at:

       data/raw/palm/images/

   Place the Olivetti NumPy archive at:

       data/raw/face/olivetti.npz

6. Run REPRODUCE_EXPERIMENTS.cmd.

   This independently trains both authentication models, recalculates
   fusion and performs every facial blur condition using the original
   fixed study protocol. New results are written to work/.

   Original submitted scores and experimental records remain unchanged.

EXPECTED CLEAR-IMAGE RESULTS

Face:       EER 8.96%, AUC 0.9714, d-prime 2.8283
Palmprint:  EER 23.80%, AUC 0.8465, d-prime 1.3925
Fusion:     EER 7.69%, AUC 0.9797, d-prime 2.9294

All five original facial blur conditions are represented in the
included results and verified by the reproduction script.

The README.md provides detailed methodology and repository context.
For this submission ZIP, follow the instructions in this file first.
"""

    (stage / "START_HERE.txt").write_text(start_here, encoding="utf-8")

    (stage / "SETUP.cmd").write_text(
        launcher(
            'py -3.13 -m venv .venv\n'
            'if errorlevel 1 exit /b 1\n'
            '".venv\\Scripts\\python.exe" -m pip install -r requirements-lock.txt\n'
            'if errorlevel 1 exit /b 1\n'
            '".venv\\Scripts\\python.exe" -m pip check\n'
        ),
        encoding="utf-8"
    )

    (stage / "VERIFY_RESULTS.cmd").write_text(
        launcher(
            '".venv\\Scripts\\python.exe" -B scripts\\verify_package.py\n'
        ),
        encoding="utf-8"
    )

    (stage / "DOWNLOAD_DATA.cmd").write_text(
        launcher(
            '".venv\\Scripts\\python.exe" scripts\\download_data.py --modality both\n'
        ),
        encoding="utf-8"
    )

    (stage / "REPRODUCE_EXPERIMENTS.cmd").write_text(
        launcher(
            '".venv\\Scripts\\python.exe" -B scripts\\reproduce_full.py\n'
        ),
        encoding="utf-8"
    )

    readme = stage / "README.md"

    readme.write_text(
        "# Code Submission Package\n\n"
        "Begin with START_HERE.txt for Windows installation, "
        "saved-result verification and independent reproduction.\n\n"
        "Raw biometric images and trained templates are excluded. "
        "The original repository documentation follows for technical context.\n\n"
        + readme.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    files = sorted(path for path in stage.rglob("*") if path.is_file())

    sums = []

    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sums.append(f"{digest}  {path.relative_to(stage).as_posix()}")

    (stage / "SHA256SUMS.txt").write_text(
        "\n".join(sums) + "\n",
        encoding="utf-8"
    )

    zip_path = destination / f"{package_name}.zip"

    with ZipFile(zip_path, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(destination))

    with ZipFile(zip_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity verification failed.")

        for name in archive.namelist():
            if (
                "/data/raw/" in name
                or "/data/processed/models/" in name
                or "/.git/" in name
                or "/.venv/" in name
            ):
                raise ValueError(f"Unexpected packaged file: {name}")

        archive.extractall(destination / "Extraction_Test")

    print(f"Selected repository files: {count}")
    print(f"ZIP size: {zip_path.stat().st_size / 1024**2:.2f} MB")
    print(f"ZIP SHA-256: {hashlib.sha256(zip_path.read_bytes()).hexdigest()}")
    print(f"ZIP: {zip_path}")
    print("PASS: ZIP built and extracted successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    build(parser.parse_args().destination)
