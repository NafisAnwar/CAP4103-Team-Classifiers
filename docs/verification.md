# Technical Verification

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

- [Automated test results](../results/metrics/main_integration_20261116/tests.txt)
- [Reproduction comparison](../results/metrics/main_integration_20261116/reproduction_comparison.json)
- [Integration audit](../results/metrics/main_integration_20261116/score_audit/integration_audit.json)
- [Master experimental metrics](../results/metrics/main_integration_20261116/score_audit/study_master_metrics.csv)
- [Verification environment](../results/metrics/main_integration_20261116/environment.json)

Historical run metadata and original verification artifacts are retained to preserve experimental provenance.
