# Level 3 - The Weekly ONNX Zoo "Tracker" (`onnx_zoo/Jenkinsfile`)

File: `AMDMIGraphX/tools/model_zoo/onnx_zoo/Jenkinsfile`

Goal: understand a *tracker* and contrast it with the Level 2 *gate*.

## What this job is for

Once a week it: builds MIGraphX, runs a curated set of real ONNX models for
**accuracy** and **performance**, and commits a report into a **separate reports
GitHub repo**. It does **not** block any merge. Its value is a historical record:
"did accuracy or speed regress compared to last week?"

## Setup at the top of the file

- `agent { label "gfx1201 && nfs" }` - a Navi4x node that also has the dataset
  NFS mount (lines ~20-22).
- `triggers { cron('H H(2-5) * * 0') }` - Sundays, 2-5 AM (line ~25).
- `disableConcurrentBuilds()` - two runs would fight over the reports repo and
  caches (line ~30).
- Parameters: `IMAGE_TAG` (default `latest`), `TIMEOUT_HOURS` (default `12`).
- Constants: `MODEL_ROOT = /datasets/onnx-model-zoo` (the NFS dataset), plus
  credential IDs for the reports repo (lines ~1-8).

## The three stages

### 1. Checkout - fail fast before spending hours

Guards, in order (lines ~47-66):
1. There is at least one `*.tar.gz` under `MODEL_ROOT` (catches a missing NFS
   mount).
2. `ci-models.txt` (the curated list) exists.
3. `IMAGE_TAG` matches `^[A-Za-z0-9._-]+$` (injection guard - it is interpolated
   into a `docker pull`).
4. An empty `withCredentials` block - asserts the reports-repo credential exists
   **now**, not 12 hours later at publish time.
Then it does `checkout scm` and builds a run id:
`env.RUN_ID = "<date>-<build#>-<short-sha>"`.

### 2. Run Models - build once, then sweep (lines ~69-112)

Inside the Docker container (mounting the dataset read-only):
1. **GPU detect** (1-min timeout) - `rocminfo | grep gfx...` -> `env.GPU_TARGET`.
   A hung `rocminfo` means a wedged GPU; fail fast.
2. **Build** (2-hour timeout) - release build for the node's single arch
   (`-DGPU_TARGETS=$GPU_TARGET`, much faster than the gate's fat binary); builds
   only the `migraphx_py` and `driver` targets.
3. **Sweep** (`TIMEOUT_HOURS` timeout) - runs
   `tools/model_zoo/onnx_zoo/test_models.sh` against the curated `ci-models.txt`.

### 3. Publish logs - commit the report (lines ~114-159)

1. Guard: `RUN_ID` must match the full pattern, else error "run the whole
   pipeline rather than restarting this stage" (prevents publishing a `null`
   directory if someone restarts just this stage).
2. Shallow-clone the reports repo (token kept in **shell** vars so it never
   prints to the log).
3. Run `summarize.py` to compare this run's perf against the most recent prior
   run and write `logs/README.md`.
4. Copy `accuracy/`, `perf/`, `README.md` into `<clone>/onnx-models/<RUN_ID>/`.
5. If nothing changed vs last run, log "nothing to push" and exit 0; otherwise
   commit as `migraphx-ci` and `git push` to the reports repo's `main`.

`post` blocks (lines ~162-170):
- `always` - remove the clone from the node.
- `unsuccessful` - archive the `logs/**/*.out,*.err` as build artifacts, because
  on failure **nothing reached the reports repo**, so this is the only copy.

## What `test_models.sh` actually does (the sweep engine)

File: `AMDMIGraphX/tools/model_zoo/onnx_zoo/test_models.sh`. Per model archive:
1. Extract the tarball into `tmp_model/` (`USE_LOCAL=1` skips git-lfs steps).
2. Find the first real `*.onnx` (ignoring `._*` AppleDouble files).
3. For each **kind** (`accuracy`, `perf`) x **dtype**, run under a per-model
   `timeout` (20m default) and write `logs/<kind>/<model>[_fp16].{out,err}`.
4. dtypes are `fp32 fp16`, **except** archives whose name contains `int8`/`qdq`
   (already quantized) -> run `int8` only, skip fp16.
5. **accuracy** calls `zoo_check.py`; **perf** calls `migraphx-driver perf`
   reusing the exact driver-args the accuracy run emitted (so both compile the
   model identically).
6. Health gate at the end: if `TOTAL_CHECKS == 0` or at least half failed, exit 1
   so a garbage baseline is never published.

## Gate vs Tracker - the one-sentence difference

- **Gate** (Level 2): parallel, fat-binary, reports pass/fail to GitHub, **blocks
  merges**, and skips work already proven for a SHA.
- **Tracker** (this): single node, single-arch, long timeouts, **blocks nothing**;
  its output is a committed historical record of accuracy + performance.

Note: this pipeline deliberately does **not** use `rocmtest` / GitHub commit
statuses - there is no PR to annotate.

## Check-your-understanding

1. Why build for only one arch here, but a fat binary in the gate?
2. Why does the Checkout stage check credentials it doesn't use yet?
3. What stops a half-broken sweep from poisoning next week's comparison?

> Deliverable done when: you can list the 3 stages and give the gate-vs-tracker
> difference in one sentence.
