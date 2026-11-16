# November 16 code and evidence review

## Conclusion

Nazmus's core S1-S5 implementation is accepted for the planned engineering scope after targeted hardening. Validation-only z-score normalization, keyed 50/50 fusion, original frozen models, face-probe-only Gaussian blur, sigma-zero checks and exact palm invariance are implemented. The supplied archive matches every one of the 1,234 files in fetched branch nazmus-fusion-blur at 2c849dd. The source archive contains LFS pointers, so Git LFS retrieval is needed for actual data/models.

## Improvements made

1. tests/test_blur.py copied the whole checkout, including .venv, into a synthetic fixture. The initial local suite exhausted temporary disk space. The fixture now copies only src, locked manifests and hash-verified accepted/parent artifacts. This fixes the failure without deleting user data or weakening the test.
2. experiments/rq3_blur.py verified normalizer identifiers and parent metadata but did not independently refit its parameters at intake. It now compares the frozen normalizer with an actual fit on the accepted validation table before reading held-out images or creating outputs.
3. src/fusion_reporting.py could audit an incomplete or duplicated system summary. It now requires exactly one face, palm and fusion record. Regression tests cover missing and duplicated systems.
4. The reviewed validation preview was absent from the transferred update. A new validation-only plan/preview was generated and visually inspected before the November 16 replay. Both transfer through LFS at data/processed/blur_plans/integration_20261116. Original historical plan hashes/review notes are preserved, not retroactively replaced.
5. Integration instructions still described extracting a ZIP and pending branch upload. Current main docs now describe the integrated repository, verified runs, source/LFS setup and the report/presentation handoff. The updated course sources/templates are retained separately from the numerical study manifests.

The review CLI was already present. An initial review observation incorrectly suggested it was missing because terminal output was truncated; full-file inspection confirmed it, and no replacement CLI was added.

## Verification

All 57 local tests pass, zero skips. Original legacy source/data byte hashes and metrics remain unchanged. All 812 raw palm byte hashes pass. Independent RQ1 enrollment refitting selected PCA64/HOG again and exactly reproduced both original score tables. Fresh RQ2 and RQ3 scores exactly match Nazmus's tables at every sigma. Independent repeat runs match exactly. Saved score/metric audits verify every claim key/label, normalization parameter, fusion equation, condition metric, sigma-zero comparison and palm invariant.

New evidence: results/metrics/main_integration_20261116/. New runs: rq1_main_verified_20261116, rq2_main_verified_20261116, rq2_main_repeat_20261116, rq3_main_verified_20261116 and rq3_main_repeat_20261116. Historical evidence remains intact. The original team environment, including scikit-learn 1.9.1, was used; Nazmus's historical 1.8.0 version caveat remains documented as historical context.

## Remaining limits

This is engineering verification, not a graded report or deployment evaluation. Data are artificially paired and small, claims are dependent, near duplicates are not comprehensively excluded, ROI alignment and demographic analysis are limited, and no confidence intervals/significance analysis were added. BMPD redistribution rights remain unresolved. The browser handoff records the template/current-description bibliography conflict and the need to accurately describe adaptation of the HW3 evaluator.
