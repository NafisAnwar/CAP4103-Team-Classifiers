# Implemented and future data contracts

The identity, partition, trial and RQ1 score manifests below are implemented. RQ2/RQ3 score schemas are reserved for Sakeeb's later phase.

```text
identity_mapping.csv:
simulated_user_id,face_subject_id,palm_subject_id

partitions.csv:
modality,simulated_user_id,original_subject_id,original_sample_id,palm_hand_if_applicable,session_if_available,split,source_path_or_key,pixel_sha256

validation_trials.csv and test_trials.csv:
trial_id,simulated_true_user,face_test_sample_id,palm_test_sample_id,claimed_user_id,is_genuine,pair_index

rq1_baseline_scores.csv:
trial_id,claimed_user_id,is_genuine,face_score_raw,palm_score_raw

rq2_fusion_scores.csv:
trial_id,claimed_user_id,is_genuine,face_score_raw,palm_score_raw,face_score_normalized,palm_score_normalized,fusion_score,normalization_version

rq3_blur_scores.csv:
blur_sigma,trial_id,claimed_user_id,is_genuine,face_score_raw,palm_score_raw,face_score_normalized,palm_score_normalized,fusion_score
```

Validation manifests use the same pairing/claim logic as test manifests. The existing face_test_sample_id and palm_test_sample_id column names are intentionally retained for both splits to keep the shared interface stable. Stable keys and ground truth must agree across modalities and conditions; keys must be unique within each split/condition. Genuine means true simulated ID equals claimed simulated ID. Samples must never cross enrollment/validation/test boundaries. All selected users need samples in each partition. Scores must be finite and higher-is-better. Never fuse by incidental array order.

data/manifests/protocol_lock.json stores schema_version, hash_format and manifest_sha256 for the nine required audit/protocol manifests. load_protocol verifies the hashes before performing structural checks. Text hashes normalize CRLF or CR to LF, preserving all other bytes, so Git line-ending conversion does not invalidate a fresh checkout. Image/model hashes remain exact bytes. Audit and protocol commands refuse existing outputs without --rebuild. An intentional audit revision requires a subsequent explicit protocol rebuild; old frozen models still reject the changed study even if the new lock is internally valid.

results/metrics/rq1_accepted.json pins the verified Nafis baseline independently of rq1_latest.json. It records run_id, hash_format, normalized manifest/metadata/validation/test text hashes and the acceptance scope. The historical metadata keeps its original Windows byte hashes. It does not claim Sakeeb has accepted the handoff. load_frozen_models verifies this reference, the accepted manifests, model feature/matching source bytes, model hashes, classes and enrollment sample IDs. On a fresh checkout, pass model_run_id from a new reproduction to load its files; their bytes must still match the accepted model hashes. Keep the accepted reference under review when intentionally changing a study.

src.datasets.dataset_images performs the audited pixel-hash checks and the unchanged palm crop for a requested split. src.experiment_support provides enrollment, keyed scoring/evaluation, frozen model loading, and run artifact management. Evaluator and evaluate_labeled accept score_type and score_label for higher-is-better normalized/fusion scores; cosine defaults preserve RQ1 descriptions.

New runs record run_status.json with running/completed/failed state and starting provenance. A process killed before cleanup can retain running state, which must be treated as incomplete. Completed metadata records source/manifest/model/artifact hashes and versions. Input hashes are checked again at completion; latest is replaced atomically only after required artifacts exist. Failed run IDs remain reserved for inspection.
