# CAP4103 Team Classifiers

Combining face and palmprint scores for authentication under image blur.

## Status

The planned coding segment is feature complete: both initial matchers, fixed data/claim protocol, validation-only normalization, equal-weight score fusion, frozen-model face-probe blur, evaluation, figures and integrity/repeatability checks. Nafis's N1-N7 and Nazmus's S1-S5 engineering scopes are integrated. Report, presentation, references, team acceptance and course submission remain separate.

The November 16 review passed all 57 local tests with zero skips. Independent raw-data RQ1, RQ2 and all five RQ3 conditions exactly reproduced the submitted scores in the original team environment. All 812 palm-file hashes pass. See [review findings](docs/integration_review.md) and [browser continuation handoff](docs/browser_handoff.md).

## Results

| Face blur sigma, source pixels | Face EER (%) | Palm EER (%) | Fusion EER (%) |
| --- | ---: | ---: | ---: |
| 0 | 8.95749 | 23.80229 | 7.69231 |
| 0.5 | 8.97436 | 23.80229 | 7.69231 |
| 1 | 9.09244 | 23.80229 | 7.94534 |
| 2 | 10.27328 | 23.80229 | 8.40081 |
| 3 | 11.08300 | 23.80229 | 9.21053 |

On this selected, artificially paired 39-user test set, fusion has lower observed EER than either modality at every tested sigma. Fusion still degrades under blur. These are descriptive results without confidence intervals, statistical-significance or demographic-fairness claims. Gaussian blur is not physical motion blur.

## Clone and open in VS Code

Install Git/Git LFS, Python 3.13 and VS Code, and obtain repository access from the owner.

```powershell
git lfs install
git clone https://github.com/NafisAnwar/CAP4103-Team-Classifiers.git
Set-Location CAP4103-Team-Classifiers
git lfs pull
git lfs fsck
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
code CAP4103-Biometric-Fusion.code-workspace
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Stop on failures; PowerShell's ErrorActionPreference alone does not catch every native exit code. Full image/model checks require actual LFS bytes, not pointer text. The validated Windows environment uses Python 3.13.2 and the original requirements-lock.txt. requirements-nazmus-tested.txt records the separate historical verification environment and does not replace the original lock.

## Verify and reproduce

The accepted reference remains rq1_20261112T151158Z_e192d8. The November 16 runs are rq1_main_verified_20261116, rq2_main_verified_20261116 and rq3_main_verified_20261116; corresponding repeat fusion/blur runs are also saved. Independent current evidence is under results/metrics/main_integration_20261116. Three separate latest pointers locate current RQ1/RQ2/RQ3 outputs.

```powershell
.\.venv\Scripts\python.exe -B scripts/verify_legacy.py
.\.venv\Scripts\python.exe -B -c "from src.experiment_support import load_frozen_models; models, info = load_frozen_models(); print(info['run_id'], sorted(models))"
.\.venv\Scripts\python.exe -B scripts/review_submission.py --rq2-run rq2_main_verified_20261116 --rq3-run rq3_main_verified_20261116 --repeat-run rq3_main_repeat_20261116 --output results/metrics/my_saved_score_audit
```

Use fresh output paths/run IDs. The last command rechecks saved scores and metrics; it does not rerun raw-image models. For an independent execution:

```powershell
.\.venv\Scripts\python.exe -B experiments/rq1_baseline.py --run-id rq1_my_reproduction
.\.venv\Scripts\python.exe -B experiments/rq2_fusion.py --run-id rq2_my_reproduction
.\.venv\Scripts\python.exe -B experiments/rq3_blur.py run --rq2-run rq2_my_reproduction --plan data/processed/blur_plans/integration_20261116/blur_plan.json --run-id rq3_my_reproduction
```

The saved plan/preview is verified against the same blur implementation, validation pixels and study protocol. To review a new severity plan, run prepare into a new directory, inspect validation_blur_preview.png, then explicitly run review with your actual observations before run. Do not claim that a recorded automated review is human-team acceptance.

```powershell
.\.venv\Scripts\python.exe -B experiments/rq3_blur.py prepare --output data/processed/my_new_plan
.\.venv\Scripts\python.exe -B experiments/rq3_blur.py review --plan data/processed/my_new_plan/blur_plan.json --note "Record your actual validation-preview observations here"
```

Do not use --rebuild during routine reproduction. The committed mapping, splits and trials define the study. Enrollment fits models, validation selects candidates and fits z-score parameters, and test remains held out. Fusion is exactly 0.5 times each normalized score. Blur changes only copies of raw face test probes; models, normalization, palms and claims remain frozen.

## Repository map

| Location | Contents |
| --- | --- |
| src/ | Audited loading, preprocessing, protocol, matchers, fusion, blur, evaluation and run support |
| experiments/ | RQ1 baseline, RQ2 clear fusion and RQ3 frozen blur runners |
| tests/ | 57 unit/integration tests |
| scripts/ | Data acquisition/audit, legacy regression, repeatability and saved-score audits |
| data/manifests/ | Locked inventories, mapping, partitions and claims |
| data/raw/ and data/processed/ | LFS-backed study assets, frozen models and reviewed blur plan |
| results/metrics/main_integration_20261116/ | Independent review, final study table, environment and test evidence |
| results/figures/ | Per-modality ROC/FAR-FRR/distributions and comparison figures |
| docs/reference/ | Supplied course sources/templates, including November 15 description |
| docs/browser_handoff.md | Final methods/results, rubric mapping, writing plan and browser starter prompt |

The original five PPA3 source/data/requirements files remain byte-preserved in ppa3_legacy/. Their landmark regression is distinct from the image study. The generic evaluator adapts the HW3 workflow and uses empirical-ROC interpolation; do not describe it as the unchanged legacy grid evaluator.

## Data and limitations

Olivetti contributes 400 grayscale 64x64 images. BMPD contributes 812 audited right-palm captures, with 56 exact duplicates and five low-contrast ROIs excluded. Thirty-nine eligible palm subjects map artificially to 39 face subjects. Each user/modality has 4 enrollment, 2 validation and 4 test images. Palms use F for enrollment/validation and S for test. There are 3,042 validation and 6,084 test claims.

Sources: [Olivetti loader](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_olivetti_faces.html), [BMPD listing](https://www.kaggle.com/datasets/mahdieizadpanah/birjand-university-mobile-palmprint-databasebmpd), [BMPD paper](https://doi.org/10.1504/IJGUC.2019.102016).

BMPD license metadata is Unknown. Public download/course preapproval and private GitHub/LFS access do not establish redistribution permission. Resolve source terms before public release or redistribution. Keep biometric samples/models out of the browser writing bundle. Other limitations include small sample size, dependent claims, artificial cross-person pairing, exact-only deduplication, palm session shift and heuristic crops without anatomical/rotation alignment.

Keep environments, secrets, caches and temporary work out of commits. Preserve seed 42 and accepted artifacts. New useful comments should be informal lowercase inline comments with no space after #. No empty placeholder files are required.
