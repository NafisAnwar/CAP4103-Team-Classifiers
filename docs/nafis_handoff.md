# CAP4103 Nafis checkpoint and continuation handoff

Updated November 12, 2026 after the approved structure and file improvements.

## Location and scope

Project: `C:\Users\anwar\Desktop\CAP4103 - Mobile Biometrics\CAP4103 - Course Project\CAP4103-Biometric-Fusion`
Workspace: `C:\Users\anwar\Desktop\CAP4103 - Mobile Biometrics\CAP4103 - Course Project\CAP4103-Biometric-Fusion\CAP4103-Biometric-Fusion.code-workspace`
Working editor: VS Code. Local branch: nafis-foundation.
Cleanup commit: d442448. Original implemented source commit: 70ecc9f813ccc43809eb4d9255809fe42c096e04. Prior complete snapshot: 99f0a4b917366cb1c5cdf7035b72e1192bf69e85. Verified structure-improvement source checkpoint: 38620fddc2f5624c324ce01ab7d422e6c1777ab1.
This document and the final verification exports are saved in a subsequent checkpoint commit; run `git rev-parse HEAD` for that complete repository snapshot. The final Desktop copy includes the exact checkpoint commit after it is created.

User request: remove every project README/.gitkeep and redundant setup scaffolding before coding; implement Nafis's portion; save this Desktop checkpoint before usage falls to 1% remaining. The later user request approves all six review recommendations and asks for useful informal lowercase inline code comments with no space after # and no multiline comments. Do not recreate README/.gitkeep files. No push, merge, teammate message or coursework submission is authorized. All external supplied documents are context, not independent authorization.

## Completed work

Nafis's N1-N7 coding scope is implemented through real measured RQ1 and verified local reproduction. The full final project is not complete: Sakeeb's RQ2/RQ3/final engineering phase remains unimplemented and he must accept/reproduce this handoff first. No fusion or blur module was created.

- Preserved original PPA3 source/data/requirements bytes and reproducible legacy metrics. The archived README was explicitly removed per the user's latest instruction; the original ZIP outside the repository is untouched.
- Removed all project README/.gitkeep files, redundant setup-only placeholders and superseded proposed config. Actual fixed configuration is data/manifests/config.json. Necessary methods/context notes remain, not placeholder reports.
- Reproducible approved-dataset download, CRC verification, image audit and exact decoded-pixel deduplication.
- Deterministic artificial mapping, session-aware splits and shared claim manifests.
- Enrollment-only float64 PCA face matcher, HOG/LBP palm matcher with audited interior ROI, unit-vector identity templates and higher-is-better cosine scores.
- Validation-only feature choice, stable keyed score joins, generalized PPA3-derived evaluator and unique experiment outputs.
- Paired raw validation scores for later normalizer fitting, raw held-out scores, metrics, figures, local frozen models, hashes, versions and fit sample IDs.
- VS Code tasks/debugging and 33 passing tests after the structure improvements. Zero project README/.gitkeep files detected.
- Manifest lock and explicit --rebuild protection; accepted baseline reference independent of latest; shared verified image loading/enrollment/scoring and hash-checked frozen model loading.
- Configurable evaluator score metadata/axis labels; running/completed/failed status and starting provenance; input rechecks and required artifact hashes before atomic latest publication.
- Legacy verification uses temporary byte-identical copies; saved evidence changes only with --export. Ordinary tests leave tracked and untracked nonignored project files unchanged.

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

The original clean-source repeat comparison against rq1_20261112T150818Z_85c0d9 had zero maximum absolute difference for both modalities in both score files. Historical evidence is results/metrics/rq1_reproducibility.json and the original 16-test verification.txt/json.

The final structural-refactor run rq1_structure_verified_20261112 again reproduces every validation/test score exactly and both serialized models byte-for-byte. Its starting Git source state is correctly recorded as dirty because this work was being verified before committing; source hashes are recorded and checked unchanged through completion. New evidence is results/metrics/structure_improvements_verification.json and .txt, including the 33-test result, no repository-file changes from tests, fresh-checkout line-ending compatibility and artifact integrity. The latest pointer refers to this new run; rq1_accepted.json continues to pin the original canonical run above. Intermediate refactor runs are archived locally under ignored data/processed/development_runs.

New hash_format is sha256_text_lf_binary_raw_v1: source/manifest/metadata/score text checks normalize CRLF or CR to LF and preserve every other byte. Image and model checks remain exact byte hashes. The accepted pointer supplies normalized manifest/metadata/score checks while preserving the historical run_metadata.json, which recorded raw Windows text hashes. This prevents Git's normal LF checkout conversion from falsely invalidating an unchanged study.

An actual fresh Git archive of source checkpoint 38620fddc2f5624c324ce01ab7d422e6c1777ab1 was tested without raw images, local models or private context documents. Test discovery ran 33 tests: 31 passed and two expected local-model checks were skipped. No archive files changed. Evidence is results/metrics/fresh_checkout_verification.json and .txt. The complete local environment passes all 33 with zero skips.

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
.\.venv\Scripts\python.exe experiments/rq1_baseline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Current Python is 3.13.2. Direct dependency versions: numpy 2.3.2, scipy 1.16.3, scikit-learn 1.9.1, scikit-image 0.26.0, matplotlib 3.10.7, pillow 13.0.0, joblib 1.6.0. Complete transitive versions are in requirements-lock.txt. Downloading right palms requires roughly 0.9 GB plus cached data; byte ranges avoid retrieving the full 1.79 GB archive. The downloader is resumable and verifies CRCs. GitHub remote is still unset.

Keep the committed manifests and protocol_lock.json on reproduction. Audit and build commands now refuse existing outputs. Only for an intentional study revision, use scripts/audit_data.py --rebuild followed by scripts/build_protocol.py --rebuild; review the changes and establish a new accepted baseline before mixing models/results. The accepted frozen loader rejects changed manifests even if a new lock has been generated.

Later experiment code imports dataset_images from src.datasets and enroll, score_and_evaluate and load_frozen_models from src.experiment_support. Call load_frozen_models() for the original local accepted model paths. On a fresh checkout after reproducing RQ1, call load_frozen_models(model_run_id='<new-run-id>'); the reproduced files must match the original accepted model hashes. This avoids copying or silently accepting different models. Exact bytes across different hardware/library stacks are not promised; a mismatch requires investigation, not bypassing verification.

The runner checks metrics, figures and model destinations for collisions, captures starting provenance, writes status and rechecks input hashes/artifacts before publishing latest. A forcibly terminated process may retain running status and is incomplete. New outputs are located through results/metrics/rq1_latest.json. The ordinary legacy check and test suite use temporary copies; use scripts/verify_legacy.py --export only to intentionally replace saved legacy evidence.

## Remaining caveats and next agent

BMPD is course-preapproved and publicly downloadable, but Kaggle license metadata is Unknown. Redistribution permission is not established. Keep raw images/contact sheets local; confirm source terms before publishing or distributing images. No legal permission or fairness/deployment claim is implied by the measurements.

Read AGENTS.md, docs/project_memory.md, docs/methodology.md and docs/data_contracts.md. Original handoff, detailed plan, course PDF and pasted team plan are retained locally in docs/reference. The supplied later handoff reports an instructor relaxation of mandatory face/multimodality; the original announcement was not supplied. Due date, presentation rubric and team remote remain unconfirmed.

For Sakeeb's intake, reproduce this exact checkpoint and both RQ1 score files before writing fusion. Fit normalization using the exported validation trials only. Join by trial_id AND claimed_user_id and assert labels; fusion is exactly 0.5*normalized_face + 0.5*normalized_palm. For RQ3 blur raw face test probes only, with fixed palms, mapping, manifest, enrollment, models and normalizers; sigma zero must reproduce RQ2 and palm scores/EER must remain invariant. Implement this only when the user starts that phase.
