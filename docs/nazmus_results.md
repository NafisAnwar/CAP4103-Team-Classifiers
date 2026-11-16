Historical November 13 results and environment record. These findings were independently reproduced on November 16; see docs/browser_handoff.md, docs/integration_review.md and docs/project_status.md for current integrated status. Pending upload statements below describe the original transfer.

# Nazmus's methods and verified results

## Completion boundary

Nazmus's S1-S5 engineering deliverables are implemented and checked against the
handoff. Real RQ2/RQ3 runs are repeated and their exports independently audited.
The actual palm images were obtained through the original downloader, and all 812
files match original audit hashes. The clean integrated suite passes 55/55 tests.
An independent RQ1 rerun from raw images reproduces PCA64/HOG selection and numerical
results. Source baseline hashes are verified, but the uploaded archive does not
provide a Git commit; branch/commit and human team acceptance occur during upload.
No repository push or coursework submission has been performed.

## Methods for the report

The original study maps 39 face subjects and 39 palm subjects to artificial shared
identities using seed 42. These are different physical people. Each modality has
four enrollment, two validation and four test samples per user. Enrollment models
and original trial manifests are unchanged. There are 3,042 validation claims
(78 genuine, 2,964 impostor) and 6,084 test claims (156 genuine, 5,928 impostor).

For each modality, matching scores were standardized using the mean and population
standard deviation of all its validation claims. The preselected rule uses all
claims without class balancing, so impostor claims dominate the fitting population.
The rule was not selected by comparing test performance. The fitted parameters are:

| Modality | Validation mean | Validation population SD |
| --- | ---: | ---: |
| Face | 0.0049598484789157935 | 0.3142481676894005 |
| Palm | 0.8215842007226275 | 0.06681383122347746 |

For modality m, z_m = (s_m - mean_m) / SD_m. No clipping is applied, and normalized
scores are not probabilities. Parameters are frozen, serialized and reloaded.
Scores are joined by trial_id and claimed_user_id, checking unique complete coverage,
binary labels and finite values. Fusion is exactly 0.5 z_face + 0.5 z_palm.

Evaluation uses the team's existing empirical ROC interpolation for EER, ROC AUC
and pooled-population-variance d-prime. Unimodal metrics are calculated on the original
cosine scores. Positive affine z-score normalization preserves their rankings and
EER/AUC. Original raw score values and all ground-truth labels are preserved.

## Table 1. Clear-image test results (RQ1 and RQ2)

| System | EER (%) | ROC AUC | d-prime | Genuine | Impostor |
| --- | ---: | ---: | ---: | ---: | ---: |
| Face PCA64 | 8.95749 | 0.971356 | 2.828287 | 156 | 5,928 |
| Palm HOG | 23.80229 | 0.846534 | 1.392485 | 156 | 5,928 |
| Equal-weight normalized fusion | 7.69231 | 0.979735 | 2.929388 | 156 | 5,928 |

RQ1 indicates that face authentication has lower EER than palmprint authentication
in this fixed study. RQ2 asks whether adding the weaker palm system can nevertheless
improve the face baseline. Fusion reduced EER by 1.26518 percentage points compared
with face alone and increased both AUC and d-prime. Thus, equal-weight fusion improved
the measured clear-image result on this specific test set. This does not prove
statistical significance, independence of modality errors, or deployment accuracy.

**Figure 1:** `results/figures/rq2_nazmus_final_20261113/rq2_comparison.png` compares
EER, AUC and d-prime. **Figure 2:** `rq2_clear_fusion_scores.png` in the same directory
shows the fusion score distributions. The directory also contains modality-specific
ROC and FAR/FRR plots. `results/metrics/rq2_nazmus_final_20261113/master_metrics.csv`
contains exact numeric values, and `rq2_fusion_scores.csv` preserves every test claim.

## RQ3 methods and results

The improvement observed in RQ2 motivated testing fusion while face quality decreased.
The predeclared Gaussian sigma levels 0, 0.5, 1, 2 and 3 were retained after the
assistant inspected four actual validation faces. Fine detail was progressively
softened; sigma 3 substantially blurred eyes and mouths while retaining overall
face shape. This was an assistant visual review, not a claimed human-team review.
No held-out blur metrics were used to select levels.

SciPy Gaussian filtering used reflect boundaries and truncate=4 on copies of the
original 64x64 [0,1] floating-point face probes before frozen PCA. There was no new
resizing, scaling or fitting. Enrollment, models, claims, palms and normalization
stayed fixed. Sigma zero returned an unchanged pixel copy. Only face test images
were newly scored; palm raw and normalized scores were reused exactly.

### Table 2. EER under facial blur

| Sigma (source pixels) | Face EER (%) | Palm EER (%) | Fusion EER (%) |
| --- | ---: | ---: | ---: |
| 0 | 8.95749 | 23.80229 | 7.69231 |
| 0.5 | 8.97436 | 23.80229 | 7.69231 |
| 1 | 9.09244 | 23.80229 | 7.94534 |
| 2 | 10.27328 | 23.80229 | 8.40081 |
| 3 | 11.08300 | 23.80229 | 9.21053 |

Fusion had lower EER than face-only and palm-only at every tested sigma. At sigma 3,
face-only EER increased to 11.08300%, while fusion EER was 9.21053%. Palm EER stayed
at 23.80229%. Compared with clear faces, the EER increase was 2.12551 percentage
points for face-only and 1.51822 points for fusion. Fusion therefore reduced the
observed degradation but did not remove it. At sigma 3, face/fusion AUC were
0.952923/0.973704, and d-prime were 2.471869/2.762097. No statistical-significance
or general-population robustness claim is made.

**Figure 3:** `results/figures/rq3_nazmus_review_final/rq3_comparison.png` compares
EER, AUC and d-prime across blur levels. The corresponding metrics directory holds
the full 15-row `master_metrics.csv`, all 30,420 keyed score rows, rates, reviewed
plan and provenance. Each condition also has modality ROC/FAR-FRR/distribution plots.

## Verification and reproducibility

All 55 tests passed on the fresh source archive with updates applied and actual assets
restored. No tests were skipped. Original PPA3 regression reproduced AUC 0.7569,
EER 0.2612 and d-prime 1.0973. All 812 raw palm files match their original byte hashes.

The independent raw-data RQ1 run selected PCA64/HOG again. Validation face scores
differed by at most 5.9396931817445875e-15 and test face scores by
6.161737786669619e-15; all palm scores were exact. Face/palm EER and AUC matched
exactly. Face d-prime differed by 1.33e-15. The serialized refitted palm model is
byte-identical; the refitted PCA model is not. Original accepted model files were
not replaced, and RQ3 used those exact accepted model bytes.

Both RQ2 runs matched every score exactly. Both final reviewed RQ3 runs matched all
30,420 score rows exactly and had identical metrics. The saved-score audit validates
all trial keys/labels, score schemas, validation-fitted normalizer parameters,
every fusion equation, unchanged palm values, sigma-zero metrics, and every exported
metric. The combined 20-row study table explicitly labels RQ1, RQ2 and RQ3; repeated
clear-condition rows are not additional independent experiments.

The original PCA was saved with scikit-learn 1.9.1, but execution uses 1.8.0 and
emits InconsistentVersionWarning. Direct scoring with the restored original face
model differs from its saved original scores by at most 1.76e-14. The maximum
sigma-zero normalized/fusion score difference is 4.88e-14. A declared 1e-12 absolute
tolerance accommodates roundoff; original model hashes and palm invariance remain
exact. Original environment reproduction is recommended for serialization identity.

Actual versions are Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, scikit-learn 1.8.0,
scikit-image 0.26.0, Matplotlib 3.10.8, Pillow 13.0.0 and joblib 1.5.3. Dependencies
pass pip check. Source/archive provenance and test logs are in
`results/metrics/nazmus_final_review/`. The final RQ3 run IDs are
`rq3_nazmus_review_final` and `rq3_nazmus_review_repeat`.

## Remaining team steps and limitations

Code, experiments, tables, figures and report-team methods/results notes are ready
for integration. Nazmus must upload/commit the files on his branch and the team must
review the changes and complete its final report/presentation/submission. No human
acceptance or current GitHub commit has been invented from the uploaded ZIP.

Results remain limited by artificial identity pairing, a small population, dependent
claims, exact-only deduplication, palm session shift, heuristic palm ROIs and missing
demographic analysis. No confidence intervals or fairness claims were produced.
Gaussian blur is not motion blur. Retain dataset citations and source-use discussion
from methodology.md. No biometric images or model files are included in the update
ZIP; the validation preview stays local, while its hash and assistant review are
recorded in the saved plan. An optional palm-model improvement was not attempted,
since changing it would change the frozen baseline.
