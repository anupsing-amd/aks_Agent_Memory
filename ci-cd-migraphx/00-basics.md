# Level 0 - The Absolute Basics (child's view, zero code)

Goal of this note: understand the *words* before touching any file. If someone
says "the PR CI gate failed because the Docker image rebuilt on a different
node," you should be able to picture what that means.

## The one-sentence problem CI/CD solves

Many people edit the same big program every day. **How do we make sure nobody's
edit secretly breaks it?** Answer: a robot re-builds and re-tests the program
automatically on every change. That robot system is called CI/CD.

## The robot-kitchen analogy

Picture a kitchen run by a robot. The robot follows a written checklist every
time the recipe changes.

| Kitchen word | Real CI word | What it means |
|---|---|---|
| Recipe | Code / source | The human-written instructions for the program |
| Cooking the dish | Build (compile) | Turning source code into a runnable program |
| Tasting the dish | Test | Checking the program behaves correctly |
| Robot auto-cooks on every recipe edit | CI (Continuous Integration) | Build + test automatically on every change |
| Robot auto-packs & ships once it passes | CD (Continuous Delivery) | Package and release automatically after tests pass |
| The checklist | Pipeline | The ordered list of steps the robot runs |
| One checklist item | Stage | A single step, e.g. "build", "test" |
| The written checklist file | Jenkinsfile | A text file **inside the repo** describing the pipeline |
| The robot / kitchen manager | Jenkins | The software that reads the Jenkinsfile and runs it |
| Which kitchen station does the work | Agent / node | The specific machine (and which GPU) that runs a stage |
| A sealed lunchbox of tools+ingredients | Docker image | A pre-packed environment so every machine is identical |
| Opening the lunchbox and working in it | Docker container | A running instance of an image |
| Oven model (gas, electric, convection) | GPU architecture (`gfx942`, `gfx1201`) | Different GPU chips; code must be built for each |
| The bouncer at the door | Gate | If tests fail, your change is **not allowed to merge** |
| A logbook of past dinners | Tracker | A job that records history instead of blocking anything |

## The 12 words you must not be fuzzy on

1. **Code / source** - the text humans write (C++, Python, etc.).
2. **Build (compile)** - convert source into a program the computer can run.
   For MIGraphX this produces a `.deb` package and test binaries.
3. **Test** - run the program on known inputs and check the outputs.
4. **CI (Continuous Integration)** - automatically build + test every change so
   bugs are caught in minutes, not weeks.
5. **CD (Continuous Delivery/Deployment)** - automatically package/ship once CI
   passes.
6. **Pipeline** - the ordered recipe of stages the automation runs.
7. **Stage** - one named step in a pipeline.
8. **Jenkins** - a popular, self-hosted automation server (the "robot"). AMD
   runs its own Jenkins servers internally.
9. **Jenkinsfile** - the pipeline written as a file in the repo. Jenkins reads
   it. It is written in a language called *Groovy* (don't worry about Groovy
   yet - at Level 2 we only read the stage names).
10. **Agent / node / runner** - the machine that executes a stage. A "label"
    like `gfx942` tells Jenkins "only run this on a machine with that GPU."
11. **Docker image / container** - a frozen, repeatable environment (OS +
    compilers + libraries). Every node opens the *same* image, so a build
    behaves the same everywhere. A **container** is one running copy of an image.
12. **Gate vs Tracker** - a *gate* blocks merging when it fails (the PR CI). A
    *tracker* just records results over time (the weekly model sweep).

## A few extra words you'll meet immediately

- **Repo (repository)** - the project's folder tracked by git (here: `AMDMIGraphX`).
- **PR (Pull Request)** - a proposed change someone wants to merge. CI runs on it.
- **Branch** - a line of development. `develop` and `master` are long-lived branches.
- **SCM** - "Source Control Management" (git). "SCM trigger" = "run when code changes."
- **cron** - a schedule. `H H(2-5) * * 0` means "once every Sunday, early morning."
- **Commit SHA** - a unique id for one exact version of the code.
- **Artifact** - a file a build produces and saves (e.g. the `.deb`, or log files).

## Clarifying: Docker image (software) vs node (hardware)

Common beginner question: *"since we build/test on different nodes and GPU
archs, is there a different image per node?"* Short answer: **no - the gate uses
one shared image for all build/test nodes.** Keep three things separate:

- **Image = software, baked once, shared everywhere.** The gate builds ONE image
  (`rocm/migraphx-ci-jenkins-ubuntu`) and every build/test node pulls that same
  tag. It is arch-independent: OS + compilers + ROCm + Python deps. (A second
  image, `...-ort`, is used *only* by the ONNX Runtime stage.)
- **Node = hardware, chosen per stage by a label.** `mi300+`, `navi32`,
  `navi4x`, `nogpu`, `onnxrt` pick a physical machine. The node's real GPU is
  plugged into the container with `--device=/dev/kfd --device=/dev/dri`.
- **Which arch to compile for is a build flag, not the image.** Most stages
  compile a "fat binary" for all archs (`GPU_TARGETS=gfx908;...;gfx1201`); the
  Navi stages narrow it to their own arch.

So the gate flow (your instinct, corrected) is:
pull the **one** image -> check out the **PR source** (`checkout scm`) -> start a
container **on the chosen node, with its GPU mounted** -> `cmake`/`make`/tests
inside -> report pass/fail. Same lunchbox at every station; the oven (GPU)
belongs to the station, not the lunchbox.

> Nuance: a `nogpu` node runs the *same* image but needs no GPU, because those
> stages only compile/run CPU + sanitizer tests.

## How this maps to MIGraphX (preview of later levels)

- MIGraphX has **two** automation systems: **Jenkins** (AMD-internal, the focus)
  and **GitHub Actions** (public). Level 1 maps them.
- The main Jenkins pipeline is a **gate** - file:
  `AMDMIGraphX/Jenkinsfile`. Level 2.
- The weekly model sweep is a **tracker** - file:
  `AMDMIGraphX/tools/model_zoo/onnx_zoo/Jenkinsfile`. Level 3.

## Check-your-understanding (answer in your own words)

1. Why do we want the robot to build on *every* change instead of once a week?
2. What is the difference between a Docker *image* and a *container*?
3. Why does the same program need to be built for `gfx942` **and** `gfx1201`?
4. What is the practical difference between a "gate" and a "tracker"?

> Deliverable done when: you can explain all 12 core words to a colleague
> without looking at this table.
