# Level 4 - The Shared Machinery (first real deep dive)

Now we read the Groovy helpers in `AMDMIGraphX/Jenkinsfile` that make the gate
efficient. Keep the "answer-key" note open alongside:
`gpu-compiler-second-brain/migraphx/migraphx-ci-jenkins-pipelines.md` (section
"Pipeline 1").

Four mechanisms matter: (A) content-addressed images, (B) node/arch selection,
(C) commit-status stage-skipping, (D) the build cleanliness gates.

## A. Content-addressed Docker images ("rebuild only when needed")

Stage `Check image` (lines ~313-330) computes a hash of every file that affects
the environment, and uses that hash as the image **tag**:

```bash
shopt -s globstar
sha256sum Dockerfile **/*requirements.txt tools/requirements-py.txt \
  **/install_prereqs.sh **/rbuild.ini **/test/onnx/.onnxrt-commit \
  | sha256sum | cut -d " " -f 1
```

- That hash becomes `env.IMAGE_TAG`.
- `docker manifest inspect <image>:<tag>` asks the registry "does this exact tag
  already exist?" -> sets `env.IMAGE_EXISTS`.
- `Build image` only runs `when { IMAGE_EXISTS == 'false' || FORCE_DOCKER_IMAGE_BUILD }`
  (lines ~334-337).

**Net effect:** if no environment file changed, the hash matches an existing
image and the (slow) image build is skipped. Change the `Dockerfile` or any
`requirements.txt` and the first build on that commit rebuilds + pushes a new
image (slow once, fast after). The build tries `--cache-from <image>:latest`
first and falls back to `--no-cache` on any error (lines ~346-351).

`Check ORT image` / `Build ORT image` do the identical trick over a different
file set (`tools/docker/ort.dockerfile`, `.onnxrt-commit`, the ORT scripts),
producing `IMAGE_TAG_ORT` / `IMAGE_EXISTS_ORT` (lines ~503-546).

> The GitHub Actions `ci.yaml` uses the **same idea** with `hashFiles(...)` -
> see Level 5. Same concept, different syntax.

## B. Node selection and GPU architectures

`rocmnodename(name)` (lines ~19-46) maps a friendly name to a Jenkins label
expression, always AND-ed with `(rocmtest || migraphx)`:

- `mi300+` -> `... && (gfx942 || gfx950) && !vm`
- `navi32` -> `... && gfx1101 && !vm`
- `navi4x` -> `... && gfx1201 && !vm`
- `nogpu` -> `... && nogpu`, `onnxrt` -> `... && onnxrt`

`&& !vm` keeps real GPU work off virtual machines. The label decides **which
physical machine** runs a stage.

Arch lists (lines ~3-17):
- `getgputargets()` = `gfx908;gfx90a;gfx942;gfx950;gfx1030;gfx1100;gfx1101;gfx1201`
  - a single build compiles kernels for **every** supported GPU (a "fat binary").
- `getnavi3xtargets()` = `gfx1100;gfx1101`; `getnavi4xtargets()` = `gfx1201`.

So one node builds code that runs on all archs (gate), whereas the weekly
tracker builds only its own node's arch (faster).

## C. Commit statuses + stage-skipping (the "replay is cheap" trick)

Four cooperating helpers:

1. **`resolveSha()`** (lines ~148-161) - find the commit SHA to report against.
   For PRs it prefers the PR **head** SHA (via `shaFromSCMRevisionAction()`,
   lines ~132-145), not the synthetic merge commit - otherwise the status would
   land on a commit nobody can see.
2. **`setCommitStatus(sha, state, context, desc)`** (lines ~115-130) - POSTs to
   the GitHub statuses API so each stage shows up as a check named
   `Jenkins - <stage>` with a link back to the Jenkins build.
3. **`autoSetGitStatus(conf){ body }`** (lines ~163-178) - wraps any block:
   set `pending` -> run `body()` -> set `success`; on exception set `failure`
   and rethrow.
4. **`isStageCompleted(stageName)`** (lines ~188-232) - asks GitHub
   `/commits/<sha>/status`; if the latest status for `Jenkins - <stage>` is
   already `success`, returns true. It retries 3x on an empty response and
   **fails open** (returns false) on any error, so a flaky API re-runs the stage
   rather than wrongly skipping it.

These come together in **`rocmtest(conf){ body }`** (lines ~234-291), which every
test stage calls. It:
- Bails early if `isStageCompleted(variant)` (and any `skip_also_requires`) are
  already green - so re-running the same commit **skips stages that already
  passed**. This is what makes "replay after one flaky stage" cheap.
- Sets cache env vars (`CCACHE_DIR`, `AMD_COMGR_CACHE_DIR`, etc.).
- Runs two nested stages `setup <variant>` and `build <variant>`, the latter
  inside `withDockerContainer` with a **4-hour timeout** and a `rm -rf build`
  cleanup in `finally`.

**The dependency exception:** `HIP Clang Release` stashes the `.deb` that
`ONNX Runtime Tests` later unstashes. So it must not be skipped unless the ORT
stage also already passed - expressed as:

```groovy
rocmtest(skip_also_requires: ['ONNX Runtime Tests']) { ... }
```

`FORCE_REBUILD=true` makes `isStageCompleted` always return false, forcing every
stage to run.

## D. The build cleanliness gates (`cmake_build`)

`cmake_build(bconf)` (lines ~72-113) is the real build closure. Two "tree must
stay clean" checks, both `git diff-index --quiet HEAD`:
1. After `cmake` - cmake must not modify tracked files.
2. After `make generate` - if the generated type-erasure headers differ, it
   fails with *"Generated files are different. Please run make generate and
   commit the changes."* (This is the classic surprise for new contributors who
   edit `tools/include/*.hpp` without re-running `make generate`.)

Other details: `CXXFLAGS='-Werror'`; an LSan suppressions file for known
`dnnl`/`libtbb` leaks; it pins the package's per-GPU dependency to the node's
arch via `THEROCK_GPU_ARCH`; default targets `all package check`
(`skip_package` drops `package`); archives the `.deb` only on `develop`/`master`.

## Caches that survive across builds

Both pipelines bind-mount `${WORKSPACE}/../` to `/workspaces` and point ccache +
comgr cache at `/workspaces/.cache/...`. Because that directory is the **parent
of the workspace** on the node, the caches persist between builds on the same
machine, making recompiles fast.

## Check-your-understanding

1. You change `requirements.txt`. Which stages get slower on the next build, and
   why only the first time?
2. Why does `isStageCompleted` return `false` on an API error instead of `true`?
3. You restart a build and the `ONNX Runtime Tests` stage fails "no .deb found."
   Which upstream stage was wrongly skipped, and which config prevents that?

> Deliverable done when: you can explain the image-hash trick and the
> status-based stage-skipping in your own words, without the code open.
