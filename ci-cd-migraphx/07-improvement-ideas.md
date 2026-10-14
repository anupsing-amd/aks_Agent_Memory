# Level 7 - Improvement Ideas (long-term bridge)

Status: **proposals only - no code changes.** This is a backlog to discuss with
the team (Austen / Paul / Vishal) once Levels 0-6 are solid. Each item lists the
observation, the idea, and the risk/trade-off so the discussion is grounded.

> Rule for yourself: do not "fix" a CI file until you can explain why it is the
> way it is. Many oddities are deliberate (fail-open, fat binaries, etc.).

## Mental model (start here): CI is load-bearing - propose, don't patch

Concrete scenario. Someone says: *"Jenkins and GitHub Actions both build Docker
images - that's duplication, let's delete one."* Before touching anything, ask
**"what does this currently protect against?"**:

- Jenkins runs on **real AMD GPUs** (internal machines) - it is the only place the
  GPU builds/tests actually execute.
- GitHub Actions runs on **GitHub's machines** (no AMD GPUs) - it does lint,
  CPU-only builds, Windows, SLES, and PR housekeeping.

They are *not* redundant - they cover different hardware and audiences. So the
real improvement isn't "delete one"; it's "document the split, and share only the
tiny duplicated bit (the image-hash file list)."

Mental model: **almost every odd thing in CI is load-bearing** (fail-open,
fat binaries, the `make generate` gate...). A good improvement **reduces friction
without removing protection**. Safe order, always: **document first -> one
low-risk change with a named owner -> never rip out a guard you don't understand.**

The backlog below follows that spirit: proposals, each with its trade-off.

## A. Reduce duplication between the two CI systems

- **Observation:** Jenkins (`Jenkinsfile`) and GitHub Actions (`ci.yaml`) both
  implement the content-addressed image trick and overlapping build/test work,
  in two different languages (Groovy vs YAML). Image-tag logic is even
  cross-referenced by a comment in `ci.yaml`.
- **Idea:** document the intended division of labor (what is authoritative
  where), and extract the image-hash file list into one shared source both read,
  to stop them drifting.
- **Risk:** the two systems run on different infra; a shared abstraction can leak.
  Start with documentation, not code.

## B. Share conventions between the two Jenkinsfiles

- **Observation:** the gate and the zoo pipeline repeat the same device/group
  plumbing (`--device=/dev/kfd ...`, `getent group video/render`) and the same
  `/workspaces/.cache` setup.
- **Idea:** factor the docker-opts + cache-env into a shared Groovy library
  (Jenkins "shared library") so both pipelines import one definition.
- **Risk:** adds a shared-library dependency to maintain; only worth it if more
  pipelines appear.

## C. Make flaky-stage handling explicit

- **Observation:** `isStageCompleted` already "fails open" and retries the GitHub
  API 3x; replaying a build skips green stages. But flakiness vs real failure is
  judged by a human.
- **Idea:** add lightweight per-stage retry for known-flaky operations (e.g.
  `docker pull`), and/or annotate stages that are safe to auto-retry.
- **Risk:** auto-retry can hide real intermittent bugs; scope it narrowly to
  infra steps, never to the actual build/test.

## D. Pin and audit third-party actions / tags

- **Observation:** `ci.yaml` already pins actions by commit SHA (good). Docker
  base images and some tool versions are pinned in the `Dockerfile`.
- **Idea:** add a periodic check that flags unpinned/`latest` references and
  stale pins (there is already a weekly onnxruntime-commit bump workflow to model
  this on).
- **Risk:** more maintenance noise; needs a clear owner.

## E. Improve first-failure readability

- **Observation:** a new maintainer must open the console log and scan for the
  first error.
- **Idea:** surface a short "why it failed" summary per stage (e.g. grep the
  known markers: "Generated files are different", sanitizer headers, `-Werror`)
  into the GitHub check description.
- **Risk:** brittle string matching; keep it additive to the raw log.

## Suggested prioritization for the team discussion

1. **A/B documentation** - capture the current design before changing it.
2. **E** (readability) - low risk, high day-to-day value.
3. **C/D** - only after the above, and only with a named owner.

## Next steps after this plan

- Walk Levels 0-6 notes with a teammate to validate accuracy.
- Turn the Level 1 "open questions" into actual questions for Austen / Paul /
  Vishal.
- Pick ONE low-risk item (likely **E**) as a first supervised change.

> Deliverable done when: you have a short, ranked list of improvements you can
> defend, each with its trade-off, ready to review with the team.
