# CAP4103 Final Project | The Classifiers

## Combining Face and Palmprint Scores for Authentication Under Image Blur

University of South Florida | CAP4103 Mobile Biometrics | Fall 2026

**Instructor:** Dr. Tempestt Neal

**Team:** Nafis Anwar, Nazmus Sakeeb, Diego Laverdy, Mikaela Kelly, Sienah Spears

## 1. Start here

1. Extract the entire ZIP to a writable folder. Do not run the launcher from inside the ZIP viewer.
2. Install Python 3.13 if needed. The original Windows 11 experiments used Python 3.13.2.
3. Double-click `RUN_PROJECT.cmd`. It creates an isolated virtual environment, installs the pinned dependencies when needed, checks the environment and opens the project menu. Initial installation requires internet access.
4. Select option 1 to check the included results and run the automated tests. No raw biometric dataset download is required for this option.
5. To independently reproduce experiments from images, obtain the datasets as described below, then select option 4.

| Menu | Task |
|---:|---|
| 1 | Verify original submitted results, file hashes and tests |
| 2 | Reproduce RQ1: individual authentication |
| 3 | Reproduce RQ1 and RQ2: score-level fusion |
| 4 | Reproduce the complete RQ1 through RQ3 study |
| 5 | Download the original datasets from authorized sources |
| 6 | Run automated tests |
| 0 | Exit |

The same entry point supports PowerShell commands:

```powershell
.\RUN_PROJECT.cmd verify
.\RUN_PROJECT.cmd full
```

With an already configured Python 3.13 virtual environment, use `python main.py verify`, `python main.py rq1`, `python main.py rq2`, `python main.py full`, `python main.py download` or `python main.py tests`. Run `python main.py setup` inside that environment if dependencies need installation. All experiment commands use the same pinned versions; no GPU is required.

## 2. Independent reproduction and datasets

The ZIP contains fixed dataset inventories, identity mappings, partitions, trial definitions, experiment configuration, source code, reference scores and figures. Raw biometric images and enrolled templates are not redistributed. Obtain the original datasets under their applicable terms:

- [Olivetti Faces](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_olivetti_faces.html)
- [Birjand University Mobile Palmprint Database (BMPD)](https://www.kaggle.com/datasets/mahdieizadpanah/birjand-university-mobile-palmprint-databasebmpd); [research publication](https://doi.org/10.1504/IJGUC.2019.102016)

Menu option 5 attempts acquisition from the original services; it requires internet access and availability of the sources. Alternatively, place the Olivetti archive at `project/data/raw/face/olivetti.npz` and the original 812 right-palm JPG files at `project/data/raw/palm/images/`. Retain the original filenames. The fixed palmprint inventory verifies the original file hashes.

If the datasets are already available in a separate directory with a `data/raw/` subdirectory, supply that directory without moving files:

```powershell
.\RUN_PROJECT.cmd full --data-root "C:\path\to\dataset-root"
```

Full reproduction independently prepares the protocol, retrains the authentication models, validates the saved claim alignment, fits fusion normalization on validation scores and evaluates each facial blur condition. New artifacts and a `reproduction_summary.json` are written under `project/work/reproduction_*/`. The original reference evidence is never overwritten. The reproduction comparison uses absolute tolerances of 1e-8 for matching scores and 1e-7 for metrics.

Saved-result verification recalculates metrics from stored scores, confirms the fusion calculation, verifies repeated runs and executes tests. It is not a substitute for independent image-level reproduction. Tests requiring original images or frozen model assets are skipped when those assets are absent. Full reproduction creates new model artifacts in its independent workspace.

## 3. Research questions and experimental design

1. **RQ1:** How do face-only and palmprint-only authentication compare under clear-image conditions?
2. **RQ2:** Does equal-weight fusion of validation-normalized face and palmprint scores improve clear-image authentication relative to either individual modality?
3. **RQ3:** As Gaussian blur increases in facial test images while palmprint quality remains unchanged, how does score-level fusion compare with either individual modality?

RQ1 established the stronger face baseline. RQ2 tested whether palmprint scores nevertheless provide complementary information. RQ3 investigated whether the observed fusion advantage persists under facial degradation.

Olivetti contains 400 grayscale images from 40 people. The BMPD audit examined 812 right-palm images from 41 individuals, of which 751 were usable after quality and duplicate checks. A fixed artificial mapping pairs 39 eligible face subjects with 39 eligible palmprint subjects. The paired subjects are not the same physical individuals.

| Protocol | Value |
|---|---:|
| Simulated identities | 39 |
| Selected samples per identity per modality | 10 |
| Enrollment / validation / test images per identity | 4 / 2 / 4 |
| Enrollment / validation / test images per modality | 156 / 78 / 156 |
| Genuine / impostor validation claims | 78 / 2,964 |
| Genuine / impostor test claims | 156 / 5,928 |
| Random seed | 42 |

Every validation and test probe is compared against all 39 enrolled identities. Palmprint enrollment and validation use first-session captures while testing uses second-session captures; facial images follow a seeded within-subject partition. Feature settings are selected on validation data, with models fitted on enrollment data only.

| Component | Implementation |
|---|---|
| Face features | 64 x 64 grayscale images, PCA with 64 components |
| Palmprint features | Skin segmentation, central ROI, 1,764 HOG features |
| Enrollment and matching | L2-normalized mean templates, cosine similarity |
| Fusion | Validation-only Z-score normalization, equal-weight averaging |
| Degradation | Gaussian blur of facial test probes only |
| Evaluation | EER, ROC AUC, d-prime, FAR, FRR and score distributions |

Fusion score = 0.5 × normalized face score + 0.5 × normalized palmprint score.

RQ3 holds the enrolled templates, normalization parameters, palmprint scores, trial identities and fusion weights fixed across all five blur conditions.

The project directly reuses the submitted HW3 numerical evaluation routines in `project/src/hw3_evaluator.py`, adapting threshold selection to empirical biometric score domains and computing interpolated EER and ROC AUC. The exact original submitted HW3 source is preserved in `project/docs/hw3_original.py.txt`. The separate PPA3 regression evidence remains available in `project/ppa3_legacy/`.

## 4. Reference results

### RQ1 and RQ2: clear-image authentication

| System | EER (%) | ROC AUC | D-prime |
|---|---:|---:|---:|
| Face only | 8.96 | 0.9714 | 2.8283 |
| Palmprint only | 23.80 | 0.8465 | 1.3925 |
| Equal-weight fusion | 7.69 | 0.9797 | 2.9294 |

### RQ3: face-only Gaussian blur

| Gaussian sigma | Face EER (%) | Palmprint EER (%) | Fusion EER (%) |
|---:|---:|---:|---:|
| 0.0 | 8.96 | 23.80 | 7.69 |
| 0.5 | 8.97 | 23.80 | 7.69 |
| 1.0 | 9.09 | 23.80 | 7.95 |
| 2.0 | 10.27 | 23.80 | 8.40 |
| 3.0 | 11.08 | 23.80 | 9.21 |

Lower EER is better; higher ROC AUC and d-prime reflect stronger observed discrimination. Fusion had the lowest observed EER across all five conditions. The artificial identity pairing and small sample limit generalization to naturally paired subjects or deployment populations. These observations are not claims of statistical significance.

The original verified and repeated run records, including numerical scores, configuration and figures, are preserved under `project/results/`. New reproduction runs record current source and environment provenance separately.

## 5. Code and rubric navigation

The submission root contains exactly `RUN_PROJECT.cmd`, `main.py`, `README.md`, `requirements.txt` and the `project/` implementation directory. The top-level requirements file is the exact pinned dependency lock. All paths below refer to the extracted ZIP; in the development checkout, omit the `project/` prefix.

| Code rubric criterion | Implementation under project/ |
|---|---|
| Sample loading, IDs and disjoint partitions | `src/datasets.py`, `src/trial_protocol.py`, `data/manifests/` |
| Feature extraction | `src/face_authentication.py`, `src/palmprint_authentication.py`, `src/preprocessing.py` |
| Enrolled templates and matching | `src/matching.py`, `src/face_authentication.py`, `src/palmprint_authentication.py` |
| Genuine/impostor labeling and HW3 evaluation | `src/trial_protocol.py`, `src/hw3_evaluator.py`, `src/evaluation.py` |
| Score fusion | `src/fusion.py` |
| RQ1 conditions | `experiments/rq1_baseline.py` |
| RQ2 conditions | `experiments/rq2_fusion.py` |
| RQ3 conditions | `experiments/rq3_blur.py`, `src/blur.py` |

Additional verification and reproducibility resources:

- `project/scripts/reproduce_full.py`: independent end-to-end reproduction.
- `project/scripts/verify_package.py`: checksum verification, saved-score audit and automated tests.
- `project/tests/`: unit, integration, regression and integrity tests.
- `project/results/metrics/main_integration_20261116/report_clear_metrics.csv`: RQ1 and RQ2 reported metrics.
- `project/results/metrics/main_integration_20261116/report_blur_metrics.csv`: all RQ3 conditions.
- `project/results/metrics/main_integration_20261116/score_audit/study_master_metrics.csv`: detailed study metrics.
- `project/results/figures/`: original plots for all three research questions.
- `project/docs/`: methodology, data contracts, verification and historical source evidence.
- `project/SHA256SUMS.txt`: SHA-256 hashes of the submitted files, relative to the outer package root.

Image degradation models controlled Gaussian blur rather than every kind of real-world acquisition failure. Palmprint cropping does not perform explicit anatomical or rotational alignment. Production use would require consent, appropriate biometric template protection, secure retention and broader validation.
