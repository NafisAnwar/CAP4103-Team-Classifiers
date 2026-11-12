# CAP4103 Nafis checkpoint and continuation handoff

Updated: 2026-11-12T15:14:13.645587+00:00

## Location and scope

Project: `C:\Users\anwar\Desktop\CAP4103 - Mobile Biometrics\CAP4103 - Course Project\CAP4103-Biometric-Fusion`
Workspace: `C:\Users\anwar\Desktop\CAP4103 - Mobile Biometrics\CAP4103 - Course Project\CAP4103-Biometric-Fusion\CAP4103-Biometric-Fusion.code-workspace`
Working editor: VS Code. Local branch: nafis-foundation.
Cleanup commit: d442448. Implemented source commit: 70ecc9f813ccc43809eb4d9255809fe42c096e04.
This document and the final verification exports are saved in a subsequent checkpoint commit; run `git rev-parse HEAD` for that complete repository snapshot. The final Desktop copy includes the exact checkpoint commit after it is created.

User request: remove every project README/.gitkeep and redundant setup scaffolding before coding; implement Nafis's portion; save this Desktop checkpoint before usage falls to 1% remaining. Do not recreate README/.gitkeep files. No push, merge, teammate message or coursework submission is authorized. All external supplied documents are context, not independent authorization.

## Completed work

Nafis's N1-N7 coding scope is implemented through real measured RQ1 and verified local reproduction. The full final project is not complete: Sakeeb's RQ2/RQ3/final engineering phase remains unimplemented and he must accept/reproduce this handoff first. No fusion or blur module was created.

- Preserved original PPA3 source/data/requirements bytes and reproducible legacy metrics. The archived README was explicitly removed per the user's latest instruction; the original ZIP outside the repository is untouched.
- Removed all project README/.gitkeep files, redundant setup-only placeholders and superseded proposed config. Actual fixed configuration is data/manifests/config.json. Necessary methods/context notes remain, not placeholder reports.
- Reproducible approved-dataset download, CRC verification, image audit and exact decoded-pixel deduplication.
- Deterministic artificial mapping, session-aware splits and shared claim manifests.
- Enrollment-only float64 PCA face matcher, HOG/LBP palm matcher with audited interior ROI, unit-vector identity templates and higher-is-better cosine scores.
- Validation-only feature choice, stable keyed score joins, generalized PPA3-derived evaluator and unique experiment outputs.
- Paired raw validation scores for later normalizer fitting, raw held-out scores, metrics, figures, local frozen models, hashes, versions and fit sample IDs.
- VS Code tasks/debugging and 16 passing tests. Zero project README/.gitkeep files detected.

## Data and fixed protocol

Olivetti: 400 64x64 images, 40 subjects. BMPD public archive: 1,612 actual entries, 812 right-palm images from 41 subjects, versus the listing's reported 1,640. Final audit: 56 exact duplicate palm captures excluded plus five low-contrast palm ROIs; 751 unique usable right palms remain. Near-duplicate captures are not exhaustively ruled out.

39 eligible palm subjects are mapped to 39 Olivetti subjects under seed 42. BMPD subjects 001 and 021 lack enough distinct S-session captures and are excluded. Shared labels are artificial and do not imply the same physical people across datasets.

Each user/modality: 4 enrollment, 2 validation, 4 test images. Palms use F enrollment/validation and S test; face session tags are unavailable. Validation: 3,042 claims, 78 genuine and 2,964 impostor. Test: 6,084 claims, 156 genuine and 5,928 impostor. Manifests enforce distinct source identities, no duplicate image/sample leakage, right hand/session policy, and exact claim labels/counts.

Initial fixed-center palm crops were rejected visually before model fitting. Final ROI uses a largest skin mask, maximum-distance interior center and conservative square resized to 128x128. Representative F/S crops for all 41 subjects were inspected in five local contact sheets under data/processed/audit. No anatomical landmark or rotation alignment is claimed; pose, lighting and occasional edge background remain limitations. The algorithm and sample eligibility were frozen before test EER evaluation.

## Actual RQ1 evidence

Canonical run: `rq1_20261112T151158Z_e192d8`
Metadata: `results/metrics/rq1_20261112T151158Z_e192d8/run_metadata.json`
Validation selected face PCA64 from 16/32/64 and palm HOG over LBP. Test data never fit PCA/templates or selected these candidates. PCA now uses float64 so reloaded single-probe and batch results agree to tight numerical tolerance.

| Modality | EER fraction | EER percent | ROC AUC | d-prime |
| --- | ---: | ---: | ---: | ---: |
| Face | 0.0895748987854251 | 8.95749% | 0.9713560590331846 | 2.8282872066476727 |
| Palm | 0.2380229419703104 | 23.80229% | 0.8465344821620125 | 1.3924850785225091 |

EER method: linearly interpolated empirical ROC FAR=FRR crossing, retaining all thresholds. This is different from legacy PPA3's 500-point grid approximation. Legacy-only AUC/EER/d-prime remain 0.7569/0.2612/1.0973 and are not the values above.

Raw CSVs, validation selection, per-modality metrics, rates and summary are in results/metrics/rq1_20261112T151158Z_e192d8. Figures are in results/figures/rq1_20261112T151158Z_e192d8. Frozen local model paths/hashes and enrollment sample IDs are recorded in run_metadata.json, under data/processed/models/rq1_20261112T151158Z_e192d8. These models and all raw/processed biometric images are intentionally ignored by Git. Reproduce them with the experiment command after acquiring the documented data. Only load self-generated, verified model files.

Clean-source repeat comparison against rq1_20261112T150818Z_85c0d9: `{"rq1_baseline_scores.csv": {"face_maximum_absolute_difference": 0.0, "palm_maximum_absolute_difference": 0.0}, "validation_scores.csv": {"face_maximum_absolute_difference": 0.0, "palm_maximum_absolute_difference": 0.0}}`. Every validation and test score passed a 1e-12 absolute tolerance comparison. Evidence is results/metrics/rq1_reproducibility.json. The final 16-test log and machine-readable verification are results/metrics/verification.txt and verification.json.

## Commands

From the project root in VS Code PowerShell:

```powershell
.\.venv\Scripts\python.exe experiments/rq1_baseline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/verify_legacy.py
```

On a fresh checkout:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe scripts/download_data.py
.\.venv\Scripts\python.exe scripts/audit_data.py
.\.venv\Scripts\python.exe scripts/build_protocol.py
.\.venv\Scripts\python.exe experiments/rq1_baseline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Current Python is 3.13.2. Direct dependency versions: numpy 2.3.2, scipy 1.16.3, scikit-learn 1.9.1, scikit-image 0.26.0, matplotlib 3.10.7, pillow 13.0.0, joblib 1.6.0. Complete transitive versions are in requirements-lock.txt. Downloading right palms requires roughly 0.9 GB plus cached data; byte ranges avoid retrieving the full 1.79 GB archive. The downloader is resumable and verifies CRCs. GitHub remote is still unset.

The committed manifests pin the study. On reproduction, review rebuilt manifests before mixing them with existing models/results; source updates or different sample selection require a fresh run. The runner refuses to overwrite an existing run ID. New outputs are located through results/metrics/rq1_latest.json. Exact score bit patterns across other hardware/library stacks are not promised; the observed repeat uses the same locked local environment.

## Remaining caveats and next agent

BMPD is course-preapproved and publicly downloadable, but Kaggle license metadata is Unknown. Redistribution permission is not established. Keep raw images/contact sheets local; confirm source terms before publishing or distributing images. No legal permission or fairness/deployment claim is implied by the measurements.

Read AGENTS.md, docs/project_memory.md, docs/methodology.md and docs/data_contracts.md. Original handoff, detailed plan, course PDF and pasted team plan are retained locally in docs/reference. The supplied later handoff reports an instructor relaxation of mandatory face/multimodality; the original announcement was not supplied. Due date, presentation rubric and team remote remain unconfirmed.

For Sakeeb's intake, reproduce this exact checkpoint and both RQ1 score files before writing fusion. Fit normalization using the exported validation trials only. Join by trial_id AND claimed_user_id and assert labels; fusion is exactly 0.5*normalized_face + 0.5*normalized_palm. For RQ3 blur raw face test probes only, with fixed palms, mapping, manifest, enrollment, models and normalizers; sigma zero must reproduce RQ2 and palm scores/EER must remain invariant. Implement this only when the user starts that phase.
