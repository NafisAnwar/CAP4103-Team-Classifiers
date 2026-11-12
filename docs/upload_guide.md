# Owner upload and collaborator setup

## What the audit means

All 113 tracked files were already on origin/main. The four missing folders were ignored, not lost in transit. The new README and updated handoff are prepared locally and need a new commit/push. The full-assets preparation command explicitly changes ignore rules for the four folders and stages their current contents. Git LFS is used for data/raw, data/processed and reference PDFs.

The local inventory on November 12, 2026 was 816 raw files (875.81 MiB), 65 processed files (20.11 MiB), five reference files (0.25 MiB, including the already tracked inventory) and three legacy plots (0.37 MiB). These counts can grow after new experiments. The virtual environment, credentials, caches, Git internals and temporary work are not portable research inputs and stay local.

## Prepare, review, then push from VS Code PowerShell

Run this from the project root. The newest request explicitly authorizes the root README, superseding the earlier no-README preference. No history rewrite or force push is needed; keep the existing noreply email configuration.

```powershell
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'C:\Users\anwar\Desktop\CAP4103 - Mobile Biometrics\CAP4103 - Course Project\CAP4103-Biometric-Fusion'
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
git switch main
if ($LASTEXITCODE -ne 0) { throw 'Cannot select main.' }
git merge --ff-only origin/main
if ($LASTEXITCODE -ne 0) { throw 'Main needs reconciliation; stop here.' }
& .\scripts\prepare_full_upload.ps1 -IncludeResearchAssets
if (-not $?) { throw 'Preparation failed.' }
git diff --cached --name-status
git diff --cached --shortstat
git lfs status
```

The IncludeResearchAssets switch includes biometric samples, local models, contact sheets, intermediate runs and reference documents. BMPD's license metadata remains Unknown, and course documents may have separate sharing conditions. Private access or LFS does not establish permission to redistribute. Use that switch only for assets you are permitted to share. To publish documentation/code while collaborators acquire datasets directly, run the same script without the switch; the four folders remain ignored.

Review the staged filenames. Then commit and push:

```powershell
git commit -m "docs: add project overview and detailed collaborator handoff"
if ($LASTEXITCODE -ne 0) { throw 'Commit failed; inspect git status.' }
git push origin main
if ($LASTEXITCODE -ne 0) { throw 'Push failed; inspect the reported Git or LFS error.' }
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw 'Cannot verify remote state.' }
git rev-parse HEAD
git rev-parse origin/main
git diff --exit-code HEAD origin/main
if ($LASTEXITCODE -ne 0) { throw 'Local and remote trees differ.' }
git lfs push --dry-run origin main
if ($LASTEXITCODE -ne 0) { throw 'Cannot verify LFS upload state.' }
git status --short
```

The commit message may be changed to mention research assets if included. A push uploads LFS objects through its local hook before updating the Git branch. Matching Git commit IDs proves Git-tree sync; it does not independently prove that each large object can be downloaded. A new clone with git lfs pull followed by the frozen-model check and tests is the end-to-end verification.

Do not push the backup/pre-email-privacy-fix branch, all branches or old tags. That backup predates the user's email-privacy rewrite. The prepared workflow pushes main only and does not change author/email configuration.

## Full-copy verification by a collaborator

```powershell
git lfs install
git clone https://github.com/NafisAnwar/CAP4103-Team-Classifiers.git
Set-Location CAP4103-Team-Classifiers
git lfs pull
git lfs fsck
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -B -c "from src.experiment_support import load_frozen_models; models, metadata = load_frozen_models(); print(metadata['run_id'], sorted(models))"
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Stop on command failures. With the complete local bundle, expect all 33 tests to run without skips. Missing raw/model assets lead to two integration-test skips; follow docs/nazmus_handoff.md rather than treating a skipped check as verified.

## Troubleshooting

- PowerShell refuses a script: inspect the file, then use powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\prepare_full_upload.ps1 -IncludeResearchAssets for that invocation. This does not change the machine's persistent policy.
- Authentication/404: ensure Nazmus accepted the private-repository invitation and signed in with an authorized GitHub account. An owner's successful push does not grant collaborator access.
- LFS storage/bandwidth error: inspect the account's LFS usage/billing; do not buy storage automatically or retry a normal-Git upload of the data. Keep code/docs available and use source downloads if the team does not want LFS storage.
- A local data file begins with version https://git-lfs.github.com/spec/v1: it is an unmaterialized pointer. Run git lfs pull before image/model loading.
- Interrupted LFS upload: keep the local files, inspect git lfs logs last and retry git push origin main after resolving the cause. Do not reset, force push, migrate existing history or remove the local assets.
- File-count mismatch during preparation: inspect git check-ignore -v <path>. The script intentionally does not disable all ignore rules or force-add the environment.
- Locked-manifest/model mismatch: stop and compare versions, clone commit and original dataset bytes. Never rebuild the manifest lock or change recorded hashes merely to suppress the error.

GitHub documentation: [Git LFS overview](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage), [repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits), [LFS install](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-install.adoc), [LFS FAQ](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-faq.adoc).
