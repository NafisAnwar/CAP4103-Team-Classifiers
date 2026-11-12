# CAP4103 engineering handoff for Nazmus Sakeeb

Prepared November 12, 2026. Project: Combining Face and Palmprint Scores for Authentication Under Image Blur. Working editor: VS Code. Branch: nafis-foundation. Verified source checkpoint before final document cleanup: df14796fa20bd3e0878417a6df9c62590d357027. The Desktop copies include the final cleanup commit after it is saved.

## Completion and ownership

Nafis's N1-N7 implementation is complete: 60 of 60 assigned engineering effort units. Nazmus owns S1-S5, the remaining 40 of the 100 planned coding effort units. This is an engineering estimate, not a grade or percentage of the entire group submission. Report, presentation and teammate acceptance remain separate gates. Diego leads research/methodology, Mikaela results/report, and Sienah presentation/ethics/references/QA.

Nafis delivered the preserved PPA3 regression; environment and acquisition tools; image audit and duplicate exclusion; fixed identity/split/claim protocol; both initial face and palm systems; generic evaluation; measured RQ1; frozen models, raw scores, plots, repeatability evidence and tests. The follow-up structure improvements protect manifests, isolate legacy tests, share verified loading/scoring, label future fusion scores correctly and track run completion/provenance.

## Start here

The local project is C:/Users/anwar/Desktop/CAP4103 - Mobile Biometrics/CAP4103 - Course Project/CAP4103-Biometric-Fusion. Open CAP4103-Biometric-Fusion.code-workspace. On another computer use your checkout root. Read docs/project_status.md, docs/data_contracts.md, docs/methodology.md and docs/developer_roadmap.md.

Use the project .venv interpreter. Current Python is 3.13.2; all dependency versions are in requirements-lock.txt. No remote is configured. Before work, verify the agreed commit and keep a separate branch for Nazmus's changes. Obtain team agreement on the handoff rather than assuming acceptance from the filename rq1_accepted.json.

Existing local environment, from the project root:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B scripts/verify_legacy.py
.\.venv\Scripts\python.exe -B experiments/rq1_baseline.py
```

Fresh checkout:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe scripts/download_data.py
.\.venv\Scripts\python.exe -B experiments/rq1_baseline.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Keep the committed manifests and protocol lock when reproducing. Audit/build commands reject existing manifests; --rebuild is only for an intentional study revision. Do not overwrite the accepted study to make a check pass. Runs refuse existing IDs across metrics, figures and model folders. scripts/verify_legacy.py uses temporary copies; --export explicitly replaces historical evidence.

## Fixed data and protocol

Olivetti: 400 grayscale 64x64 images from 40 subjects. BMPD download: 812 right-palm images from 41 subjects, 56 exact decoded-pixel duplicates and five low-contrast ROIs excluded, leaving 751 usable unique images. Subjects 001 and 021 lack the required distinct second-session samples. Seed 42 maps 39 eligible palm subjects to 39 face subjects under artificial shared user IDs. These are different physical people across modalities.

Each user/modality has 4 enrollment, 2 validation and 4 test images. Palm enrollment/validation use F session; test uses S. Face session tags are unavailable. Validation contains 3,042 claims (78 genuine, 2,964 impostor); test contains 6,084 (156 genuine, 5,928 impostor). No sample/pixel duplicates cross splits. The heuristic palm ROI lacks anatomical and rotation alignment; do not change it during the frozen blur study.

data/manifests/protocol_lock.json pins nine audit/protocol manifests. Text hashes normalize line endings only; model/image hashes require exact bytes. The accepted reference separately pins original metadata, manifests and score contents. A rebuilt lock cannot authorize using old models with changed data.

## RQ1 evidence to reproduce

Original accepted Nafis baseline: rq1_20261112T151158Z_e192d8. Latest verified reproduction: rq1_structure_verified_20261112. Discover the original through results/metrics/rq1_accepted.json and latest through rq1_latest.json.

Face: PCA64 selected on validation from 16/32/64, no whitening, enrollment-only fit; EER 0.0895748987854251 (8.95749%), AUC 0.9713560590331846, d-prime 2.8282872066476727.

Palm: HOG selected over LBP on validation; EER 0.2380229419703104 (23.80229%), AUC 0.8465344821620125, d-prime 1.3924850785225091.

Both systems average unit enrollment vectors per identity, normalize the template and use higher-is-better cosine similarity. EER uses the linearly interpolated empirical ROC crossing. Original PPA3 landmark-only AUC/EER/d-prime are 0.7569/0.2612/1.0973, using its older threshold-grid method; those are not the image-system results.

Each run's results/metrics/<run-id> contains validation_scores.csv, rq1_baseline_scores.csv, selection, summary, rates and run_metadata.json. Figures are under results/figures/<run-id>. Frozen local models are under data/processed/models/<run-id> and are not committed. Raw images, contact sheets, virtual environments and private reference documents are also excluded from Git.

Read structure_improvements_verification.json/.txt and fresh_checkout_verification.json/.txt under results/metrics. The full local suite passed all 33 tests; a fresh Git archive passed its 31 available checks with two model/data checks skipped. All raw validation/test scores and both model files reproduced exactly in the locked local environment. Other hardware/library versions may differ; investigate discrepancies rather than bypassing integrity checks.

## Shared interfaces

src.datasets.dataset_images loads a requested split, verifies audited decoded-pixel hashes and applies the existing palm crop. src.experiment_support.enroll fits only enrollment; score_and_evaluate uses keyed claims. load_frozen_models() verifies the accepted metadata, manifests, feature/matching implementation, scores, model bytes, identity ordering and enrollment IDs.

For a fresh reproduction, call load_frozen_models(model_run_id='<your-new-run-id>') from src.experiment_support. Its models must still match the original accepted byte hashes. Missing ignored raw data/models is expected on a fresh checkout; download and reproduce locally.

The trial fields face_test_sample_id and palm_test_sample_id are retained for BOTH validation and test. Score-row keys are trial_id plus claimed_user_id. Verify unique complete keys and matching is_genuine labels before joining. Never fuse arrays by incidental row order. Scores must be finite and higher-is-better. See docs/data_contracts.md for the exact CSV schemas.

Evaluator/evaluate_labeled accept score_type and score_label. Set those descriptions for normalized or fusion scores so plots do not call them cosine similarities. Keep one EER method across all new conditions. Only consume completed runs; a forcibly terminated process may leave running status. The latest pointer is published only after successful artifact checks.

## Nazmus's remaining work in order

1. S1, 10 units: reproduce the accepted handoff and agree on the baseline. Fit and document normalization using validation scores only; save its fitted parameters/version and input hashes. Choose the normalization rule using validation, freeze it and apply it unchanged to held-out scores. Compute exactly 0.5 * normalized_face + 0.5 * normalized_palm. Measure RQ2 against both unimodal systems using the same test claims. Improvement, deterioration or a tie are all valid findings.

2. S2, 10 units: predeclare and visually inspect Gaussian blur levels using suitable validation examples. Blur only raw held-out face probe pixels, on the existing [0,1] scale, before the frozen face transform. Keep enrollment, models, palm probes/scores, trial mapping and fitted normalizers unchanged. Include sigma zero, which must reproduce the unblurred RQ2 scores/metrics. Record sigma units, boundary mode, implementation and preprocessing order. Gaussian blur models lost sharpness, not physical motion blur.

3. S3, 8 units: export the checked RQ2/RQ3 score schemas, a master metrics table and publication figures with unique run/condition names. Include face, palm and fusion comparisons, blur severity, EER, AUC, d-prime and trial counts. Keep original RQ1 evidence intact.

4. S4, 7 units: test validation-only normalizer fitting, frozen parameters, exact keyed coverage/labels, equal weights, finite scores, sigma-zero equivalence, unchanged palm scores/EER and model non-refitting. Reproduce runs and compare every score. Any separate palm improvement must be selected on validation and evaluated as a new experiment, without silently changing the frozen baseline. Do not tune against the already observed test EER.

5. S5, 5 units: provide verified methods/results and figure/table references to the report/presentation team. Document limitations and negative findings. Finish dependency, provenance and reproducibility checks. Follow the user's no-README/no-placeholder-file preference; update the existing methods/status notes instead.

Suggested implementation locations: src/fusion.py, src/blur.py, experiments/rq2_fusion.py, experiments/rq3_blur.py and corresponding focused tests, created when implemented. These are proposed next files, not claims that they already exist.

## Constraints and unresolved items

BMPD is course-preapproved and publicly accessible, but Kaggle's license metadata is Unknown; redistribution permission is not established. Keep images/contact sheets/models local and resolve terms before distributing images. Artificial identities, exact-only deduplication, small subject count, heuristic ROI, session shift and no demographic analysis limit the conclusions.

Preserve the five original PPA3 source/data/requirements files byte-for-byte. Keep seed 42. Use useful informal lowercase inline comments with no space after #. Do not commit environments, secrets, images or private source documents. No team messages, push, merge or submission has been authorized here.

The supplied course PDF limits the report to five pages including visuals, excluding references; Arial/Calibri 11, one-inch margins, single spaced/justified, numbered pages/figures/tables and 14-point title/headings. Ethics is at most three paragraphs with at least three credible citations. Verify any later instructor changes directly. Due date, presentation rubric, remote/sharing links and source usage terms remain unresolved. Coding completion alone does not complete these group deliverables.
