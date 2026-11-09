# 04. Plugin EP: build a venv, register, run on MIGraphX

Same `tiny.onnx`, now through a plugin EP on the GPU. The model does not change. What changes is that ORT does not contain this EP, so you load it at runtime and attach it to the session.

## Build the plugin venv

This one needs the full stack: ORT, the plugin EP wheel (it carries `libmigraphx-ep.so`), and MIGraphX (the compiler + its runtime libraries the EP will call).

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
D=$PWD/downloads
uv venv --python 3.12 .venv-plugin
PPY=$PWD/.venv-plugin/bin/python
uv pip install --python "$PPY" \
  "$D/onnxruntime-1.29.0+rocm10.1.0a20260910.db10ad4-cp312-cp312-manylinux_2_28_x86_64.whl" \
  "$D/onnxruntime_ep_migraphx-1.0.0+rocm10.1.0a20260910.db10ad4-cp312-cp312-manylinux_2_28_x86_64.whl" \
  "$D/migraphx-2.18.0+rocm10.1.0a20260910.eaac82c-cp312-none-manylinux_2_28_x86_64.whl" \
  "$D/migraphx_libs-2.18.0+rocm10.1.0a20260910.eaac82c-py3-none-manylinux_2_28_x86_64.whl" \
  numpy onnx
```

Four wheels, one idea each:

- `onnxruntime` — the runtime you import (same build as the in-tree venv).
- `onnxruntime_ep_migraphx` — the plugin EP; it ships `libmigraphx-ep.so`.
- `migraphx` and `migraphx_libs` — the MIGraphX compiler and its runtime `.so`s, external to both ORT and the EP.

## One required fixup: the soname symlink

The ORT wheel ships the library as `libonnxruntime.so.1.29.0`, but the plugin asks the loader for `libonnxruntime.so.1` (its soname). Make the symlink:

```bash
cap=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/.venv-plugin/lib/python3.12/site-packages/onnxruntime/capi
ln -sf libonnxruntime.so.1.29.0 "$cap/libonnxruntime.so.1"
```

Without it, registration fails with `libonnxruntime.so.1: cannot open shared object file`.

## The environment file

Running on the GPU needs ROCm and MIGraphX on the library path. A helper sets that and defines `PY` for this venv:

```bash
cd /scratch/anupsing/migraphx/aks_Agent_Memory/ep-intree-vs-plugin
source exp/env-plugin.sh
echo $PY     # .../.venv-plugin/bin/python
```

Read [exp/env-plugin.sh](exp/env-plugin.sh). It only sets `ROCM_PATH`, `LD_LIBRARY_PATH` (the external MIGraphX libs, ROCm libs, and the ORT `capi` dir), and `PY`. Notice `migraphx_libs` is on the path: that is the real MIGraphX, living outside ORT and outside the EP, exactly as lecture 01 described.

## Experiment: register the plugin and run

```bash
source exp/env-plugin.sh
$PY exp/make_tiny_model.py     # if you did not already write tiny.onnx
$PY exp/run_plugin_mgx.py
```

Expected tail (ignore any `adjust_allocation` warnings from MIGraphX):

```text
available (in-tree) providers: ['CPUExecutionProvider']
MIGraphX in that list before register?: False
registered: .../onnxruntime_ep_migraphx/libmigraphx-ep.so
session providers: ['MIGraphXExecutionProvider', 'CPUExecutionProvider']
y   = [[1.0, 1.0, 2.0, 4.0]] (from the MIGraphX plugin EP)
match: True
ran on MIGraphX EP: True
```

Three things to notice:

1. `MIGraphXExecutionProvider` is **not** in `get_available_providers()` before you register. In-tree EPs would be; a plugin is not. This is the exact contrast with lecture 03.
2. It took two calls to attach: `register_execution_provider_library` (load the `.so`) then `add_provider_for_devices` (use it for this session). A name in a list would not have worked.
3. The answer `[1, 1, 2, 4]` is identical to the CPU run. Same model, different attachment, same result.

Read [exp/run_plugin_mgx.py](exp/run_plugin_mgx.py) side by side with `run_intree_cpu.py`. The model code and the numbers are identical; only the attachment differs.

You can stop here. Lecture 05 opens up both libraries to see why one needed registering and the other did not.
