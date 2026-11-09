# 03. In-tree EP: build a venv, run on the CPU by name

Now you build the first environment and run `tiny.onnx` on an in-tree EP. "In-tree" is demonstrated by the CPU EP, which is compiled into every ONNX Runtime. You will see it needs nothing but ORT itself: no plugin wheel, no MIGraphX, no registration.

## What a venv is

A virtual environment is a folder with its own Python and its own packages, isolated from the system Python and from the other venvs on this box. You never "install ORT on the machine"; you install it into one venv. Packages come from wheels (a zip of a prebuilt library plus metadata). The wheel you need is already cached in `JIRA/AIMIGRAPHX-1371/downloads/`.

## Build the in-tree venv

Deliberately minimal: only ONNX Runtime, plus `numpy` and `onnx` to build and feed the model. No plugin EP, no MIGraphX. That is the whole point — an in-tree EP needs nothing external.

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
D=$PWD/downloads
uv venv --python 3.12 .venv-intree
IPY=$PWD/.venv-intree/bin/python
uv pip install --python "$IPY" \
  "$D/onnxruntime-1.29.0+rocm10.1.0a20260910.db10ad4-cp312-cp312-manylinux_2_28_x86_64.whl" \
  numpy onnx
```

Yes, this ORT wheel is a ROCm build, but you are only using its **CPU** EP here, which is in-tree in every build. No ROCm libraries are needed on the path to run on the CPU.

## Experiment: write the model and run it in-tree

```bash
cd /scratch/anupsing/migraphx/aks_Agent_Memory/ep-intree-vs-plugin
IPY=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/.venv-intree/bin/python
$IPY exp/make_tiny_model.py
$IPY exp/run_intree_cpu.py
```

Expected tail:

```text
available (in-tree) providers: ['CPUExecutionProvider']
registered anything? no
session providers: ['CPUExecutionProvider']
x   = [[-2.0, -0.5, 1.0, 3.0]]
y   = [[1.0, 1.0, 2.0, 4.0]] (from the in-tree CPU EP)
match: True
```

(Some builds also list `AzureExecutionProvider`; `CPUExecutionProvider` is always there.)

Two things to notice:

1. `CPUExecutionProvider` is in `get_available_providers()` **before** you create any session and **without** registering anything. That is what in-tree means: the adapter is already inside `libonnxruntime.so`.
2. You selected it with one argument, `providers=["CPUExecutionProvider"]` — a name, not a file path. This is exactly the mechanism ROCm 7.2's in-tree MIGraphX EP used.

Read [exp/run_intree_cpu.py](exp/run_intree_cpu.py). It prints the available providers first to make the "already there" point, then runs by name.

You can stop here. Lecture 04 does the contrasting case: a plugin EP that is *not* in that list until you load it.
