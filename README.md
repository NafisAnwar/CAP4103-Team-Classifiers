# CAP4103 Team Classifiers

## Combining Face and Palmprint Scores for Authentication Under Image Blur

- **Course:** CAP4103 - Mobile Biometrics
- **Institution:** University of South Florida
- **Semester:** Fall 2026
- **Instructor:** Dr. Tempestt Neal
- **Team:** The Classifiers

## Team Contributions

| Team Member | Role | Responsibilities |
| --- | --- | --- |
| Nafis Anwar | Lead Developer and Project Coordinator | 60% of engineering implementation, project architecture, dataset preparation, facial authentication, baseline evaluation, system integration, repository management and technical verification |
| Nazmus Sakeeb | Developer and Evaluation Lead | 40% of engineering implementation, palmprint authentication development, score-level fusion, facial blur experiments and performance evaluation |
| Diego Laverdy | Research and Methodology Lead | Dataset research, literature review, citations and experimental methodology |
| Mikaela Kelly | Results and Report Lead | Results analysis, tables, figures, technical report writing and document organization |
| Sienah Spears | Presentation and Quality Assurance Lead | Presentation development, ethics statement, references, testing coordination and final quality review |

The 60/40 allocation refers specifically to software development and engineering work, rather than overall project contribution.

## Project Overview

This project implements and evaluates a multimodal biometric authentication system combining facial recognition and palmprint recognition. The objective is to determine whether score-level fusion improves authentication performance under clear image conditions and whether an unaffected biometric modality can help maintain performance when facial image quality deteriorates.

The system uses separate feature extraction and matching pipelines for each modality, followed by validation-based score normalization and equal-weight fusion. Performance is measured using Equal Error Rate (EER), ROC AUC, d-prime, and genuine and impostor score distributions.

## Research Questions

### RQ1: Baseline Authentication Performance

How do face-only and palmprint-only biometric authentication systems compare in terms of Equal Error Rate (EER), ROC AUC and d-prime under clear-image conditions?

### RQ2: Equal-Weight Score-Level Fusion

Does equal-weight fusion of validation-normalized face and palmprint matching scores improve authentication performance relative to either individual modality under clear-image conditions?

### RQ3: Authentication Performance Under Facial Image Blur

As Gaussian blur increases in facial test images while palmprint image quality remains unchanged, how does equal-weight score-level fusion affect authentication performance compared with face-only and palmprint-only authentication?

### Experimental Progression

RQ1 established individual modality performance, with face authentication achieving an EER of 8.96% compared with 23.80% for palmprint authentication. This motivated RQ2, which investigated whether palmprint matching scores could provide complementary information despite the weaker individual baseline.

RQ2 achieved a fusion EER of 7.69%, reducing observed EER by 1.27 percentage points relative to face-only authentication. This motivated RQ3, which evaluated whether the observed fusion advantage persisted under increasing facial image blur.

All three experiments retain the same simulated identities, sample partitions and authentication claim protocol.

## System Architecture

| Component | Implementation |
| --- | --- |
| Facial preprocessing | Original 64x64 grayscale face images |
| Facial features | Principal Component Analysis (64 components) |
| Palmprint preprocessing | Skin segmentation and interior palm ROI extraction |
| Palmprint features | Histogram of Oriented Gradients (1,764 features) |
| Enrollment | L2-normalized mean feature templates |
| Matching | Cosine similarity |
| Score normalization | Validation-only Z-score normalization |
| Fusion | Equal-weight normalized score averaging |
| Image degradation | Gaussian filtering of facial test probes |
| Evaluation | EER, ROC AUC, d-prime and score distributions |

Both biometric pipelines share the same simulated identity mapping, authentication trial protocol and evaluation workflow.

## Datasets and Experimental Protocol

- [Olivetti Faces Dataset](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_olivetti_faces.html)
- [Birjand University Mobile Palmprint Database](https://www.kaggle.com/datasets/mahdieizadpanah/birjand-university-mobile-palmprint-databasebmpd)
- [BMPD associated research publication](https://doi.org/10.1504/IJGUC.2019.102016)

| Parameter | Value |
| --- | --- |
| Simulated identities | 39 |
| Enrollment samples per identity, per modality | 4 |
| Validation samples per identity, per modality | 2 |
| Test samples per identity, per modality | 4 |
| Total selected images | 780 |
| Validation claims | 3,042 |
| Test claims | 6,084 |
| Random seed | 42 |

The original datasets contain different physical individuals. A fixed artificial identity mapping simulates a shared multimodal population. Enrollment, validation and test partitions remain consistent across all experiments.

Palmprint enrollment and validation use first-session captures, while testing uses second-session captures. Facial images use a seeded within-user partition.

## Experimental Results

### RQ1 and RQ2: Clear-Image Authentication

| System | EER (%) | ROC AUC | D-prime |
| --- | ---: | ---: | ---: |
| Face | 8.96 | 0.9714 | 2.8283 |
| Palmprint | 23.80 | 0.8465 | 1.3925 |
| Equal-weight fusion | 7.69 | 0.9797 | 2.9294 |

Equal-weight fusion reduced observed EER by 1.27 percentage points relative to face-only authentication and 16.11 percentage points relative to palmprint-only authentication.

![Clear-condition authentication comparison](results/figures/rq2_main_verified_20261116/rq2_comparison.png)

### RQ3: Authentication Under Facial Image Blur

| Gaussian Sigma (pixels) | Face EER (%) | Palmprint EER (%) | Fusion EER (%) |
| ---: | ---: | ---: | ---: |
| 0.0 | 8.96 | 23.80 | 7.69 |
| 0.5 | 8.97 | 23.80 | 7.69 |
| 1.0 | 9.09 | 23.80 | 7.95 |
| 2.0 | 10.27 | 23.80 | 8.40 |
| 3.0 | 11.08 | 23.80 | 9.21 |

Fusion retained a lower observed EER at every evaluated blur level. Palmprint inputs and matching scores remained unchanged while facial probe quality decreased.

![Authentication performance under facial image blur](results/figures/rq3_main_verified_20261116/rq3_comparison.png)

## Experimental Controls

| Setting | RQ1 | RQ2 | RQ3 |
| --- | --- | --- | --- |
| Identity mapping and data splits | Fixed | Fixed | Fixed |
| Enrollment models | Fitted on enrollment | Frozen | Frozen |
| Matching method | Cosine | Cosine | Cosine |
| Score normalization | None | Validation-fitted | Frozen |
| Fusion weights | None | 0.5 / 0.5 | 0.5 / 0.5 |
| Facial blur sigma | 0 | 0 | 0, 0.5, 1, 2, 3 |
| Palmprint image quality | Unchanged | Unchanged | Unchanged |

No test-set data are used to fit the normalization parameters or select fusion weights.

## Repository Structure

| Directory | Description |
| --- | --- |
| `src/` | Dataset processing, feature extraction, matching, fusion, blur and evaluation |
| `experiments/` | Executable research question experiments |
| `data/manifests/` | Fixed dataset inventories, identity mappings, partitions and claims |
| `data/raw/` | Original biometric dataset assets |
| `data/processed/` | Audited data, frozen models and blur plans |
| `results/metrics/` | Authentication scores, quantitative metrics and verification evidence |
| `results/figures/` | ROC curves, score distributions and comparative figures |
| `scripts/` | Dataset preparation, environment checks and verification utilities |
| `tests/` | Automated unit and integration tests |
| `ppa3_legacy/` | Preserved PPA3 implementation and regression inputs |
| `docs/` | Technical methodology, data contracts and verification documentation |

## Installation

The validated environment uses Python 3.13.2.

Git LFS is required to retrieve the biometric dataset and model assets. Dataset access and distribution must comply with the original dataset terms.

```powershell
git lfs install
git clone https://github.com/NafisAnwar/CAP4103-Team-Classifiers.git
Set-Location CAP4103-Team-Classifiers
git lfs pull

py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check

code CAP4103-Biometric-Fusion.code-workspace
```

## Running the Experiments

Execute the following commands from the repository root using unique run identifiers.

### RQ1: Individual Authentication

```powershell
.\.venv\Scripts\python.exe experiments/rq1_baseline.py --run-id rq1_reproduction
```

### RQ2: Score-Level Fusion

```powershell
.\.venv\Scripts\python.exe experiments/rq2_fusion.py --run-id rq2_reproduction
```

### RQ3: Facial Image Blur

```powershell
.\.venv\Scripts\python.exe experiments/rq3_blur.py run --rq2-run rq2_reproduction --plan data/processed/blur_plans/integration_20261116/blur_plan.json --run-id rq3_reproduction
```

These commands preserve the accepted baseline and fixed study manifests. Existing run identifiers cannot be overwritten.

## Results and Traceability

| Experiment | Implementation | Verified Results |
| --- | --- | --- |
| RQ1 | `experiments/rq1_baseline.py` | `results/metrics/rq1_main_verified_20261116/` |
| RQ2 | `experiments/rq2_fusion.py` | `results/metrics/rq2_main_verified_20261116/` |
| RQ3 | `experiments/rq3_blur.py` | `results/metrics/rq3_main_verified_20261116/` |

Combined experimental results and independent verification evidence are available under:

- [Clear-condition metrics](results/metrics/main_integration_20261116/report_clear_metrics.csv)
- [Blur-condition metrics](results/metrics/main_integration_20261116/report_blur_metrics.csv)
- [Master experimental metrics](results/metrics/main_integration_20261116/score_audit/study_master_metrics.csv)
- [Reproduction comparison](results/metrics/main_integration_20261116/reproduction_comparison.json)

## Testing and Verification

The complete saved-study verification workflow can be executed with one command:

```powershell
.\.venv\Scripts\python.exe -B scripts/verify_study.py
```

This command verifies RQ1 artifact integrity, all 812 raw palmprint file hashes, the automated test suite, RQ2 repeatability and the saved RQ3 experimental results.

Verification outputs are written to a new temporary directory without replacing the recorded experimental artifacts.

Individual verification commands are provided below.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B scripts/verify_legacy.py
```

The integrated implementation passed 57 automated tests with zero skips. Independent reproduction verified the RQ1 scores, RQ2 fusion results and all five RQ3 blur conditions.

The evaluator extends the original HW3/PPA3 performance evaluation workflow to support image-based authentication and normalized multimodal similarity scores.

For detailed documentation, see:

- [Methodology](docs/methodology.md)
- [Data Contracts](docs/data_contracts.md)
- [Technical Verification](docs/verification.md)

## Limitations

The study uses a small, artificially paired population and reports descriptive results for the evaluated conditions. Authentication claims sharing identities and probe samples are not statistically independent.

Gaussian blur approximates a reduction in image sharpness but does not represent every form of physical motion blur. The palmprint ROI method does not include explicit anatomical or rotational alignment.

The findings do not establish demographic fairness, statistical significance or deployment-level authentication accuracy. A production authentication threshold has not been independently validated.

Dataset accessibility does not establish redistribution permission. Biometric assets must be handled in accordance with their original usage terms.
