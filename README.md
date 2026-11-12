# Combining Face and Palmprint Scores for Authentication Under Image Blur

CAP4103, Fall 2026, Dr. Tempestt Neal. Working editor: Visual Studio Code on Windows.

Start with [the project status](docs/project_status.md), [persistent project memory](docs/project_memory.md), and [the developer roadmap](docs/developer_roadmap.md).

This repository extends the supplied PPA3 matching and HW3 evaluation foundation. The six original source/data files in `ppa3_legacy/` are byte-for-byte copies. They use Caltech landmark coordinates, not photographs. Raw face images are required for the later blur experiment.

## Current capability

The original PPA3 program, an executable regression check, a Python environment, VS Code tasks/debugging, and the project structure are provided. Final image pipelines, datasets, mapping/split manifests, and RQ1/RQ2/RQ3 measurements are pending. See `results/metrics/legacy_regression.json` for executed legacy evidence. An initial setup commit is not Nafis's completed 60% handoff.

## Open and run

Open `CAP4103-Biometric-Fusion.code-workspace` in VS Code. Select `.venv\Scripts\python.exe` if VS Code asks for an interpreter. Run these commands from the repository root in its PowerShell terminal; activation is optional:

```powershell
.\.venv\Scripts\python.exe scripts/check_environment.py
.\.venv\Scripts\python.exe ppa3_legacy/main.py
.\.venv\Scripts\python.exe scripts/verify_legacy.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`Terminal > Run Task` exposes environment, legacy, regression, and test commands. `Run and Debug` includes the unchanged legacy program and regression verifier.

To recreate the environment on Windows with Python 3.13:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

`requirements.txt` lists direct packages verified during setup; `requirements-lock.txt` records the installed environment. Install new feature dependencies only when their implementation uses them. No system execution-policy changes are needed.

## Project organization

| Folder | Purpose |
| --- | --- |
| `ppa3_legacy/` | Original runnable PPA3 source and landmark arrays |
| `src/` | Future image loaders, mapping, matching, evaluation, then fusion/blur |
| `experiments/` | Future RQ1, RQ2, RQ3 entrypoints, created as implemented |
| `tests/`, `scripts/` | Executable checks and development utilities |
| `configs/` | Explicitly provisional protocol configuration |
| `data/raw/`, `data/processed/` | Local image data and derived arrays, ignored by Git |
| `data/manifests/` | Actual audited dataset/mapping/split/trial manifests, pending |
| `results/metrics/`, `results/figures/` | Measured numerical evidence and figures |
| `docs/reference/` | Unmodified source documents, local and excluded from Git |
| `docs/team/`, `report/`, `presentation/` | Team planning and future submission materials |

## Engineering sequence

Nafis owns N1-N7 (60 effort units): setup, data audit, fixed protocol, initial face and palm pipelines, evaluator, measured RQ1. Sakeeb owns S1-S5 (40 effort units): reproduce the accepted handoff, validation normalization and equal-weight fusion, face-probe blur, RQ2/RQ3, final engineering QA and documentation. These are planned engineering shares, not grading percentages.

The older team plan assigns palm work broadly to Nazmus; the newer engineering handoff puts the first palm baseline with Nafis so the RQ1 boundary is runnable before transfer. See `docs/team/responsibilities.md`.

No remote repository has been selected. Local Git is used for reviewable checkpoints. Configure the agreed GitHub remote when the team supplies it. Dataset acquisition and source permissions must be verified before image experiments.
