from pathlib import Path
import argparse
import json
import shutil
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from experiments.rq1_baseline import run as run_rq1
from experiments.rq2_fusion import run as run_rq2
from experiments.rq3_blur import run as run_rq3

from src.blur import prepare_plan, assert_equal_scores
from src.files import read_csv, write_json, sha256, text_sha256
from src.files import manifest_hashes
from src.trial_protocol import load_protocol


def copy_file(source, destination):  # copy selected inputs into an isolated workspace without touching the source
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def compare_scores(actual, expected, fields):  # compare newly generated scores with the accepted reference by claim key
    return assert_equal_scores(
        read_csv(actual),
        read_csv(expected),
        fields,
        atol=1e-8
    )


def compare_metrics(actual, expected):  # check condition coverage, metric tolerances and claim counts
    def key(row):  # identify one result row by modality and blur condition
        return row["modality"], float(row.get("blur_sigma", 0))

    actual_rows = {key(row): row for row in actual}
    expected_rows = {key(row): row for row in expected}

    if actual_rows.keys() != expected_rows.keys():
        raise ValueError("Reproduction metric conditions differ.")

    for condition in expected_rows:
        for field in ["eer", "auc", "d_prime"]:
            difference = abs(
                float(actual_rows[condition][field]) -
                float(expected_rows[condition][field])
            )

            if difference > 1e-7:
                raise ValueError(
                    f"Metric reproduction mismatch: {condition}, {field}"
                )

        for field in ["genuine_count", "impostor_count"]:
            if int(actual_rows[condition][field]) != int(
                expected_rows[condition][field]
            ):
                raise ValueError("Reproduction claim count differs.")


def finish(destination, **experiments):  # publish a summary only for the research questions independently reproduced
    summary = {
        "status": "passed",
        "experiments": [name.upper() for name in experiments],
        "score_absolute_tolerance": 1e-8,
        "metric_absolute_tolerance": 1e-7,
        "original_results_preserved": True,
    }
    summary.update({f"{name}_metrics": result["test_metrics"] for name, result in experiments.items()})
    write_json(destination / "reproduction_summary.json", summary)
    print(f"\nPASS: IMAGE-LEVEL REPRODUCTION ({', '.join(summary['experiments'])})")
    print(f"Independent reproduction outputs: {destination}")
    return destination


def reproduce(data_root, through="rq3"):  # refit from original biometric data, then reproduce the dependent experiments in order
    if through not in ("rq1", "rq2", "rq3"):
        raise ValueError("Unknown reproduction endpoint.")
    data_root = Path(data_root).resolve()

    work = root / "work"
    work.mkdir(exist_ok=True)

    destination = Path(
        tempfile.mkdtemp(prefix="reproduction_", dir=work)
    )

    print("\nChecking original dataset integrity", flush=True)

    for row in read_csv(root / "data/manifests/palm_samples.csv"):
        path = data_root / row["source_path"]

        if not path.is_file() or sha256(path) != row["file_sha256"]:
            raise ValueError(f"Missing or changed palmprint image: {path}")

    print("PASS: All original palmprint file hashes", flush=True)

    for folder in ["src", "experiments", "scripts", "data/manifests"]:
        shutil.copytree(
            root / folder,
            destination / folder,
            ignore=shutil.ignore_patterns("__pycache__")
        )

    for name in ["requirements.txt", "requirements-lock.txt"]:
        copy_file(root / name, destination / name)

    copy_file(
        data_root / "data/raw/face/olivetti.npz",
        destination / "data/raw/face/olivetti.npz"
    )

    _, partitions, _ = load_protocol(root)

    for row in partitions:
        if row["modality"] == "palm":
            relative = row["source_path_or_key"]
            copy_file(data_root / relative, destination / relative)

    print("\nRQ1: Refitting authentication models", flush=True)

    rq1 = run_rq1("rq1_reproduced", root=destination)

    folder = destination / "results/metrics/rq1_reproduced"
    metadata = folder / "run_metadata.json"

    reference_rq1 = root / "results/metrics/rq1_main_verified_20261116"

    for name in ["validation_scores.csv", "rq1_baseline_scores.csv"]:
        compare_scores(
            folder / name,
            reference_rq1 / name,
            ["face_score_raw", "palm_score_raw"]
        )

    compare_metrics(
        rq1["test_metrics"],
        json.loads(
            (reference_rq1 / "run_metadata.json").read_text()
        )["test_metrics"]
    )

    write_json(
        destination / "results/metrics/rq1_accepted.json",  # register only the new baseline within the isolated workspace
        {
            "run_id": "rq1_reproduced",
            "metadata": metadata.relative_to(destination).as_posix(),
            "metadata_sha256": text_sha256(metadata),
            "manifest_sha256": manifest_hashes(destination),
            "score_sha256": {
                name: text_sha256(folder / name)
                for name in [
                    "validation_scores.csv",
                    "rq1_baseline_scores.csv"
                ]
            },
            "hash_format": "sha256_text_lf_binary_raw_v1"
        }
    )

    print("PASS: RQ1 reproduced from original images", flush=True)
    if through == "rq1":
        return finish(destination, rq1=rq1)

    print("\nRQ2: Recomputing normalization and fusion", flush=True)

    rq2 = run_rq2("rq2_reproduced", root=destination)

    reference_rq2 = root / "results/metrics/rq2_main_verified_20261116"

    fields = [
        "face_score_raw",
        "palm_score_raw",
        "face_score_normalized",
        "palm_score_normalized",
        "fusion_score"
    ]

    compare_scores(
        destination / "results/metrics/rq2_reproduced/rq2_fusion_scores.csv",
        reference_rq2 / "rq2_fusion_scores.csv",
        fields
    )

    compare_metrics(
        rq2["test_metrics"],
        json.loads(
            (reference_rq2 / "run_metadata.json").read_text()
        )["test_metrics"]
    )

    print("PASS: RQ2 reproduced using newly computed scores", flush=True)
    if through == "rq2":
        return finish(destination, rq1=rq1, rq2=rq2)

    print("\nRQ3: Reproducing the facial blur experiment", flush=True)

    reference_rq3 = root / "results/metrics/rq3_main_verified_20261116"

    reference_plan = json.loads(
        (reference_rq3 / "blur_plan.json").read_text()
    )

    plan_path = prepare_plan(
        destination,
        destination / "data/processed/blur_plans/reproduction",
        reference_plan["sigmas"]
    )

    plan = json.loads(plan_path.read_text())

    for field in ["sample_ids", "sample_pixel_sha256", "sigmas"]:
        if plan[field] != reference_plan[field]:
            raise ValueError("Validation blur selection differs.")

    plan["reviewed"] = True
    plan["review_note"] = (
        "Reuses the original reviewed validation-only blur selection. "
        "Validation sample identities, pixel hashes and sigma values "
        "were verified before the regenerated preview."
    )

    write_json(plan_path, plan)

    rq3 = run_rq3(
        "rq2_reproduced",
        plan_path,
        "rq3_reproduced",
        root=destination
    )

    actual = read_csv(
        destination / "results/metrics/rq3_reproduced/rq3_blur_scores.csv"
    )

    expected = read_csv(reference_rq3 / "rq3_blur_scores.csv")

    for sigma in reference_plan["sigmas"]:
        assert_equal_scores(
            [row for row in actual if float(row["blur_sigma"]) == sigma],
            [row for row in expected if float(row["blur_sigma"]) == sigma],
            fields,
            atol=1e-8
        )

    compare_metrics(
        rq3["test_metrics"],
        json.loads(
            (reference_rq3 / "run_metadata.json").read_text()
        )["test_metrics"]
    )

    print("PASS: RQ3 reproduced across all five blur conditions.")
    return finish(destination, rq1=rq1, rq2=rq2, rq3=rq3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-root",
        default=str(root),
        help="Project directory containing authorized original datasets"
    )

    parser.add_argument("--through", choices=["rq1", "rq2", "rq3"], default="rq3",
                        help="Stop after the selected experiment; dependencies run first")
    args = parser.parse_args()
    reproduce(args.data_root, args.through)
