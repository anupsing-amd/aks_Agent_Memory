# AMDMIGraphX CI/CD - Overview

A concise, practical reference for how Continuous Integration (CI) runs for
AMDMIGraphX: the systems involved, the pipeline files, and the core concepts.

---

## TL;DR

- AMDMIGraphX is validated by **two independent CI systems**:
  - **Jenkins** - AMD-internal servers with **real AMD GPUs**; the authoritative
    build/test gate and the weekly model sweep.
  - **GitHub Actions** - public, GitHub-hosted runners (no AMD GPUs); linting,
    static analysis, CPU/Windows/SLES builds, and repository housekeeping.
- **Jenkins uses a single gate pipeline** for both **PR CI** and **Develop CI**
  ([`Jenkinsfile`](https://github.com/ROCm/AMDMIGraphX/blob/develop/Jenkinsfile)):
  it builds MIGraphX many ways in parallel on matching GPU/CPU nodes and
  **blocks merges** on failure.
- A **separate weekly Jenkins pipeline**
  ([`tools/model_zoo/onnx_zoo/Jenkinsfile`](https://github.com/ROCm/AMDMIGraphX/blob/develop/tools/model_zoo/onnx_zoo/Jenkinsfile))
  runs an ONNX model-zoo **accuracy/performance sweep** and records history
  (it does not block merges).
- **GitHub Actions' main workflow**
  ([`.github/workflows/ci.yaml`](https://github.com/ROCm/AMDMIGraphX/blob/develop/.github/workflows/ci.yaml))
  runs format/lint/static-analysis and build/test jobs; additional workflows
  cover Windows, performance, and maintenance.
- **Core mechanisms** (shared in spirit by both systems): content-addressed
  Docker images (rebuilt only when the environment changes), node selection by
  GPU **label**, and **commit-status stage-skipping** that makes re-runs cheap.

---

## 1. The two systems at a glance

| | Jenkins | GitHub Actions |
|---|---|---|
| Hosting | AMD-internal servers (real AMD GPUs) | GitHub-hosted runners (no AMD GPUs) |
| Primary role | Authoritative build/test **gate** + weekly GPU **sweep** | Lint, static analysis, CPU/Windows/SLES builds, housekeeping |
| Triggers | PRs and pushes to `develop`/`master`; weekly cron | PRs, pushes, schedules, PR lifecycle events |
| Config files | `Jenkinsfile`, `tools/model_zoo/onnx_zoo/Jenkinsfile` | `.github/workflows/*.yaml` |
| On failure | Merge is blocked (gate) | Merge is blocked for required checks |

---

## 2. Jenkins pipelines

### 2.1 PR and Develop gate - [`Jenkinsfile`](https://github.com/ROCm/AMDMIGraphX/blob/develop/Jenkinsfile)

- **Trigger:** every PR, and pushes to `develop`/`master`. The same file serves
  both jobs; `env.BRANCH_NAME` drives small per-branch differences (for example,
  the `.deb` package is archived only on `develop`/`master`).
- **Flow:** Check/Build image -> **9 parallel build+test stages** -> Check/Build
  ONNX Runtime (ORT) image -> ONNX Runtime test -> workspace cleanup. Any failure
  blocks the merge.
- **The 9 parallel stages, grouped by purpose:**
  - *Normal builds (2):* All Targets Release; HIP Clang Release (produces the
    `.deb` package consumed by the ORT stage).
  - *Per-GPU coverage (2):* Navi32 (gfx1101); Navi4x (gfx1201). MI300-class
    (gfx942/gfx950) is covered by the normal builds.
  - *Safety/sanitizer builds (3):* Clang ASAN; Clang libstdc++ Debug; HIP RTC
    Debug.
  - *Non-default configurations (2):* HIP Clang Static; MLIR Debug.
- **Key mechanisms:** content-addressed Docker images; node selection by GPU
  label (`mi300+`, `navi32`, `navi4x`, `nogpu`, `onnxrt`); commit-status
  stage-skipping (re-runs skip already-passed stages); build-cleanliness gates
  (`make generate` output must be committed; warnings are errors via `-Werror`).

### 2.2 Weekly ONNX model-zoo sweep - [`tools/model_zoo/onnx_zoo/Jenkinsfile`](https://github.com/ROCm/AMDMIGraphX/blob/develop/tools/model_zoo/onnx_zoo/Jenkinsfile)

- **Trigger:** weekly cron (Sunday, early morning), on a Navi4x node that has the
  dataset NFS mount. This is a **tracker**, not a gate.
- **Flow (3 stages):** Checkout (fail-fast validation of data/credentials) ->
  Run Models (single-arch build, then an accuracy + performance sweep) ->
  Publish logs (commit a report to a separate reports repository).

---

## 3. GitHub Actions workflows

### 3.1 Main CI - [`.github/workflows/ci.yaml`](https://github.com/ROCm/AMDMIGraphX/blob/develop/.github/workflows/ci.yaml)

- **Trigger:** PRs and pushes to `develop`/`master`/`release/**`.
- **Jobs:** cancel stale runs; content-addressed image check/build (Ubuntu +
  SLES); `tidy` (clang-tidy); `cppcheck`; `format` (clang-format); `pyflakes`;
  `licensing`; `linux` (build + unit-test matrix); `misspell`; `sles`.

### 3.2 Other workflows

- `windows.yaml` - Windows CPU build (Release/Debug).
- `performance.yaml` - scheduled performance tests + manual dispatch.
- `weekly_master_sync.yaml` - sync `master` and merge `develop` (weekly).
- `sync-onnxrt-main.yaml` - weekly PR bumping the pinned onnxruntime commit.
- `clean-closed-pr-caches.yaml` - remove CI caches when a PR closes.
- `pr-review-status.yaml` - publish a PR-review dashboard.

---

## 4. Concepts worth remembering

- **Gate vs tracker.** The PR/Develop gate blocks merges on failure; the sweep
  and performance jobs record history and do not block merges.
- **Image vs node vs arch.** The Docker **image** provides software and is shared
  across nodes; the **node** provides the physical GPU; the **target
  architecture** is a build flag (`GPU_TARGETS=...`). Compiling for an
  architecture needs no GPU; *running* the tests requires the matching GPU - which
  is why dedicated Navi stages exist.
- **Content-addressed images.** The image tag is a hash of the files that define
  the environment (`Dockerfile`, `*requirements.txt`, `install_prereqs.sh`,
  `rbuild.ini`, ...). The image is rebuilt only when one of those changes;
  otherwise the existing image is reused.
- **Commit-status stage-skipping.** Each stage records a pass/fail status against
  the commit. Re-running a build skips stages already marked successful, so
  replaying after a flaky failure is cheap.
- **Build-cleanliness gates.** CI runs `make generate` and fails if the result
  differs from what was committed, and treats compiler warnings as errors
  (`-Werror`) - keeping the repository self-consistent and warning-clean.

---

## 5. Triage quick reference

| Symptom | Likely cause | First move |
|---|---|---|
| Stage skipped unexpectedly | Already green for that commit | Re-run with `FORCE_REBUILD=true` |
| Image rebuilds every run | A file in the image-hash set keeps changing | Review `Dockerfile`/`*requirements.txt`/`install_prereqs.sh`/`rbuild.ini` |
| "Generated files are different..." | `make generate` output not committed | Run `make generate` locally and commit |
| ORT stage: "no .deb found" | `HIP Clang Release` was skipped | Re-run so the package is produced |
| Sweep: "No .tar.gz ..." | Node lost the dataset NFS mount | Check the NFS mount on the agent |

**Re-run controls:** `FORCE_REBUILD`, `FORCE_DOCKER_IMAGE_BUILD` (gate);
`IMAGE_TAG`, `TIMEOUT_HOURS` (weekly sweep).

---
