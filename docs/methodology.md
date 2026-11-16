# Implemented RQ1 methodology

This is the implemented Nafis baseline, not a description of future fusion/blur work.

## Sources and audit

The October 15 course PDF lists Olivetti and BMPD as preapproved datasets. Olivetti is loaded through [scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_olivetti_faces.html): 400 original 64x64 grayscale images, 40 subjects, 10 images each. The downloaded array contains no exact decoded-pixel duplicates.

BMPD is downloaded from the [creator's public Kaggle listing](https://www.kaggle.com/datasets/mahdieizadpanah/birjand-university-mobile-palmprint-databasebmpd). The archive actually contains 1,612 entries, including 812 explicitly named right-palm images from 41 subjects. The listing's description says 1,640 images; its capture counts also do not fully match the archive. Actual filenames, CRC-verified bytes, decoded pixels and session labels govern this implementation. F and S are treated as first/second session tokens. No left palms enter the experiment.

The decoded-pixel audit identified 56 exact duplicate right-palm images and five additional images whose final 128x128 palm ROI standard deviation is below 0.02. After these exclusions 751 unique usable right-palm images remain. No cross-subject exact pixel duplicates were found. Exact deduplication does not establish the absence of near-duplicate acquisitions.

Kaggle's license field is Unknown. Public download and course preapproval are documented; redistribution permission has not been established. Raw images, ROI contact sheets and frozen feature/model files were originally kept local. An optional Git LFS upload workflow is now documented, but sharing still requires permitted source usage terms. Before publication or sharing images, the team must resolve source usage terms. Source article: Izadpanahkakhk et al., Novel mobile palmprint databases for biometric authentication, 2019, [DOI](https://doi.org/10.1504/IJGUC.2019.102016).

## Palm preprocessing

Visual inspection rejected a fixed center crop because it often included fingers/background. The final method converts EXIF-oriented RGB images to a thumbnail with maximum side 512, segments skin using R>0.12, Cr>0.53, R>G and R>B, closes small gaps, retains the largest component and fills internal holes. Its maximum distance-transform location defines the palm center. A conservative square whose side equals that distance is cropped from the full-resolution grayscale image and bilinearly resized to 128x128. Minimum source crop side is 64 pixels. The algorithm is fixed across all subjects/splits.

Five contact sheets with representative first/second-session captures and crops covering all available subjects were reviewed before fitting. This is a heuristic interior crop, without anatomical landmarks or explicit rotation alignment. Variable pose, shadows and occasional edge background remain limitations. It should not be described as a validated anatomical ROI detector or an exhaustive manual review of every capture.

## Shared identity and claim protocol

Seed 42 selects/maps distinct source identities under explicitly artificial shared labels. These face and palm captures are from different physical people. Subjects 001 and 021 lack the required distinct second-session palm captures, leaving 39 eligible palm subjects paired with 39 of the 40 Olivetti subjects. The mapping is persisted, not regenerated during experiment execution.

Each modality/user has four enrollment, two validation and four test samples. Palms use only F-session images for enrollment/validation and only S-session images for testing. Face session labels are unavailable, so their samples use a seeded within-user split. Every selected decoded image and sample ID occurs in just one partition. Enrollment/validation share a palm session, so validation quality does not fully characterize the cross-session test shift.

Each validation/test face probe is paired with a same-simulated-user palm probe, then compared against all 39 claimed identities. Validation: 78 genuine and 2,964 impostor claims (3,042 total). Test: 156 genuine and 5,928 impostor claims (6,084 total). Ground truth is true simulated ID equals claimed simulated ID. CSV rows use unique trial_id plus claimed_user_id keys. Modality joins validate keys and labels; they never rely on incidental row order.

## Features, fitting and validation selection

Face PCA is fit on the 156 enrollment images only, with float64 arithmetic, randomized SVD, seed 42 and no whitening. Candidate component counts are 16, 32 and 64. Palm candidates are HOG (9 orientations, 16x16 pixels/cell, 2x2 cells/block, L2-Hys, square-root transform, 1,764 features) and uniform LBP (16 neighbors, radius 2, 4x4 spatial histograms with 18 bins each and square-root normalization, 288 features).

For each modality, each enrollment feature vector is L2-normalized, vectors are averaged within identity, then templates are L2-normalized. Probe-template cosine similarity is finite and higher-is-better. Similarities are not calibrated probabilities. Candidates are chosen by the lowest validation EER with positive genuine/impostor mean direction. Ties use the first candidate. Within the RQ1 runner, no test image is loaded or scored until those choices are frozen. The prior dataset audit decodes images for quality and duplicate checks, without model fitting or EER-guided preprocessing. The executed run selected 64 face components and HOG palms.

## Evaluation and reproduction

The new evaluator extends PPA3's genuine/impostor labeling, pooled-variance d-prime and FAR/FRR/ROC structure while removing probability-range and Caltech-only plot assumptions. Final EER is the linearly interpolated FAR=FRR crossing on the empirical ROC with all distinct thresholds retained. AUC uses the same score direction. It is explicitly different from legacy PPA3's nearest point on a 500-threshold grid. Tied/discrete scores can yield an interpolated EER that no single deterministic threshold attains. Zero-variance d-prime is null for separated constants and zero for identical constants.

Each experiment writes a unique metrics/figures directory and refuses to overwrite an existing run ID. Outputs include paired raw validation/test scores, validation model comparisons, ROC and FAR/FRR curves, score distributions, summary metrics, manifest/source hashes, fit sample IDs and package versions. Local joblib files freeze the chosen enrollment models for Sakeeb's intake and blur experiments. Only load these self-generated, hash-verified joblib files; they are not general untrusted model inputs.

Results are descriptive for this small selected population. No uncertainty interval, broad demographic fairness or deployable accuracy claim is made. RQ2 must assess whether equal-weight fusion helps rather than assume it; RQ3 must preserve the mapping, manifests, models, enrollment and validation-trained normalizers while blurring only raw face test probes. Neither RQ2 nor RQ3 was implemented in the original RQ1 scope; Nazmus's extension is documented below.

From the VS Code project-root terminal:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe experiments/rq1_baseline.py
```

On another checkout, create Python 3.13 .venv, install requirements-lock.txt and run scripts/download_data.py. Keep the committed manifests and protocol_lock.json for reproduction; the experiment verifies their bytes and the decoded source images. Audit/build commands are for a new study or an intentional revision and refuse existing manifests by default. Use scripts/audit_data.py --rebuild followed by scripts/build_protocol.py --rebuild only when intentionally replacing the study. Review changes before accepting any new baseline.

The refactored RQ1 uses shared verified image loading and enrollment/scoring helpers. Models, matching, preprocessing, candidates and numerical evaluation are unchanged. Evaluator score descriptions can be supplied by later normalized/fusion callers. The accepted baseline pointer pins metadata and score hashes separately from latest-run discovery; the frozen loader also checks the feature/matching source, enrollment IDs and model bytes.

New runs capture provenance before work, record running/completed/failed status, recheck input hashes at completion and hash required artifacts. JSON writes replace files atomically. A forced termination may leave running status, so only completed runs should be consumed. The regular legacy check runs byte-identical copies in a temporary directory and leaves saved project evidence untouched; scripts/verify_legacy.py --export explicitly replaces that evidence.

## Nazmus RQ2/RQ3 extension

RQ2 retains the accepted 39-user mapping and all 6,084 test claims. Each modality
is standardized using the mean and population standard deviation over its 3,042
validation claim scores, including 78 genuine and 2,964 impostor claims. The
imbalance is deliberately retained and disclosed. No test scores select the rule,
weights, means or standard deviations. Scores are unbounded and not probabilities.
Keyed, label-checked fusion is exactly half face z-score plus half palm z-score.
The fitted parameters and source hashes are saved and reloaded before use.

RQ2 is executed from hash-verified accepted score CSVs, not newly acquired images.
Face/palm metrics match the accepted RQ1 metrics. Fusion EER is 7.69231%, compared
with face 8.95749% and palm 23.80229%. The paired descriptive improvement motivates
RQ3; it does not establish significance or robustness under blur.

RQ3 implementation proposes sigma 0, 0.5, 1, 2 and 3 source pixels. A validation-only
preview and explicit inspection record precede the held-out sweep. Gaussian filtering
uses SciPy, reflect boundaries and truncate=4, preserving original 64x64 [0,1]
face arrays and dtype. Sigma zero returns an unchanged copy. Filtering precedes
the frozen PCA transform. Enrollment, models, palm images/scores, claims and
normalizers remain fixed. No fit method is called. The runner checks model-state
hashes, input arrays, exact sigma-zero score equivalence and invariant palm scores
and metrics. It recomputes saved metrics from exported score CSVs.

Actual RQ3 was subsequently executed twice after the real Olivetti NPZ and accepted
face/palm model bytes were restored and hash-verified. The assistant inspected the
validation preview before held-out scoring. Fusion EER at sigmas 0/0.5/1/2/3 was
7.69231/7.69231/7.94534/8.40081/9.21053 percent. Palm EER stayed 23.80229 percent.
The two runs matched every score exactly. Sigma-zero comparison with historical RQ2
allows 1e-12 absolute roundoff (observed maximum 4.88e-14), preserving strict model
hashes. Independent raw-palm/RQ1 reproduction subsequently passed numerically; see the final review evidence. See nazmus_results.md for the actual
library-version warning, validation checks and limitations.


## November 16 integration verification

All three questions were independently executed in the original Python 3.13.2/scikit-learn 1.9.1 environment. RQ1 enrollment refitting exactly reproduced both original score tables; RQ2 and all RQ3 levels exactly reproduced Nazmus's tables and each new repeat. All 57 local tests and all 812 raw palm hashes pass. The new plan/preview is retained with actual source-input hashes. See docs/browser_handoff.md and results/metrics/main_integration_20261116 for current environment, methods, quantitative answers, limitations and report guidance. Historical cross-version verification details above remain historical evidence.
