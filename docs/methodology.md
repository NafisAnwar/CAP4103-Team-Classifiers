# Experimental Methodology

## Research Design

The study develops a multimodal authentication system through three connected experiments. RQ1 establishes individual modality baselines, RQ2 evaluates equal-weight score fusion, and RQ3 investigates the effect of increasing facial image blur while maintaining palmprint image quality.

All experiments use the same fixed simulated identities, sample partitions and authentication claims.

## Dataset Preparation

The Olivetti dataset contains 400 grayscale face images from 40 individuals, with 10 images per individual and dimensions of 64x64 pixels.

The BMPD archive contains 812 right-palm captures from 41 subjects. The dataset audit excluded 56 exact decoded-pixel duplicates and five low-contrast palm regions, leaving 751 usable unique captures. Subjects 001 and 021 did not satisfy the fixed second-session sample requirements.

A seeded mapping pairs 39 eligible palmprint subjects with 39 face subjects. These are different physical individuals represented using artificial shared identity labels.

Dataset sources:

- https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_olivetti_faces.html
- https://www.kaggle.com/datasets/mahdieizadpanah/birjand-university-mobile-palmprint-databasebmpd
- https://doi.org/10.1504/IJGUC.2019.102016

## Sample Partitioning

Each simulated identity contributes four enrollment, two validation and four test samples per modality.

Palmprint enrollment and validation use first-session captures. Testing uses second-session captures. Facial samples are partitioned within each identity using random seed 42 because session labels are unavailable.

| Partition | Images per Modality | Purpose |
| --- | ---: | --- |
| Enrollment | 156 | Model fitting and template construction |
| Validation | 78 | Feature selection and score normalization |
| Test | 156 | Independent performance evaluation |

The committed manifests preserve the identity mapping, image hashes, sample partitions and authentication trial definitions.

## Feature Extraction

### Face

Facial features are extracted using PCA with float64 arithmetic, randomized SVD, seed 42 and no whitening. Candidate dimensionalities of 16, 32 and 64 are compared using validation EER.

The selected representation contains 64 principal components. PCA fitting uses enrollment images only.

### Palmprint

Palm images undergo EXIF orientation correction and thumbnail generation with a maximum side length of 512 pixels.

The processing pipeline applies skin segmentation using fixed RGB and chrominance conditions, morphological closing, largest-component selection and hole filling. A distance transform identifies the interior palm region. A conservative grayscale crop is then resized to 128x128 pixels using bilinear interpolation.

HOG and LBP representations are compared using validation performance. The selected HOG configuration contains nine orientations, 16x16 pixels per cell, 2x2 cells per block, L2-Hys normalization and square-root transformation, producing 1,764 features.

The ROI method is heuristic and does not provide explicit anatomical landmark or rotational alignment.

## Enrollment and Authentication

Enrollment feature vectors are L2-normalized and averaged within each simulated identity. The resulting identity templates are normalized again.

Probe features are matched against enrolled templates using cosine similarity. Higher scores indicate stronger similarity. Scores are not calibrated probabilities.

Each paired validation or test probe makes an authentication claim against all 39 enrolled identities. A claim is genuine when the simulated true identity equals the claimed identity.

| Partition | Genuine Claims | Impostor Claims | Total |
| --- | ---: | ---: | ---: |
| Validation | 78 | 2,964 | 3,042 |
| Test | 156 | 5,928 | 6,084 |

All modality scores are joined using trial ID and claimed identity, with ground-truth labels checked for agreement.

## RQ1: Individual Authentication Performance

Face-only and palmprint-only authentication are evaluated using clear images and the fixed test claim protocol.

Feature extraction candidates are selected from validation performance before held-out test scoring. The selected features, enrollment templates and baseline scores are preserved as verified artifacts.

The observed baseline EER values are 8.95749% for face authentication and 23.80229% for palmprint authentication.

## RQ2: Equal-Weight Score-Level Fusion

Each modality is standardized using its validation-score mean and population standard deviation.

The normalization parameters are estimated over all 3,042 validation claims, retaining their genuine and impostor distribution. Test scores do not participate in fitting.

The fusion equation is:

    fusion_score = 0.5 * normalized_face_score + 0.5 * normalized_palm_score

The fitted parameters and equal weights remain fixed. Scores are not clipped.

Fusion achieved a test EER of 7.69231%, improving upon the observed individual modality baselines.

## RQ3: Facial Image Degradation

Gaussian blur is applied to copies of raw facial test probes before PCA transformation.

The evaluated sigma values are 0, 0.5, 1, 2 and 3 pixels in the original 64x64 image space. Filtering uses SciPy Gaussian filtering with reflect boundaries and a truncation value of 4.

Only facial test images change between conditions. Enrollment templates, feature extraction models, claim identities, palmprint scores and normalization parameters remain frozen.

The blur levels were inspected through automated visual review of validation previews before the held-out test sweep. The recorded blur plan preserves the selection procedure.

The implementation verifies sigma-zero equivalence within 1e-12 and exact palmprint score invariance.

## Performance Evaluation

The evaluation module invokes the submitted HW3 numerical evaluator in `src/hw3_evaluator.py` to calculate true/false positive and negative counts, FAR, FRR, TAR and d-prime. Its four numerical methods are preserved with unchanged executable statements. The project supplies all empirical score thresholds rather than the original fixed grid so negative cosine and unbounded normalized fusion scores are covered. Since both score groups must be nonempty, the rate denominators are nonzero; the project handles zero pooled variance separately before calling HW3 d-prime with epsilon zero.

The reported metrics include:

- Equal Error Rate (EER)
- ROC Area Under the Curve (AUC)
- D-prime using pooled score variance
- Genuine and impostor score distributions
- False Acceptance Rate and False Rejection Rate

EER is calculated using linear interpolation at the empirical FAR/FRR crossing rather than the original nearest-grid approximation. The original HW3 source remains unchanged in `docs/hw3_original.py.txt`. The project additionally calculates ROC AUC using exact score rankings. Historical PPA3 evidence and prior experimental results are retained as originally generated.

## Reproducibility

Experiment settings, score tables, model hashes, source hashes and artifact hashes are recorded in the run metadata.

The November 16 integrated verification used Python 3.13.2, NumPy 2.3.2, SciPy 1.16.3, scikit-learn 1.9.1, scikit-image 0.26.0, Matplotlib 3.10.7, Pillow 13.0.0 and joblib 1.6.0.

The experiments were executed on a Windows CPU environment with an AMD Ryzen 9 7940HS processor and approximately 15.2 GiB of RAM.

## Study Limitations

Artificial identity pairing does not establish real-world multimodal identity correlations. Authentication claims sharing probes or identities are dependent.

The study does not establish statistical significance, demographic fairness or production-level security. Exact duplicate detection does not exclude all near-duplicate captures.

The BMPD test partition introduces a session change, while facial session labels are unavailable. Gaussian blur represents controlled image degradation rather than physical motion blur.

BMPD redistribution permission has not been established. Dataset access and storage must remain consistent with applicable usage terms.
