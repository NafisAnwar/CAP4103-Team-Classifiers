# Technical Verification

## Documentation-only source revision

All active Python modules, experiment runners, utilities and tests use lowercase inline comments. The historical HW3 and PPA3 sources remain unchanged. Four source files referenced by the accepted model metadata have exact pre-comment bytes archived in `docs/source_history/`. Regression tests compare their SHA-256 values with the original accepted metadata, confirm exact executable AST equivalence and require that the reviewed commented variants match their own separately recorded SHA-256 values. The source guard recognizes only the four documented old-to-new hash pairs; any subsequent byte change is rejected. Original run metadata, manifests, models and score files are not rewritten. A new image-level reproduction generates its own current source provenance and validation blur plan.

## Verification Scope

The integrated implementation was verified on November 16, 2026, using the fixed dataset manifests, accepted baseline, frozen models and saved experiment artifacts.

Verification covered the three research questions, the original PPA3 regression, authentication score alignment, model integrity and repeatability.

## Verification Results

| Verification | Result |
| --- | --- |
| Automated tests | 57 passed, zero skipped |
| Raw palmprint file hashes | 812 verified |
| RQ1 enrollment refitting | Original scores reproduced |
| RQ2 score-level fusion | Original scores reproduced |
| RQ3 facial blur evaluation | All five conditions reproduced |
| Repeated fusion and blur runs | Identical saved scores |
| Sigma-zero equivalence | Within 1e-12 tolerance |
| Palmprint score invariance | Exact agreement |
| Original PPA3 regression | Passed |

The verification establishes reproducibility within the recorded experimental environment. It does not establish statistical significance or production-level authentication performance.

## Verified Experiment Identifiers

| Experiment | Run Identifier |
| --- | --- |
| Accepted RQ1 baseline | `rq1_20261112T151158Z_e192d8` |
| Verified RQ1 reproduction | `rq1_main_verified_20261116` |
| Verified RQ2 | `rq2_main_verified_20261116` |
| Repeated RQ2 | `rq2_main_repeat_20261116` |
| Verified RQ3 | `rq3_main_verified_20261116` |
| Repeated RQ3 | `rq3_main_repeat_20261116` |

## Automated Test Coverage

The test suite verifies:

- Dataset loading and palmprint region extraction.
- Identity mappings and partition integrity.
- Authentication claim alignment and score labels.
- Feature extraction and template matching.
- Frozen-model integrity.
- Validation-only normalization.
- Equal-weight fusion.
- Gaussian blur and original input preservation.
- Sigma-zero equivalence and palmprint score invariance.
- Evaluation metrics and run artifact integrity.
- Original PPA3 regression behavior.

## Single-Command Verification

From the extracted submission root, run the grader-facing verification workflow:

```powershell
.\RUN_PROJECT.cmd verify
```

To independently reproduce all image-level experiments, obtain the original datasets and run `.\RUN_PROJECT.cmd full`. See the top-level README for acquisition and reproduction instructions.

The complete historical study verification workflow, requiring the original raw data and frozen models in the development checkout, is available through:

```powershell
.\.venv\Scripts\python.exe -B scripts/verify_study.py
```

The utility integrates baseline artifact verification, raw palmprint file integrity, automated tests, RQ2 repeatability and the RQ2/RQ3 saved-score audit. Existing experimental results are preserved.

## Reproducing the Verification

Run the automated tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B scripts/verify_legacy.py
```

The following command independently audits the saved RQ2 and RQ3 results:

```powershell
.\.venv\Scripts\python.exe -B scripts/review_submission.py --rq2-run rq2_main_verified_20261116 --rq3-run rq3_main_verified_20261116 --repeat-run rq3_main_repeat_20261116 --output results/metrics/submission_audit
```

Use a new output directory for each audit.

## Verification Evidence

- [Historical integrated verification record](../results/metrics/main_integration_20261116/verification.json)
- [Reproduction comparison](../results/metrics/main_integration_20261116/reproduction_comparison.json)
- [Integration audit](../results/metrics/main_integration_20261116/score_audit/integration_audit.json)
- [Master experimental metrics](../results/metrics/main_integration_20261116/score_audit/study_master_metrics.csv)
- [Verification environment](../results/metrics/main_integration_20261116/environment.json)

Historical run metadata and original verification artifacts are retained to preserve experimental provenance.
