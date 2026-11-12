# CAP4103 project setup checkpoint

Prepared November 12, 2026.

Project directory: `C:\Users\anwar\Desktop\CAP4103 - Mobile Biometrics\CAP4103 - Course Project\CAP4103-Biometric-Fusion`

The new VS Code workspace contains the preserved PPA3 baseline, source/experiment/test directories, raw and processed data locations, manifest/config locations, measured results locations, developer documentation, and report/presentation workspaces. Original course-folder PDFs remain in place. Five source context documents are retained locally under docs/reference and excluded from Git.

Persistent project context is in AGENTS.md and docs/project_memory.md. The roadmap and team responsibilities distinguish Nafis's initial 60 engineering units from Nazmus Sakeeb's final 40. This is project-local memory, not account-wide memory. The scope of this checkpoint is setup/N1.

## Executed verification

- Isolated Python 3.13.2 environment created at .venv.
- Core dependency versions: numpy 2.3.2, scipy 1.16.3, scikit-learn 1.9.1, matplotlib 3.10.7.
- Complete installed dependency versions recorded in requirements-lock.txt.
- One executable legacy regression test passed in 21.747 seconds.
- All six original source/data SHA-256 hashes match the supplied PPA3 archive.
- Original dataset: 375 samples, 20 identities, 251 enrollment samples and 124 test probes.
- Comparisons: 124 genuine, 2,356 impostor.
- Original PPA3 AUC 0.7569, approximate EER 0.2612 (26.12%), d-prime 1.0973.
- Three plots generated under ppa3_legacy/plots. JSON evidence and captured stdout are in results/metrics.
- VS Code workspace observed open with the project tree, README and developer roadmap.

These metrics belong only to the original Caltech landmark baseline. No face-image, palmprint, fusion or blur experiment has been run, and no raw image datasets were downloaded.

## Current commands in the VS Code PowerShell terminal

```powershell
.\.venv\Scripts\python.exe scripts/check_environment.py
.\.venv\Scripts\python.exe ppa3_legacy/main.py
.\.venv\Scripts\python.exe scripts/verify_legacy.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The same checks are exposed through Terminal > Run Task. Python and debug extensions were already installed. Workspace settings point at .venv; debug configurations are provided for the baseline and verifier.

## Next development work

Nafis: N2 dataset access, permitted-use verification, counts, identity/hand/session parsing and image-quality audit. Then N3 fixed artificial mappings and splits, N4/N5 face and palm pipelines, N6 shared evaluation, and N7 measured RQ1 plus an exact-commit handoff.

Sakeeb: reproduce that completed N7 handoff first; then validation-only normalization/50-50 fusion, face-probe-only blur, RQ2/RQ3, integrity checks, final results and technical packaging. The initial setup commit is not that N7 handoff.

The team GitHub URL, verified BMPD access conditions, original later instructor announcement, submission schedule and presentation rubric remain open inputs. Git is local; no remote was added and no push, submission or teammate message occurred.
