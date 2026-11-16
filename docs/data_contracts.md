# Data Contracts

## Identity and Partition Manifests

The dataset manifests define the fixed identity mapping, sample partitions and authentication protocol.

```text
identity_mapping.csv:
simulated_user_id,face_subject_id,palm_subject_id

partitions.csv:
modality,simulated_user_id,original_subject_id,original_sample_id,palm_hand_if_applicable,session_if_available,split,source_path_or_key,pixel_sha256

validation_trials.csv and test_trials.csv:
trial_id,simulated_true_user,face_test_sample_id,palm_test_sample_id,claimed_user_id,is_genuine,pair_index
```

The validation and test manifests use the same claim structure. Existing sample ID column names are retained across both splits to preserve the shared interface.

Each selected sample belongs to exactly one partition. Claims are identified using the trial ID and claimed identity. Ground-truth labels must match across modalities and experimental conditions.

## Authentication Score Schemas

```text
rq1_baseline_scores.csv:
trial_id,claimed_user_id,is_genuine,face_score_raw,palm_score_raw

rq2_fusion_scores.csv:
trial_id,claimed_user_id,is_genuine,face_score_raw,palm_score_raw,face_score_normalized,palm_score_normalized,fusion_score,normalization_version

rq3_blur_scores.csv:
blur_sigma,trial_id,claimed_user_id,is_genuine,face_score_raw,palm_score_raw,face_score_normalized,palm_score_normalized,fusion_score
```

All authentication scores must be finite and use a higher-is-better similarity convention. Score fusion relies on validated claim keys rather than array ordering.

## Protocol Integrity

`data/manifests/protocol_lock.json` records the schema version and hashes of the fixed study manifests.

Protocol loading validates these hashes before performing structural checks. Text hashes normalize line endings, while binary image and model hashes preserve exact bytes.

Dataset audit and protocol preparation commands refuse to replace existing study artifacts unless an explicit rebuild is requested.

## Accepted Baseline

`results/metrics/rq1_accepted.json` identifies the accepted baseline independently of the latest RQ1 run.

The frozen-model loader verifies the accepted manifest hashes, original enrollment sample IDs, model classes, model bytes and relevant feature extraction source files.

The accepted baseline and frozen models must remain unchanged during routine reproduction.

## Normalization and Fusion

The saved `normalizer.json` records the validation normalization parameters, baseline identifier, validation score hash and provenance.

Normalization accepts validation claims only. The implementation verifies complete claim coverage and prevents accidental test-set fitting.

Fusion uses equal weights applied to the normalized modality scores.

## Run Artifacts

Each experiment creates a unique run directory and records its status as running, completed or failed.

Completed run metadata includes source hashes, manifest hashes, artifact hashes, configuration settings and software versions.

Latest-run pointers are updated only after the required artifacts have been successfully verified.

RQ1, RQ2 and RQ3 maintain separate latest-run pointers.

## Blur Conditions

RQ3 requires a verified blur plan, frozen models and a completed RQ2 normalization artifact.

The experiment preserves original facial dimensions, applies blur before feature extraction and holds palmprint scores constant.

Sigma-zero score equivalence and palmprint score invariance are checked during execution.

## Metric Outputs

The master metrics tables identify the experimental condition, blur sigma and biometric system.

EER and AUC values are stored as fractions. Report-ready EER tables convert EER to percentages.

ROC curves, score distributions and FAR/FRR plots are exported with each completed experiment.

## Dataset and Model Availability

Git LFS pointers are not usable image or model files. Actual dataset and model bytes must be available before running experiments that depend on them.
