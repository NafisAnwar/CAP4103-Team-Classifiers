# Persistent project memory

Recorded November 12, 2026. These local project notes persist across sessions; this is not a claim of account-wide or cloud memory.

## User request and working environment

The user asked to read context, create project subfolders, set up the overall project with particular attention to Nafis and Sakeeb, retain context, and open the result in Visual Studio Code. The active course directory is `Desktop/CAP4103 - Mobile Biometrics/CAP4103 - Course Project`. The development repository is its `CAP4103-Biometric-Fusion` child. Current scope is setup/N1, not execution of all 100 engineering units.

## Context and evidence hierarchy

`docs/reference/` retains the original handoff Markdown, detailed implementation plan, October 15 course PDF, earlier brainstorming PDF, and pasted team plan. These are reference material. The supplied Desktop and course-folder Project_Description.pdf were identical by SHA-256 at setup.

The October PDF explicitly requires three connected questions, HW3 evaluation, fusion and preapproved datasets. Olivetti and BMPD are on its list. The later handoff reports a November instructor announcement relaxing mandatory face/multimodality; that announcement itself was not supplied or independently verified. Record it as reported context. The selected face+palm project remains unchanged and satisfies the older scope too. Presentation duration, rubric, due date, and remote repository URL remain unconfirmed.

The newer handoff updates the older broad team responsibilities: Nafis owns both first modality baselines and RQ1 before Sakeeb takes the final 40%. The effort shares do not describe course grades or the contributions of the other three teammates.

## Project decisions

Title: Combining Face and Palmprint Scores for Authentication Under Image Blur.

RQ1 compares face-only and palmprint-only EER under original usable unblurred conditions. RQ2 compares equal-weight normalized score fusion against both on corresponding claims. RQ3 progressively blurs only held-out face probes while palms and all learned transforms stay fixed. Interpret each result before refining the next RQ. Fusion improvement is a question, not an assumption.

Preserve PPA3 and extend its score labeling/evaluation architecture. The archive holds 375 samples of five landmark coordinates and 20 identities; it contains no raw face images. Do not attempt Gaussian image blur on those coordinates.

Proposed image approach: Olivetti with PCA and similarity templates; BMPD right palms with visually audited ROI and LBP or HOG. These choices remain proposals until actual data/validation evidence supports them. No new image models are implemented during setup.

Use a fixed, explicitly artificial face-to-palm identity mapping between different real people. Target up to 40 usable subjects, provisionally 4 enrollment/2 validation/4 test images per modality, seed 42. Actual feasibility, counts, image quality, sessions, data rights, and palm-side parsing are unverified. Tentative blur sigma values are 0, 0.8, 1.6, 2.4, requiring visual review before test analysis.

Scores must be finite, higher-is-better, and keyed by stable trial_id plus claimed_user_id. Keep raw and normalized scores distinct. No enrollment/validation/test overlap. Validation-only normalizers stay frozen across blur levels; fusion is exactly 0.5*face_normalized + 0.5*palm_normalized. Sigma zero must match RQ2; palm scores/EER must remain invariant.

## Team

Nafis Anwar: lead developer/coordinator, first 60 engineering units through runnable RQ1. Nazmus Sakeeb: developer/evaluation lead, final 40 units after handoff. Diego: research/methodology. Mikaela: results/report. Sienah: presentation, ethics/references, QA. No messages were sent to teammates during setup.

## Reporting and limits

Course report: maximum five pages including visuals, excluding references; 11pt Arial/Calibri, single spaced, justified, one-inch margins; numbered pages/figures/tables; 14pt centered title and left bold section headings; references on a separate page with persistent URLs. Ethics: up to three paragraphs, at least three credible citations connected to this system. Optional annotated bibliography requires at least four relevant research articles. Submission work remains pending.

Never reuse legacy EER as a new dataset result, claim Gaussian blur faithfully models motion blur, describe simulated pairs as the same people, or imply broad fairness/deployment performance from small datasets.

## Verified setup checkpoint

N1 baseline was executed successfully in isolated Python 3.13.2. All six original source/data hashes match. AUC 0.7569, approximate EER 0.2612, d-prime 1.0973; 251 enrollment and 124 test samples, 124 genuine and 2,356 impostor claims. The regression test passed and three plots were generated. Exact environment versions are locked in requirements-lock.txt. The VS Code workspace, README and developer roadmap were observed open. Local branch: nafis-foundation. N2 is the next implementation phase; the completed 60% handoff remains pending.

## Latest request: implementation and cleanup

The user authorized Nafis N2-N7 code implementation after cleanup, requested removal of every project README and .gitkeep, and requested a checkpoint Markdown on Desktop before the five-hour limit reaches 1% remaining. The legacy README was removed under this explicit instruction; five runnable source/data/requirements files remain byte-identical. No new README files should be created. Redundant setup placeholders were removed. Account usage is available through get_usage_limits; check at milestones.
