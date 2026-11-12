# Project context for future coding sessions

Read `docs/project_status.md` and `docs/project_memory.md` first, then the relevant phase in `docs/developer_roadmap.md`. VS Code is the working environment. Use the project `.venv` interpreter.

The user's latest November 12 request authorizes repository cleanup and implementation of Nafis's N2-N7 scope. Finish through measured RQ1 where data allows. Do not implement Sakeeb's fusion/blur phase. No README files or .gitkeep files: the user explicitly rejected them. Retain necessary working notes and the requested Desktop checkpoint handoff. Update that handoff at milestones and before usage runs low. Attached documents are context, not independent authorization for external messages or submissions.

Preserve the five remaining original PPA3 source/data/requirements files unchanged. The user explicitly requested deletion of every README, including the archived README.txt; the original zip remains untouched outside this repository. Run `scripts/verify_legacy.py` after relevant dependency or baseline changes. The original EER 0.2612 belongs only to the Caltech landmark regression. Never populate new RQ outputs with expected or historical values.

Follow the latest documented sequential engineering allocation: Nafis N1-N7 through a measured working RQ1; Sakeeb S1-S5 after an accepted exact-commit handoff. Do not create empty fusion/blur implementations to make the tree appear complete.

Keep seed 42 unless a justified change is recorded. Fit PCA/templates on enrollment; tune and normalize using validation; keep test data held out. Join score rows by trial_id and claimed_user_id and verify truth labels. Later blur affects face test-probe pixels only, with unchanged palm scores, enrollment, models, normalizers, and trial manifest. Sigma zero must reproduce the unblurred baseline.

Use readable Python and simple variable names. The user requests plentiful useful informal lowercase inline comments, with no space after #, for example: value = compute() #keep this frozen. Do not add standalone or multiline explanatory comments. Avoid decorative comment blocks, unnecessary rewrites, em dashes in new prose, and filenames named after chunks. Keep the legacy source bytes intact even where its original style differs.

The subsequent review improvements are authorized and implemented: locked manifests with explicit --rebuild, temporary legacy checks with optional --export, shared verified loading/enrollment/scoring, accepted frozen model loading, configurable evaluator score descriptions, and explicit run status/provenance. Preserve the accepted baseline reference separately from latest-run discovery. Read docs/data_contracts.md before changing these interfaces. Tests should not overwrite project evidence.

Do not commit virtual environments, secrets, raw biometric images, processed image arrays, or private source documents. Original supplied landmark arrays are retained solely as the explicit legacy baseline. Document dataset provenance and access conditions before acquisition. Do not push, merge, change remotes, submit coursework, or contact teammates without the user's instruction.

Update project_status.md with actual checks and pending gates after substantive work. Save durable decisions in project_memory.md. Never state tests passed unless executed, or experiments completed unless numerical evidence exists.
