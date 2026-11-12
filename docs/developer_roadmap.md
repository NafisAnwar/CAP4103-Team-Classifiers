# Developer roadmap and gates

Detailed source plan: `reference/CAP4103_PPA3_Extension_Implementation_Plan.txt`. This checklist tracks future work, rather than claiming it is implemented.

| Phase | Units | Deliverable and gate |
| --- | ---: | --- |
| N1 | 10 | Unchanged legacy run, clean environment/repository and setup evidence |
| N2 | 8 | Permitted datasets audited; counts, identities, sides, sessions and exclusions recorded |
| N3 | 10 | Deterministic artificial mapping, leak-free enrollment/validation/test partitions, paired claim manifests |
| N4 | 12 | Enrollment-fit PCA face pipeline, stable class ordering, finite claimed-ID scores |
| N5 | 10 | Verified right-palm parser/ROI/features and scores for every shared claim |
| N6 | 6 | Generic evaluator derived from PPA3, truthful labels, named outputs, consistent EER method |
| N7 | 4 | Actual RQ1 metrics/score CSVs/plots, tests, exact-commit handoff |
| S1 | 10 | Reproduce handoff, validation-only normalization, keyed 50/50 fusion and measured RQ2 |
| S2 | 10 | Frozen-model facial-probe Gaussian blur and measured RQ3 |
| S3 | 8 | Consistent master metrics and uniquely named publication figures |
| S4 | 7 | Integrity tests, repeatability audit, validation-only palm improvements |
| S5 | 5 | Final README/methods/results and report/presentation evidence package |

Nafis implements N1-N7 before transfer (60 units). Sakeeb implements S1-S5 after accepting the tested handoff (40 units). One unit is an effort estimate, not a percentage of the course grade.

## Nafis handoff checklist

- [ ] Original legacy metrics reproduced in the handoff environment.
- [ ] Dataset provenance, access instructions and actual exclusions recorded.
- [ ] Real identity/split/validation/test-trial manifests saved and checked for leakage.
- [ ] Both modalities emit finite higher-is-better scores for the same keys/labels.
- [ ] RQ1 script executes and saves measured scores, metrics, and labeled plots.
- [ ] Relevant automated checks and reproduction commands pass.
- [ ] Exact branch/commit, versions, unresolved issues and commands recorded in nafis_handoff.md.

## Sakeeb intake and completion checklist

- [ ] Reproduce PPA3 and RQ1 at Nafis's exact accepted commit before fusion work.
- [ ] Join unique trial/claim keys and assert label agreement.
- [ ] Fit normalization on validation only; keep it frozen for all held-out conditions.
- [ ] Compute exactly equal-weight fusion, then measure RQ2.
- [ ] Predeclare visually inspected blur levels; blur face test pixels only.
- [ ] Measure RQ3 with identical palms, trials, enrollment, models and normalizers.
- [ ] Assert sigma-zero equivalence and invariant palm scores/EER.
- [ ] Export checked master metrics/figures; document negative findings and limitations.
- [ ] Complete final QA and provide verified methods/results to the report team.
