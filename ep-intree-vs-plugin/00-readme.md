# In-tree vs plugin EP, hands-on

A short, self-contained series about one thing only: the **two ways an execution provider (EP) is attached to ONNX Runtime (ORT)**. You will build two Python environments, run the *same* tiny model through each, and then look inside ORT to see what is actually compiled in versus loaded at runtime.

This is a companion to `JIRA/AIMIGRAPHX-1371/learn-ep/`. That series builds the MIGraphX plugin EP end to end. This one zooms in on the attachment mechanism so the plugin lectures make sense.

## The one idea

An EP can be attached two ways:

- **In-tree** — the EP adapter is compiled *into* `libonnxruntime.so`. You pick it by name: `providers=["SomeExecutionProvider"]`. No runtime loading, no registration.
- **Plugin** — the EP adapter is a *separate* `.so`. ORT does not contain it. You load it at runtime (`register_execution_provider_library`) and attach it to the session (`add_provider_for_devices`).

## How in-tree is taught

In-tree is shown twice, cheapest first:

1. The **CPU EP** (lecture 03) — genuinely in-tree in every ORT build, selected by name, zero external dependencies. It isolates the *mechanism*.
2. The **real in-tree MIGraphX EP** (lecture 06) — AMD's `onnxruntime-migraphx` wheel, where the MIGraphX adapter is compiled into ONNX Runtime. This is how ROCm 7.2 shipped it. It runs on the GPU and hits the exact same MIGraphX libraries as the plugin, so in-tree vs plugin becomes a true apples-to-apples comparison.

Plugin is taught with the **MIGraphX plugin EP** (lecture 04). So you run one tiny model three ways: in-tree CPU, in-tree MIGraphX, plugin MIGraphX.

## Order

Read in order. Each lecture is one sitting: a short idea, one experiment, a "stop here" line.

| File | You will |
|---|---|
| [01-two-ways-to-attach.md](01-two-ways-to-attach.md) | Learn what in-tree and plugin mean, and what is compiled where |
| [02-tiny-model.md](02-tiny-model.md) | Write a tiny ONNX model whose answer you can predict by hand |
| [03-venv-intree-cpu.md](03-venv-intree-cpu.md) | Build a venv with only ORT; run the model on the in-tree CPU EP by name |
| [04-venv-plugin-migraphx.md](04-venv-plugin-migraphx.md) | Build a venv with the plugin stack; register and run the model on the MIGraphX EP |
| [05-analyze-what-comes-in-ort.md](05-analyze-what-comes-in-ort.md) | Inspect both EPs: what ORT reports, and what the libraries actually contain |
| [06-intree-migraphx.md](06-intree-migraphx.md) | Build a venv with the real in-tree MIGraphX EP; run MIGraphX by name and compare all three |

## Conventions

- Experiments live in [`exp/`](exp/). Each is small and self-contained. A lecture tells you which one to run.
- Three fresh venvs, built in lectures 03, 04, and 06, live under `JIRA/AIMIGRAPHX-1371/` so they can reuse the cached wheels in `downloads/`:
  - `.venv-intree` — only the `onnxruntime` wheel. No plugin, no MIGraphX.
  - `.venv-plugin` — `onnxruntime` + the plugin EP + MIGraphX.
  - `.venv-intree-mgx` — AMD's `onnxruntime-migraphx` wheel (MIGraphX EP built in) + MIGraphX.
- "Black box" means do not open it, trust what it returns. MIGraphX internals are a black box here. ORT and the EP boundary are exactly what you are learning.

## What you need going in

A `gfx1151` GPU, the ROCm 10.1 tarball at `/scratch/anupsing/migraphx/rocm-10.1.0`, `uv` installed, and the cached wheels in `JIRA/AIMIGRAPHX-1371/downloads/`. Only lecture 06 downloads one thing: AMD's in-tree `onnxruntime-migraphx` wheel.

Start with [01-two-ways-to-attach.md](01-two-ways-to-attach.md).
