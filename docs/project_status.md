# Current project integration status

Nazmus's S1-S5 implementation and engineering evidence are ready for repository
integration. RQ2 and real RQ3 have both been measured and repeated. Independent
raw-image RQ1 reproduction selected PCA64/HOG again and reproduced EER/AUC exactly;
palm scores matched exactly and face-score roundoff was below 6.2e-15.

A fresh source-plus-update integration passed all 55 tests, with no failures/skips.
The original 812 palm-image hashes, accepted model hashes, manifests, core model
source and RQ1 evidence remain intact. The local cross-version PCA refit is not
byte-identical; RQ3 uses the original accepted model bytes, with sigma-zero score
agreement checked within 1e-12. No integrity hashes were weakened.

See docs/nazmus_readiness.md, docs/nazmus_results.md and
results/metrics/nazmus_final_review/ for current evidence. RQ2 fusion EER is 7.69231%;
at sigma 3 it is 9.21053% versus face-only 11.08300%. All other conditions and metrics
are in the combined study table.

Pending human/team actions: branch upload and commit, review/acceptance, final group
report and presentation assembly, and course submission. The uploaded archive has
no Git history; current GitHub branch contents/commit were not independently verified.
