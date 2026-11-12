# CAP4103 Team Classifiers

## Combining face and palmprint scores for authentication under image blur

This CAP4103 Mobile Biometrics project compares face and palmprint authentication, then studies equal-weight score fusion and the effect of Gaussian blur on face probes. The face and palm datasets contain different people, so shared identities are explicitly simulated.

## Current status

Nafis's N1-N7 implementation is complete. Both modality pipelines, fixed partitions/claims, validation selection, evaluation, RQ1 results and reproducibility checks are implemented. Nazmus Sakeeb's next phase is validation-only normalization, 50/50 fusion (RQ2), face-probe blur (RQ3) and final engineering QA. The allocation is 60/40 engineering effort units; it does not measure completion of the report or presentation.

| RQ1 system | EER | ROC AUC | d-prime |
| --- | ---: | ---: | ---: |
| Face, PCA64 and cosine templates | 8.95749% | 0.971356 | 2.828287 |
| Palm, HOG and cosine templates | 23.80229% | 0.846534 | 1.392485 |

Models are fitted on enrollment only. Candidate selection uses validation only. EER uses linear interpolation at the empirical FAR/FRR crossing. These image results are separate from the archived PPA3 landmark regression.

## Quick start in VS Code on Windows

Install Git, Git LFS, Python 3.13 and VS Code. Repository access requires the owner's invitation while the repository is private.

```powershell
git lfs install
git clone https://github.com/NafisAnwar/CAP4103-Team-Classifiers.git
Set-Location CAP4103-Team-Classifiers
git lfs pull
code CAP4103-Biometric-Fusion.code-workspace
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Run each command only after the preceding command succeeds. Activation is optional; the commands use the environment interpreter directly. The original validated environment used Python 3.13.2. If VS Code selects another interpreter, select .venv/Scripts/python.exe.

The 33-test local suite passed with all local data/models present. Two integration tests are skipped when their required local assets are absent. A skip is not proof that those assets were downloaded successfully.

## Data and model availability

The original source upload deliberately excluded data/raw, data/processed, most docs/reference files and ppa3_legacy/plots. It was a complete upload of tracked files. scripts/prepare_full_upload.ps1 optionally adds these four folders and uses Git LFS for raw/processed files and reference PDFs. Its preparation step does not commit or push. Until that bundle has been committed and pushed, a clone will not contain those assets.

If the full bundle is available, git lfs pull materializes the files; check the frozen baseline before starting new work:

```powershell
.\.venv\Scripts\python.exe -B -c "from src.experiment_support import load_frozen_models; models, metadata = load_frozen_models(); print(metadata['run_id'], sorted(models))"
```

If raw data is absent, retrieve it from the documented sources and reproduce locally:

```powershell
.\.venv\Scripts\python.exe scripts/download_data.py
.\.venv\Scripts\python.exe -B experiments/rq1_baseline.py
```

The experiment prints a fresh run ID and updates results/metrics/rq1_latest.json. Load reproduced models using load_frozen_models(model_run_id='<new-run-id>'); they must match the original accepted model bytes. Do not overwrite existing run IDs or rebuild manifests to bypass a failed integrity check.

## Fixed study

- Olivetti: 400 grayscale face images, 40 source identities.
- BMPD: 812 right-palm captures audited; 56 exact duplicates and five low-contrast ROIs excluded, leaving 751 usable unique captures.
- Seed 42 maps 39 eligible palm subjects to 39 face subjects under simulated shared labels.
- Each user/modality has 4 enrollment, 2 validation and 4 test images. Palm enrollment/validation use session F; test uses session S.
- Validation has 3,042 claims; test has 6,084. Join modalities by trial_id and claimed_user_id, with identical truth labels.

## Repository map

| Location | Purpose |
| --- | --- |
| src/ | Auditing/loading, preprocessing, protocol validation, models, keyed matching, evaluation and run support |
| experiments/rq1_baseline.py | Enrollment-only fit, validation selection and held-out RQ1 export |
| scripts/ | Acquisition, audit, protocol building, environment/legacy checks and upload preparation |
| data/manifests/ | Locked image inventory, identity mapping, partitions and claim manifests |
| results/metrics/ and results/figures/ | Measured results, plots, versions and integrity evidence |
| ppa3_legacy/ | Five byte-preserved original PPA3 source/data/requirements files |
| tests/ | Protocol, matching, metric, artifact and reproduction checks |
| docs/nazmus_handoff.md | Detailed next-phase instructions and acceptance criteria |
| docs/upload_guide.md | Owner upload commands, verification and recovery |

Read [Nazmus's handoff](docs/nazmus_handoff.md), [methodology](docs/methodology.md), [data contracts](docs/data_contracts.md) and [project status](docs/project_status.md).

## Integrity and reproduction

results/metrics/rq1_accepted.json pins the original verified Nafis baseline rq1_20261112T151158Z_e192d8. The later rq1_structure_verified_20261112 run reproduced all validation/test scores exactly and both serialized models byte-for-byte in the locked local environment. Latest-run discovery is independent of the accepted baseline.

protocol_lock.json protects the nine audit/protocol manifests. Text hashes tolerate line-ending conversion only; image/model hashes require exact bytes. Runs record provenance and completion state and refuse collisions. Audit/build commands require --rebuild to replace existing manifests. Ordinary legacy verification uses temporary copies:

```powershell
.\.venv\Scripts\python.exe -B scripts/verify_legacy.py
```

## Dataset sources and limitations

Olivetti is retrieved through [scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_olivetti_faces.html). BMPD comes from the [creator's Kaggle listing](https://www.kaggle.com/datasets/mahdieizadpanah/birjand-university-mobile-palmprint-databasebmpd), with [source paper](https://doi.org/10.1504/IJGUC.2019.102016).

BMPD's downloaded license metadata is Unknown. Public availability and course preapproval do not establish redistribution permission; private GitHub access and LFS do not change those terms. Confirm permitted sharing before uploading biometric data or course/private documents. The downloader path allows collaborators to acquire data directly from its source.

The study has artificial identity pairing, a small selected population, exact-only duplicate detection, session shift, heuristic palm crops without anatomical/rotation alignment and no demographic fairness analysis. Gaussian blur represents loss of sharpness rather than physical motion blur. Report negative or inconclusive fusion results honestly.

## Development

Preserve seed 42 and the original PPA3 files. Keep test data held out from fitting, normalization and model selection. Use useful informal lowercase inline comments, with no space after #. Keep environments, credentials, caches and temporary work outside version control. One root README is now requested; avoid empty placeholder documents and .gitkeep files.
