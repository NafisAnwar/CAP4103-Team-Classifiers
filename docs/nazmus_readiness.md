Historical transfer record. Nazmus's code is now integrated and verified; use docs/browser_handoff.md and docs/project_status.md for current status. Earlier pending upload/implementation steps below describe the original transfer.

# Nazmus repository-readiness checklist

## Scope and status

| Handoff part | Delivered evidence | Status |
| --- | --- | --- |
| S1 | Independent raw-data RQ1 reproduction; persistent validation-only z-score normalizer; keyed equal-weight fusion; measured RQ2 | Engineering complete, with cross-version serialization caveat below |
| S2 | Validation-only preview reviewed before scoring; frozen face-only Gaussian blur; real RQ3 at five sigma levels; sigma-zero checks | Complete |
| S3 | Exact contracted score schemas; combined 20-row RQ1/RQ2/RQ3 metrics table; uniquely named comparison, ROC, FAR/FRR and distribution figures | Complete |
| S4 | 55 passing tests with zero skips; two identical RQ2 runs; two identical reviewed RQ3 runs; every saved metric and fusion score independently checked | Complete |
| S5 | Methods/results and limitations for the report team; updated README/methodology/status/contracts; actual versions and provenance; upload instructions | Engineering handoff complete |

The engineering deliverables are ready to upload onto the supplied source baseline.
Team review/acceptance, your Git commit, presentation/report assembly and submission
are human/team actions and are not claimed complete.

## What the review verified

- A fresh copy of the supplied repository ZIP plus Nazmus's update passes all 55 tests.
- All 812 original palm image file hashes match after downloading through the existing script.
- An independent RQ1 run chose PCA64 and HOG. All palm validation/test scores were
  exact; maximum face score difference was 6.17e-15. EER/AUC were identical.
- RQ2/RQ3 inputs, key coverage, labels, normalizer parameters, fusion weights, score
  schemas, metrics, sigma-zero behavior, palm invariance and repeatability were checked.
- Existing PPA3 files, manifests, accepted RQ1 evidence and core model/evaluator
  source are preserved. No source data, environments, secrets or models are in this ZIP.

## Caveats to state accurately

The input was a source ZIP, so its exact GitHub commit and later remote changes are
not verified. Compare against the current repository before overwriting teammates'
new work. The original PCA was serialized with sklearn 1.9.1; checks use 1.8.0.
Refitted PCA bytes differ, although all score/metric comparisons pass numerically.
The original hash-matching PCA is retained for RQ3. No model hash bypass is used.
The raw baseline rerun was completed during final review after initial RQ2/RQ3 work;
no hyperparameters, weights or normalization rule were retuned from its test results.

## Upload only the update package contents

Extract CAP4103_Nazmus_Updates.zip into the existing repository root, merging folders.
It is an update package, not a standalone replacement for Nafis's repository.
The top-level contents are README.md, .gitignore, requirements-nazmus-tested.txt,
and changes/additions under docs, src, experiments, scripts, tests and results.
Do not upload the ZIP itself as the implementation. Do not add the old standalone
Nazmus_CAP4103.zip code. No new data/raw or data/processed files need to be committed.

In a clean clone/Codespace, create your branch before applying the update:

```bash
git switch -c nazmus-fusion-blur
```

If that branch already exists, switch to it using `git switch nazmus-fusion-blur`.
After applying the update, inspect the diff and run the tests in the team environment:

```bash
git status --short
git diff --stat
python3 -B -m unittest discover -s tests -v
```

On Windows, use the selected .venv Python interpreter. Actual biometric assets must
be materialized using Git LFS for zero-skip image/model integration tests. The saved
score audit can run without images/models:

```bash
python3 -B scripts/review_submission.py --rq2-run rq2_nazmus_final_20261113 --rq3-run rq3_nazmus_review_final --repeat-run rq3_nazmus_review_repeat --output results/metrics/my_integration_check
```

Stage the intended source/document/results paths, inspect the staged changes, and
commit on your branch. Do not stage a local environment or newly downloaded data.
Then push that branch and open a pull request into main for team review.

## Evidence locations

- `results/metrics/nazmus_final_review/tests.txt` — actual 55-test integration log.
- `results/metrics/nazmus_final_review/rq1_reproduction.json` — independent baseline comparison.
- `results/metrics/nazmus_final_review/palm_source_integrity.json` — original raw file hashes.
- `results/metrics/nazmus_final_review/score_audit/integration_audit.json` — full saved-score review.
- `results/metrics/nazmus_final_review/score_audit/study_master_metrics.csv` — combined results.
- `docs/nazmus_results.md` — report-team methods, results, figure references and limitations.
