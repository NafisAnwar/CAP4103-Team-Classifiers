# Planned data contracts

Actual manifests are not created during setup. CSV field names below define the shared interface for N3 and later work.

```text
identity_mapping.csv:
simulated_user_id,face_subject_id,palm_subject_id

partitions.csv:
modality,simulated_user_id,original_subject_id,original_sample_id,palm_hand_if_applicable,session_if_available,split,source_path_or_key

validation_trials.csv and test_trials.csv:
trial_id,simulated_true_user,face_test_sample_id,palm_test_sample_id,claimed_user_id,is_genuine,pair_index

rq1_baseline_scores.csv:
trial_id,claimed_user_id,is_genuine,face_score_raw,palm_score_raw

rq2_fusion_scores.csv:
trial_id,claimed_user_id,is_genuine,face_score_raw,palm_score_raw,face_score_normalized,palm_score_normalized,fusion_score,normalization_version

rq3_blur_scores.csv:
blur_sigma,trial_id,claimed_user_id,is_genuine,face_score_raw,palm_score_raw,face_score_normalized,palm_score_normalized,fusion_score
```

Validation manifests use the same pairing/claim logic as test manifests. Resolve neutral probe field naming during N3 and update both this contract and callers together. Stable keys and ground truth must agree across modalities and conditions; keys must be unique within each split/condition. Genuine means true simulated ID equals claimed simulated ID. Samples must never cross enrollment/validation/test boundaries. All selected users need samples in each partition. Scores must be finite and higher-is-better. Never fuse by incidental array order.
