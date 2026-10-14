# Level 5 - The Supporting Cast (files the pipelines call)

Goal: know what each pipeline step actually runs. Think of this as the
"ingredients list" behind the two Jenkinsfiles, plus the parallel GitHub Actions
system.

## Mental model (start here): the Jenkinsfile is a thin conductor

Picture one PR going through the gate, and watch *who actually does the work*:

1. The Jenkinsfile says "check/build the image" - but the real recipe lives in
   **`Dockerfile`** (plus the `requirements.txt` / `install_prereqs.sh` it pulls
   in). The Jenkinsfile only decides *whether* to build it.
2. The Jenkinsfile says "build & test" - the real work is `cmake` + `make`,
   wrapped by the `cmake_build` closure. The Jenkinsfile just passes flags.
3. The ORT stage says "test onnxruntime" - the real work is
   **`build_and_test_onnxrt.sh`**, baked into the ORT image.

Same for the weekly sweep: the "Run Models" stage is thin; the work is
**`test_models.sh`**, which itself calls **`zoo_check.py`** (accuracy) and
**`migraphx-driver perf`** (perf), and finally **`summarize.py`** writes the
report.

So the mental model: **the pipeline file is a conductor; the Dockerfiles and
scripts are the musicians doing the actual playing.** When a stage fails, it is
almost always *one of these files* that failed - and the lists below tell you
which one to open.

## Docker images (the environments)

- `AMDMIGraphX/Dockerfile` - the main build environment: Ubuntu 24.04 + ROCm
  repos + Clang-17 + cmake + Python + ccache + PyTorch(rocm) + doc tools. It runs
  `tools/install_prereqs.sh` using `requirements.txt`, `dev-requirements.txt`,
  `rbuild.ini`, `tools/requirements-py.txt`. This is the content that the image
  hash (Level 4A) is computed over.
- `AMDMIGraphX/tools/docker/ort.dockerfile` - starts from the same base, then
  clones onnxruntime at a pinned commit (`test/onnx/.onnxrt-commit`) into
  `/onnxruntime` and adds the CI scripts `build_and_test_onnxrt.sh` and
  `pai_*_launcher.sh`. Used by the gate's ONNX Runtime stage.
- Other `tools/docker/*.dockerfile` (sles, ubuntu_2204, ubuntu_2404, legacy,
  hip-clang-legacy, migraphx_with_onnxruntime_pytorch) - alternative/older
  environments; `sles.docker` feeds the GitHub Actions SLES jobs.

## Scripts behind the weekly sweep (Level 3)

- `tools/model_zoo/onnx_zoo/test_models.sh` - the sweep driver. Extracts each
  model archive, finds the `.onnx`, and for each kind x dtype runs under a
  `timeout`, writing `logs/<kind>/<model>.{out,err}`. Ends with a health gate
  (fail if 0 checks or >= half failed).
- `tools/model_zoo/onnx_zoo/zoo_check.py` - the **accuracy** checker. Parses the
  onnx model, optionally quantizes to fp16, compiles for the target, runs each
  bundled test case, and compares outputs within `--atol/--rtol`. Prints
  `PASSED`/`FAILED` per case and a summary ("Worst deviation ... of tolerance").
  With `--emit-driver-args` it writes the exact driver flags so the perf run
  compiles identically.
- `tools/model_zoo/onnx_zoo/summarize.py` - reads `logs/accuracy` + `logs/perf`,
  finds the most recent **baseline** run, compares perf rates (>= 5% drop =
  regression), and writes `logs/README.md` (a table with status icons and links).

## Scripts behind the ORT stage (Level 2)

- `tools/build_and_test_onnxrt.sh` - built into the ORT image at
  `/onnxruntime/`; the final gate stage runs it after installing this commit's
  `.deb`.
- `tools/pai_test_launcher.sh`, `tools/pai_provider_test_launcher.sh` - test
  launchers copied into the onnxruntime tree by `ort.dockerfile`.

## Shared build config (feeds the image hash)

- `tools/install_prereqs.sh` - installs build prerequisites inside the image.
- `rbuild.ini`, `requirements.txt`, `dev-requirements.txt`,
  `tools/requirements-py.txt` - dependency pins. Changing any of these changes
  the image hash and triggers a rebuild (Level 4A).

## Pipeline step -> file it invokes (quick map)

| Pipeline step | Runs / depends on |
|---|---|
| Gate: Check/Build image | `Dockerfile` + requirements/`install_prereqs.sh`/`rbuild.ini` |
| Gate: each test stage | `cmake_build` closure -> `cmake` + `make all package check` |
| Gate: Check/Build ORT image | `tools/docker/ort.dockerfile` + `.onnxrt-commit` + ORT scripts |
| Gate: ONNX Runtime Tests | installs the stashed `.deb`, runs `build_and_test_onnxrt.sh` |
| Zoo: Run Models | `cmake`/`make migraphx_py driver`, then `test_models.sh` |
| Zoo: test_models.sh | `zoo_check.py` (accuracy) + `migraphx-driver perf` (perf) |
| Zoo: Publish logs | `summarize.py` -> `logs/README.md` -> git push to reports repo |

## The other CI system: GitHub Actions (`.github/workflows/`)

`ci.yaml` jobs (public CI, runs on PRs and pushes to develop/master/release):

- `cancel` - cancel older in-progress runs of the same PR.
- `check_image` / `build_image` / `build_SLES_image` - content-addressed images
  (Ubuntu + SLES) via `hashFiles(...)` - same idea as Jenkins Level 4A.
- `tidy` - clang-tidy static analysis (cached).
- `cppcheck` - cppcheck static analysis (cached).
- `format` - clang-format / `tools/format.py` check, posts review suggestions.
- `pyflakes` - Python lint.
- `licensing` - verifies license headers.
- `linux` - the big build + unit-test matrix (lines ~404-642).
- `misspell` - spelling check.
- `sles` - build/test on the SLES image.

Other workflows:
- `windows.yaml` - Windows CPU build (Release + Debug).
- `performance.yaml` - scheduled perf tests (weekdays 07:00) + manual dispatch.
- `weekly_master_sync.yaml` - Sunday: sync `master`, merge `develop`.
- `sync-onnxrt-main.yaml` - Friday: open a PR bumping the pinned onnxruntime
  commit.
- `clean-closed-pr-caches.yaml` - delete caches when a PR closes.
- `pr-review-status.yaml` - publish a PR-review dashboard to GitHub Pages.

> Observation for later: Jenkins and GitHub Actions **duplicate** the
> content-addressed-image trick and some build/test work in different languages.
> Note that for Level 7.

## Check-your-understanding

1. Which file does the gate's final stage execute, and where did it come from?
2. In the sweep, which script decides pass/fail for accuracy vs performance?
3. Name two jobs that exist in GitHub Actions but not in the Jenkins gate.

> Deliverable done when: you can trace any pipeline step to the concrete file it
> runs.
