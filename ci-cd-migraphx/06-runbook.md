# Level 6 - Health-Maintenance Runbook (mid-term bridge)

Goal: be able to read a failure and know the first move. This is your personal
cheat-sheet. Source of truth: the "Operational notes" section of
`gpu-compiler-second-brain/migraphx/migraphx-ci-jenkins-pipelines.md`, plus the
two Jenkinsfiles.

## Mental model (start here): a red build is a pointer, not a mystery

Concrete scenario. You get pinged: *"PR CI is red."* You open the PR and see:

- white-check `Jenkins - All Targets Release`
- red-x `Jenkins - MLIR Debug`

Your routine:

1. **Click the red check** - it links straight to that stage's Jenkins build log.
2. **Find the first error line** (scroll to where normal output stops).
3. **Match it to a known pattern** in the tables below. Say it reads
   *"Generated files are different..."* -> cause: someone forgot `make generate`
   -> first move: run `make generate` locally and commit.
4. **Decide flaky vs real**: transient infra (node died, empty API response) ->
   just re-run; a real code error (sanitizer, `-Werror`, accuracy) -> fix the code.

Mental model: **a red build is a pointer, not a puzzle.** Around 90% of failures
are one of a handful of known patterns - click, read the first error, match,
apply the first move. The tables below *are* that lookup.

## Main gate (`AMDMIGraphX/Jenkinsfile`) - symptom -> cause -> fix

| Symptom | Likely cause | First move |
|---|---|---|
| A stage was skipped unexpectedly | It already has a `success` status for that commit SHA on GitHub (Level 4C) | Re-run with `FORCE_REBUILD=true` |
| Image build runs on every build | A file in the hash set keeps changing, or `FORCE_DOCKER_IMAGE_BUILD` is stuck on | Check what changed among `Dockerfile`/`*requirements.txt`/`install_prereqs.sh`/`rbuild.ini`; turn the param off |
| "Generated files are different..." | Someone edited `tools/include/*.hpp` without regenerating | Run `make generate` locally and commit the result |
| "Git repo is not clean after running cmake" | cmake is writing into the source tree | Find/fix the cmake step writing tracked files |
| ORT stage: "no .deb found" | `HIP Clang Release` was skipped without `skip_also_requires` covering it | Re-run; ensure the stash dependency is intact (Level 4C) |
| Stage red with sanitizer output | Real memory/UB bug caught by ASAN/UBSan | Read the sanitizer stack in the stage log; fix the code |
| `-Werror` compile failure | A new warning | Fix the warning (CI treats warnings as errors) |

## Weekly tracker (`onnx_zoo/Jenkinsfile`) - symptom -> cause -> fix

| Symptom | Likely cause | First move |
|---|---|---|
| "No .tar.gz archives under /datasets/onnx-model-zoo" | The node lost its NFS mount (the `nfs` label is necessary but not sufficient) | Check the NFS mount on that agent |
| "unhealthy run: N/M checks failed" | The sweep ran but >= half failed, so nothing was published | Pull the archived `logs/**/*.err` from the build and triage |
| "run the whole pipeline rather than restarting this stage" | Someone restarted only `Publish logs`; `RUN_ID` was null | Restart from the top of the pipeline |
| Nothing pushed, no error | Logs were byte-identical to the previous run | Nothing to do - expected behavior |
| GPU-detect step times out (1 min) | Wedged GPU on the node | Investigate/reset the GPU; the job fails fast on purpose |

## How to re-run things (parameters you'll actually use)

- Gate `FORCE_REBUILD=true` - ignore prior green statuses; run **every** stage.
- Gate `FORCE_DOCKER_IMAGE_BUILD=true` - rebuild/push images even if the hash
  already exists.
- Zoo `IMAGE_TAG=<tag>` - pin which prebuilt image the sweep pulls (default
  `latest`); `TIMEOUT_HOURS=<n>` - sweep time budget.

## Where the evidence lives

- **Gate**: each stage reports a GitHub check `Jenkins - <stage>` linking back to
  the Jenkins build; open the build's console log for that stage. `.deb`
  artifacts are archived only on `develop`/`master`.
- **Zoo success**: the report is committed to the reports repo under
  `onnx-models/<RUN_ID>/` (`accuracy/`, `perf/`, `README.md`).
- **Zoo failure**: nothing reaches the reports repo, so the `post { unsuccessful }`
  block archives `logs/**/*.out,*.err` on the Jenkins build - that is the only
  copy.

## Reproduce the sweep locally (fastest way to learn)

From `AMDMIGraphX/tools/model_zoo/onnx_zoo/README.md`:

```bash
# Curated CI set against pre-downloaded models
USE_LOCAL=1 MODEL_LIST=/datasets/onnx-model-zoo/ci-models.txt \
    ./tools/model_zoo/onnx_zoo/test_models.sh /datasets/onnx-model-zoo

# More logging while debugging
VERBOSE=1 DEBUG=1 USE_LOCAL=1 ./test_models.sh /datasets/onnx-model-zoo/<one-model-dir>
```

## Triage greps (point at the `logs/` folder)

```bash
grep -HRL PASSED logs            # files that did NOT pass -> something went wrong
grep -HRi RuntimeError logs/     # runtime errors
grep -HRl FAILED logs/accuracy   # accuracy failures specifically
```

## A sane first-response checklist

1. Which pipeline failed - gate or tracker?
2. Which stage, and what's the first error line in its log?
3. Match it to a row above -> apply the "first move."
4. If it's a flaky/infra blip (empty API response, transient node issue),
   re-run; the gate fails open and is safe to replay.
5. If it's a real code failure (sanitizer, `-Werror`, accuracy), it's a
   genuine regression - open/triage with the code author.

> Deliverable done when: given a red build, you can name the probable cause and
> the first action without searching.
