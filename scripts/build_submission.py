from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
package_name = "CAP4103_Team_Classifiers_Code"
root_files = {"RUN_PROJECT.cmd": "RUN_PROJECT.cmd", "main.py": "main.py",
              "README.md": "README.md", "requirements.txt": "requirements-lock.txt"}
runs = ["rq1_20261112T151158Z_e192d8", "rq1_main_verified_20261116",
        "rq2_main_verified_20261116", "rq2_main_repeat_20261116",
        "rq3_main_verified_20261116", "rq3_main_repeat_20261116"]


def include(relative):  # select only implementation, protocol and accepted experimental evidence
    if relative == "scripts/build_submission.py":
        return False  # the grader does not need the git-dependent distribution builder
    if relative in {"requirements.txt", "requirements-lock.txt"}:
        return True
    if relative.startswith(("src/", "experiments/", "scripts/", "tests/", "docs/",
                            "ppa3_legacy/", "data/manifests/")):
        return True
    if any(relative.startswith(f"{folder}/{run}/") for run in runs
           for folder in ("results/metrics", "results/figures")):
        return True
    if relative in {"results/metrics/rq1_accepted.json", "results/metrics/rq1_latest.json",
                    "results/metrics/rq2_latest.json", "results/metrics/rq3_latest.json",
                    "results/metrics/legacy_regression.json"}:
        return True
    prefix = "results/metrics/main_integration_20261116/"
    return relative.startswith(prefix) and relative[len(prefix):] in {
        "environment.json", "report_clear_metrics.csv", "report_blur_metrics.csv",
        "reproduction_comparison.json", "rq2_repeatability.json", "verification.json",
        "score_audit/integration_audit.json", "score_audit/study_master_metrics.csv"}


def copy_selected(source, target):  # reject unresolved large-file pointers and symbolic links
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"Invalid submission source: {source}")
    with source.open("rb") as stream:
        if stream.read(128).startswith(b"version https://git-lfs.github.com/spec/v1"):
            raise ValueError(f"Unresolved LFS pointer: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def build(destination):  # assemble a five-entry distribution without altering the repository
    tracked = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode("utf-8").split("\0"))
    changes = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=root)
    if changes.strip():
        raise ValueError("Commit the reviewed source changes before building the submission.")
    if not set(root_files.values()).issubset(tracked):
        raise ValueError("A required top-level submission source is not tracked.")
    destination = Path(destination).resolve()
    if destination == root or root in destination.parents:
        raise ValueError("Choose a destination outside the repository.")
    destination.mkdir(parents=True, exist_ok=False)
    stage = destination / package_name
    project = stage / "project"
    for target, source in root_files.items():
        copy_selected(root / source, stage / target)
    for relative in sorted(tracked):
        if include(relative):
            copy_selected(root / relative, project / relative)

    required = {"scripts/reproduce_full.py", "scripts/verify_package.py", "src/hw3_evaluator.py",
                "data/manifests/protocol_lock.json", "docs/hw3_original.py.txt", "requirements-lock.txt",
                "results/metrics/main_integration_20261116/report_clear_metrics.csv",
                "results/metrics/main_integration_20261116/report_blur_metrics.csv"}
    if any(not (project / name).is_file() for name in required):
        raise ValueError("Required implementation or evidence is missing.")
    if {path.name for path in stage.iterdir()} != set(root_files) | {"project"}:
        raise ValueError("Unexpected top-level submission layout.")
    files = sorted(path for path in stage.rglob("*") if path.is_file())
    sums = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(stage).as_posix()}"
            for path in files]  # cover the launcher and all project files relative to the outer root
    (project / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    zip_path = destination / f"{package_name}.zip"
    with ZipFile(zip_path, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(destination))

    extraction = destination / "Extraction_Test"
    with ZipFile(zip_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity verification failed.")
        for name in archive.namelist():
            if any(fragment in name for fragment in ("/data/raw/", "/data/processed/", "/.git/", "/.venv/", "/__pycache__/")):
                raise ValueError(f"Unexpected packaged file: {name}")
        archive.extractall(extraction)
    extracted = extraction / package_name
    if {path.name for path in extracted.iterdir()} != set(root_files) | {"project"}:
        raise ValueError("Extracted ZIP layout differs from the submission layout.")
    for path in files:
        if (extracted / path.relative_to(stage)).read_bytes() != path.read_bytes():
            raise ValueError(f"Extracted file differs: {path.name}")
    print(f"Packaged files: {len(files) + 1}")
    print(f"ZIP size: {zip_path.stat().st_size / 1024**2:.2f} MB")
    print(f"ZIP SHA-256: {hashlib.sha256(zip_path.read_bytes()).hexdigest()}")
    print(f"ZIP: {zip_path}")
    print("PASS: Five-entry ZIP built and independently extracted successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    build(parser.parse_args().destination)
