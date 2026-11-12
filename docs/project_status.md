# Project status

Setup date: November 12, 2026. Scope: initial project foundation (N1).

Completed setup items: context reviewed and retained locally; directory structure; unchanged PPA3 source/data; environment requirements; regression utility and test; VS Code workspace, tasks, debugging; developer roadmap and team folders. Consult the measured legacy JSON and setup report for executed verification and commit ID.

| Phase | Owner | State |
| --- | --- | --- |
| N1: setup and PPA3 regression | Nafis | Complete: source hashes, counts, metrics and figures verified in isolated Python 3.13.2 |
| N2: approved image data acquisition/quality audit | Nafis | Pending |
| N3: mapped identities, partitions, fixed claims | Nafis | Pending |
| N4: face-image authentication | Nafis | Pending |
| N5: first palm-image authentication | Nafis | Pending |
| N6: generic PPA3-derived evaluator | Nafis | Pending |
| N7: measured RQ1 and accepted handoff | Nafis | Pending |
| S1-S5: fusion, blur, final QA and packaging | Sakeeb | Waiting for complete N7 handoff |

Next implementation task: N2, verify permitted Olivetti/BMPD access, labels, right-palm parsing, sessions, actual counts, image quality, and dataset provenance. Only then finalize the protocol and create real manifests. No raw image datasets were downloaded for setup. No RQ1/RQ2/RQ3 numerical results exist.

Open inputs: agreed team GitHub URL; BMPD source and permitted use; any updated course announcement/rubric and submission schedule. These inputs do not prevent local setup.

Executed: `.venv\Scripts\python.exe -m unittest discover -s tests -v`, one regression test passed. Observed original PPA3 AUC 0.7569, EER 0.2612, d-prime 1.0973; 124 genuine and 2,356 impostor scores. Three legacy plots generated. These are historical Caltech-only measurements.
