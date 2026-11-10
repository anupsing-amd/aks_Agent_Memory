# 02. Make an environment and run a model on the CPU

You will build a clean Python environment from nothing, install ONNX Runtime and MIGraphX into it, and run a tiny model. This lecture stays on the CPU so nothing can go wrong with the GPU yet. The point is the environment.

## What a venv is

A virtual environment (venv) is a folder with its own Python and its own installed packages. It keeps this project's libraries separate from the system Python and from the other venvs on this box. You never "install ONNX Runtime on the machine." You install it into one venv.

The packages come from wheels. A wheel is a zip of a prebuilt library plus a little metadata. The four wheels you need are already cached in `JIRA/AIMIGRAPHX-1371/downloads/`, so nothing is downloaded here.

## Create the venv and install the wheels

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
D=$PWD/downloads
uv venv --python 3.12 .venv-learn
VPY=$PWD/.venv-learn/bin/python
uv pip install --python "$VPY" \
  "$D/onnxruntime-1.29.0+rocm10.1.0a20260910.db10ad4-cp312-cp312-manylinux_2_28_x86_64.whl" \
  "$D/onnxruntime_ep_migraphx-1.0.0+rocm10.1.0a20260910.db10ad4-cp312-cp312-manylinux_2_28_x86_64.whl" \
  "$D/migraphx-2.18.0+rocm10.1.0a20260910.eaac82c-cp312-none-manylinux_2_28_x86_64.whl" \
  "$D/migraphx_libs-2.18.0+rocm10.1.0a20260910.eaac82c-py3-none-manylinux_2_28_x86_64.whl" \
  numpy onnx
```

Four wheels, one idea each:

- `onnxruntime` is the runtime you import.
- `onnxruntime_ep_migraphx` is the plugin EP: it carries `libmigraphx-ep.so`. You do not use it yet in this lecture, but install it now so the environment is complete.
- `migraphx` and `migraphx_libs` are the MIGraphX compiler and its runtime libraries, which the EP will call later.

## One required fixup: the soname symlink

The ONNX Runtime wheel ships the library as `libonnxruntime.so.1.29.0`. The plugin asks the loader for `libonnxruntime.so.1` (its soname, the name baked into the dependency). Those are not the same filename, so you make a symlink from one to the other:

```bash
cap=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/.venv-learn/lib/python3.12/site-packages/onnxruntime/capi
ln -sf libonnxruntime.so.1.29.0 "$cap/libonnxruntime.so.1"
```

Without this, lecture 03 fails with `libonnxruntime.so.1: cannot open shared object file`. The known-good `.venv` has this same symlink.

## The environment file

Running against the GPU needs ROCm and MIGraphX on the library path. A helper sets that up and defines `LPY` as this venv's Python:

```bash
source ep-plugin-from-source/env-learn.sh
echo $LPY          # .../.venv-learn/bin/python
```

Read [env-learn.sh](env-learn.sh). It only sets `ROCM_PATH`, `LD_LIBRARY_PATH` (MIGraphX libs, ROCm libs, and the ONNX Runtime `capi` dir), and `LPY`. From here on, lectures use `$LPY` and assume you have sourced it.

## Experiment: run the tiny model on the CPU

```bash
source ep-plugin-from-source/env-learn.sh
$LPY ep-plugin-from-source/exp/make_tiny_model.py
$LPY ep-plugin-from-source/exp/run_cpu.py
```

`make_tiny_model.py` writes `tiny.onnx`: `y = relu(x) + 1` in fp16. `run_cpu.py` feeds `x = [-2, -0.5, 1, 3]` and prints `y`. Expected:

```text
y   = [[1.0, 1.0, 2.0, 4.0]]
match: True
```

Work it out by hand: `relu` clamps negatives to 0, giving `[0, 0, 1, 3]`, then `+1` gives `[1, 1, 2, 4]`. You now have a working runtime and a model whose answer you can predict. Lecture 03 sends the same model to the GPU.

You can stop here.
