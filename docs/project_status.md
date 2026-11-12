# Nafis implementation status

N1-N7 code and first measured RQ1 are implemented. Final integrity/reproducibility review is in progress; inspect the current Desktop handoff for the latest verified commit and checks. Sakeeb's acceptance of the handoff remains a separate step.

Completed: repository cleanup; byte-preserved runnable legacy code/data; public dataset retrieval and integrity/audit tools; 39-user artificial mapping; session-aware 4/2/4 partitions; fixed validation/test claim manifests; enrollment-only PCA face and HOG/LBP palm pipelines; validation model selection; keyed raw score exports; general evaluator and actual RQ1 metrics/figures. No README or .gitkeep files remain in project-owned source folders.

Actual outputs are located by results/metrics/rq1_latest.json. The first measured face EER is 0.0895748987854251 and palm EER is 0.2380229419703104, using interpolated empirical ROC EER. These are new image-dataset results, distinct from the legacy Caltech EER 0.2612.

Source caveat: BMPD Kaggle license metadata is Unknown, even though the course preapproves the dataset. No redistribution permission is claimed; raw images, contact sheets and frozen models remain ignored/local. The heuristic ROI lacks rotation/anatomical alignment. See methodology.md for the actual controls and limitations.

Next after Nafis review: Sakeeb reproduces the exact accepted checkpoint, then implements validation-only normalization and keyed 50/50 fusion (RQ2), face-probe blur with fixed palms/models (RQ3), and final engineering QA. No fusion/blur code is included yet. GitHub remote and final submission requirements remain unconfirmed; no push or submission occurred.
