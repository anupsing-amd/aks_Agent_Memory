# Build and understand the MIGraphX plugin EP

This is a hands-on series. By the end you will have created a Python environment from nothing, run a tiny model on the MIGraphX execution provider, compiled that execution provider from source yourself, and read the exact code that moves tensors between ONNX Runtime and the GPU.

It is separate from the `learn/` folder. That one explains the AIMIGRAPHX-1371 ticket. This one teaches the stack you will work on.

## Order

Read in order. Each lecture is one sitting: a short idea, one experiment you run, and a "stop here" line. The chat is where questions get answered.

| File | You will |
|---|---|
| [01-plugin-ep-idea.md](01-plugin-ep-idea.md) | See what a plugin execution provider is, and list the one on this box |
| [02-venv-and-run-cpu.md](02-venv-and-run-cpu.md) | Create a venv, install ONNX Runtime and MIGraphX, run a tiny model on the CPU |
| [03-run-on-migraphx-ep.md](03-run-on-migraphx-ep.md) | Run the same model on the MIGraphX GPU EP and compare |
| [04-ortvalue-and-iobinding.md](04-ortvalue-and-iobinding.md) | Learn tensors, shapes, strides, OrtValue, and IO binding |
| [05-migraphx-install.md](05-migraphx-install.md) | Turn your existing MIGraphX build into something the EP build can link against |
| [06-onnxrt-home.md](06-onnxrt-home.md) | Assemble the ONNX Runtime headers the EP build needs, and prove they work |
| [07-build-ep.md](07-build-ep.md) | Compile the MIGraphX EP from source and run the tiny model on your own build |
| [08-buffers-inside-compute.md](08-buffers-inside-compute.md) | Read how the EP copies inputs and outputs across the GPU boundary |
| [09-your-first-edit.md](09-your-first-edit.md) | Add one log line to the EP, rebuild, and watch it fire (optional) |

## Conventions

- Experiments live in [`exp/`](exp/). Each is small and self-contained. A lecture tells you which one to run.
- The hands-on environment is a fresh venv at `JIRA/AIMIGRAPHX-1371/.venv-learn`, which you build in lecture 02. The existing `.venv` and `.venv-new` are left alone as known-good references.
- "Black box" means: do not open it, trust what it returns. MIGraphX's internals are a black box for this series. We care about its edges: what shapes it takes and returns. The EP and ONNX Runtime are not black boxes; those are what you are learning.

## What you need going in

You already have a MIGraphX build at `/scratch/anupsing/migraphx/AMDMIGraphX/build`, a ROCm 10.1 tarball at `/scratch/anupsing/migraphx/rocm-10.1.0`, a gfx1151 GPU, and the original wheels cached in `JIRA/AIMIGRAPHX-1371/downloads/`. Every command in the series uses those. Nothing is downloaded except, once, a set of ONNX Runtime headers in lecture 06.

Start with [01-plugin-ep-idea.md](01-plugin-ep-idea.md).
