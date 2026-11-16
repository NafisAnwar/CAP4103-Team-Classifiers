Current update: all planned N1-N7 and S1-S5 engineering work is now implemented and verified. Independent review is in docs/integration_review.md; human team acceptance and report/presentation/submission are still separate. This roadmap retains the original phase allocation.

# Developer roadmap and gates

Detailed source plan: `reference/CAP4103_PPA3_Extension_Implementation_Plan.txt`. Nafis's implementation checklist is complete locally; Nazmus's engineering implementation and numerical reproduction are complete; human team acceptance remains separate. docs/project_status.md is the authoritative current progress record.

| Phase | Units | Deliverable and gate |
| --- | ---: | --- |
| N1 | 10 | Unchanged legacy run, clean environment/repository and setup evidence |
| N2 | 8 | Dataset provenance audited; counts, identities, sides, sessions, exclusions and unresolved BMPD rights recorded |
| N3 | 10 | Deterministic artificial mapping, leak-free enrollment/validation/test partitions, paired claim manifests |
| N4 | 12 | Enrollment-fit PCA face pipeline, stable class ordering, finite claimed-ID scores |
| N5 | 10 | Verified right-palm parser/ROI/features and scores for every shared claim |
| N6 | 6 | Generic evaluator derived from PPA3, truthful labels, named outputs, consistent EER method |
| N7 | 4 | Actual RQ1 metrics/score CSVs/plots, tests, exact-commit handoff |
| S1 | 10 | Reproduce handoff, validation-only normalization, keyed 50/50 fusion and measured RQ2 |
| S2 | 10 | Frozen-model facial-probe Gaussian blur and measured RQ3 |
| S3 | 8 | Consistent master metrics and uniquely named publication figures |
| S4 | 7 | Integrity tests, repeatability audit, validation-only palm improvements |
| S5 | 5 | Final methods/results notes and report/presentation evidence package; maintain the requested root README |

Nafis implements N1-N7 before transfer (60 units). Sakeeb implements S1-S5 after accepting the tested handoff (40 units). One unit is an effort estimate, not a percentage of the course grade.

## Nafis handoff checklist

- [x] Original legacy metrics reproduced in the local Nafis environment.
- [x] Dataset provenance, access instructions and actual exclusions recorded, including unresolved BMPD rights.
- [x] Real identity/split/validation/test-trial manifests saved and checked for leakage.
- [x] Both modalities emit finite higher-is-better scores for the same keys/labels.
- [x] RQ1 script executes and saves measured scores, metrics, and labeled plots.
- [x] Relevant automated checks and reproduction commands pass locally.
- [x] Branch/implementation commits, versions, unresolved issues and commands recorded in nazmus_handoff.md.

## Sakeeb intake and completion checklist

- [x] Reproduce PPA3 and RQ1 from the hash-verified source/archive and raw images. Original archive limitations are historical; fetched branch 2c849dd and the original team environment are now independently verified.
- [x] Join unique trial/claim keys and assert label agreement.
- [x] Implement validation-only fitting and frozen parameters; execute RQ2.
- [x] Compute equal-weight fusion and measure RQ2 from verified accepted scores.
- [x] Predeclare and inspect validation blur levels; blur real face test pixels only.
- [x] Measure and repeat RQ3 with identical palms, trials, enrollment, models and normalizers.
- [x] Verify sigma-zero within 1e-12 and exact palm invariance on real runs.
- [x] Export checked master metrics/figures and document findings/limitations.
- [x] Complete clean-integration QA and prepare verified methods/results for the report team.

Current integration evidence is in docs/integration_review.md and results/metrics/main_integration_20261116. Raw-palm integrity, RQ1 refitting and real RQ3 are independently verified in the original environment. The browser handoff identifies remaining human report/presentation/acceptance steps; the delivery record confirms the final main upload.
