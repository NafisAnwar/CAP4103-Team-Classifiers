# CAP4103 Team Classifiers

Combining face and palmprint scores for authentication under image blur.

## Current results

Nazmus's validation-only normalization, equal-weight fusion and real face-blur
experiments are implemented and executed. The original accepted baseline, models,
seed 42, manifests and PPA3 files are preserved. RQ2 and RQ3 each reproduced exactly
across two runs. RQ3 used restored, hash-matching face/palm models and real Olivetti
face probes; palm scores were reused unchanged from Nafis's verified baseline.

| Face blur sigma | Face EER (%) | Palm EER (%) | Fusion EER (%) |
| --- | ---: | ---: | ---: |
| 0 | 8.95749 | 23.80229 | 7.69231 |
| 0.5 | 8.97436 | 23.80229 | 7.69231 |
| 1 | 9.09244 | 23.80229 | 7.94534 |
| 2 | 10.27328 | 23.80229 | 8.40081 |
| 3 | 11.08300 | 23.80229 | 9.21053 |

Fusion outperformed each unimodal system at all tested levels. Blur still degraded
fusion; it did not eliminate quality sensitivity. Results are descriptive for this
39-user artificially paired study, without confidence intervals or fairness claims.

## Apply this update

Extract `CAP4103_Nazmus_Updates.zip` into the existing repository root, merging
folders and replacing the included changed files. This ZIP includes all Nazmus
updates, measured results and plots; it does not include biometric images/models.
Do not use the earlier standalone `Nazmus_CAP4103.zip` with this repository.

## Run

Use the project virtual environment. On Mac use python3; on Windows the project's
`.venv/Scripts/python.exe` may be used instead. The saved runs record their actual
versions. The original requirements-lock.txt has not been rewritten.

```bash
python3 -B -m unittest discover -s tests -v
python3 -B experiments/rq2_fusion.py
```

For real RQ3, place the actual Olivetti NPZ at `data/raw/face/olivetti.npz` and the
hash-matching face.joblib/palm.joblib at
`data/processed/models/rq1_20261112T151158Z_e192d8/`. In an authorized Git clone,
`git lfs pull` retrieves these files. The GitHub source ZIP may contain pointers.

```bash
python3 -B experiments/rq3_blur.py prepare --output data/processed/my_blur_plan
```

Inspect the generated validation preview before recording your own observations:

```bash
python3 -B experiments/rq3_blur.py review --plan data/processed/my_blur_plan/blur_plan.json --note "Your actual validation-image observations"
python3 -B experiments/rq3_blur.py run --rq2-run rq2_nazmus_final_20261113 --plan data/processed/my_blur_plan/blur_plan.json
```

Use fresh run/plan names. Original and new results are never overwritten. RQ1,
RQ2 and RQ3 each have separate latest pointers. Plan preparation and review use
validation faces only. Models and normalizers stay frozen during the test sweep.

## Results and verification

- Requirements checklist and upload instructions: `docs/nazmus_readiness.md`.
- Report-team methods/results: `docs/nazmus_results.md`.
- RQ2 metrics: `results/metrics/rq2_nazmus_final_20261113/`.
- RQ3 metrics: `results/metrics/rq3_nazmus_review_final/`.
- Figures: matching run directories under `results/figures/`.
- Combined RQ1/RQ2/RQ3 table:
  `results/metrics/nazmus_final_review/score_audit/study_master_metrics.csv`.
- Latest independent review and logs: `results/metrics/nazmus_final_review/`.

A clean base-plus-update integration run passed all 55 tests with zero skips after
restoring actual assets. All 812 palm image byte hashes match the original audit.
An independent raw-data RQ1 rerun selected PCA64/HOG again; palm scores were exact
and maximum face score difference was 6.17e-15. EER/AUC matched exactly. RQ2 and RQ3
were each repeated with exact score agreement. All saved metrics were recomputed.

The original model was saved with scikit-learn 1.9.1; verification used 1.8.0.
The independently refitted face model has different serialization bytes. Original
accepted model hashes remain strict and unchanged; those original models are used
for RQ3. Numerical sigma-zero agreement uses a documented 1e-12 tolerance.
`requirements-nazmus-tested.txt` records the seven tested library versions; it does
not replace the original team requirements/lock. Use the team environment for its
original serialization baseline, or a separate environment for the tested versions:

```bash
python3 -m venv .venv-nazmus
source .venv-nazmus/bin/activate
python3 -m pip install -r requirements-nazmus-tested.txt
```

Keep that environment outside your Git commit. Test logs are specific to the listed
environment; they are not a guarantee of identical results on every platform.

To independently audit saved results without loading biometric image/model files:

```bash
python3 -B scripts/review_submission.py --rq2-run rq2_nazmus_final_20261113 --rq3-run rq3_nazmus_review_final --repeat-run rq3_nazmus_review_repeat --output results/metrics/my_saved_score_audit
```

## Data and limitations

Olivetti Faces is retrieved through scikit-learn; BMPD from the creator's Kaggle
listing. The study uses 39 artificial shared identities, 4/2/4 enrollment/validation/
test samples per modality and 6,084 test claims. Face and palm subjects are different
physical people. Palm crops, session shifts, exact-only deduplication and missing
demographic analysis limit interpretation. Gaussian blur models lost sharpness,
not motion blur. See `docs/methodology.md` for dataset sources and source-use limits.

The group report, presentation, team acceptance and final submission remain separate
responsibilities. No push or submission was performed.
