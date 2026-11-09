# 06. In-tree MIGraphX EP: the real apples-to-apples

Lectures 03 and 04 contrasted in-tree (CPU) with plugin (MIGraphX). Clean, but two different backends. This capstone closes the loop: the **same MIGraphX backend**, attached **in-tree**, so the only variable left is the attachment mechanism. This is exactly how ROCm 7.2 shipped the MIGraphX EP, and the wheel for it still exists.

## The wheel

AMD publishes an `onnxruntime-migraphx` wheel where the MIGraphX EP is compiled into ONNX Runtime. From [the ROCm multi-arch index](https://rocm.frameworks.amd.com/whl-multi-arch/onnxruntime-migraphx/) grab the cp312 / ROCm 7.14 build (it pairs with the `rocm7.14.0rc3` MIGraphX wheels already in `downloads/`):

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/downloads
curl -L -o "onnxruntime_migraphx-1.23.2+rocm7.14.0-cp312-cp312-manylinux_2_28_x86_64.whl" \
  "https://rocm.frameworks.amd.com/whl-multi-arch/onnxruntime-migraphx/onnxruntime_migraphx-1.23.2%2Brocm7.14.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
```

Peek inside and you see the key difference from the plugin wheel:

```bash
unzip -l onnxruntime_migraphx-1.23.2*.whl | grep -i migraphx
# onnxruntime/capi/libonnxruntime_providers_migraphx.so   <-- the EP, shipped with ORT
```

`libonnxruntime_providers_migraphx.so` is the in-tree MIGraphX adapter. It ships *inside the onnxruntime package*, not as a separate plugin you register. ORT loads it internally when you name the provider.

## Build the in-tree MIGraphX venv

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
D=$PWD/downloads
uv venv --python 3.12 .venv-intree-mgx
IMPY=$PWD/.venv-intree-mgx/bin/python
uv pip install --python "$IMPY" \
  "$D/onnxruntime_migraphx-1.23.2+rocm7.14.0-cp312-cp312-manylinux_2_28_x86_64.whl" \
  "$D/migraphx-2.16.0+rocm7.14.0rc3.c7984a4-cp312-none-manylinux_2_28_x86_64.whl" \
  "$D/migraphx_libs-2.16.0+rocm7.14.0rc3.c7984a4-py3-none-manylinux_2_28_x86_64.whl" \
  numpy onnx
```

Note there is **no** `onnxruntime_ep_migraphx` here. The EP is in the `onnxruntime-migraphx` wheel itself. MIGraphX (`migraphx`, `migraphx_libs`) is still separate, exactly as lecture 01 insisted.

## Two fixups

**1. Unversioned sonames.** The ROCm 7.14 `migraphx_libs` wheel ships `libmigraphx_gpu.so.2016000`, but MIGraphX's loader `dlopen`s the unversioned `libmigraphx_gpu.so`. Create the symlinks:

```bash
cd /scratch/anupsing/migraphx/aks_Agent_Memory/ep-intree-vs-plugin
bash exp/fixup_intree_mgx.sh
```

**2. The HIP runtime.** This ORT is a ROCm 7.14 build, so MIGraphX needs `libhiprtc.so.7` / `libamdhip64.so.7`. There is no ROCm 7.14 on this box, but the ROCm 10.1 tarball supplies those exact HIP-major-7 sonames, and they work. The env file puts `rocm-10.1.0/lib` on the path for you. (This is a pragmatic cross-ROCm shim for a learning box; a real deployment would use matching ROCm 7.14 libraries.)

Read [exp/env-intree-mgx.sh](exp/env-intree-mgx.sh): it sets `LD_LIBRARY_PATH` to `migraphx_libs` + the ROCm 10.1 lib dirs + the ORT `capi`, and defines `IMPY`.

## Experiment: run MIGraphX by name

```bash
source exp/env-intree-mgx.sh
$IMPY exp/make_tiny_model.py     # if tiny.onnx is not already written
$IMPY exp/run_intree_mgx.py
```

Expected tail (ignore `adjust_allocation` warnings):

```text
available (in-tree) providers: ['MIGraphXExecutionProvider', 'CPUExecutionProvider']
MIGraphX available by name?: True
registered anything? no
session providers: ['MIGraphXExecutionProvider', 'CPUExecutionProvider']
y   = [[1.0, 1.0, 2.0, 4.0]] (from the in-tree MIGraphX EP)
match: True
ran on MIGraphX EP: True
```

The payoff line is `MIGraphX available by name?: True`. In the plugin venv (lecture 04) that was `False` until you registered a `.so`. Here MIGraphX is in `get_available_providers()` from the start, and you select it with a bare name, just like the CPU EP. Same backend, same GPU, same answer as lecture 04 — only the attachment changed.

## The three cases together

| | in-tree CPU (lec 03) | **in-tree MIGraphX (this lec)** | plugin MIGraphX (lec 04) |
|---|---|---|---|
| Backend | CPU | GPU via MIGraphX | GPU via MIGraphX |
| EP adapter lives in | `libonnxruntime.so` | `onnxruntime/.../libonnxruntime_providers_migraphx.so` (ships with ORT) | `libmigraphx-ep.so` (separate wheel) |
| In `get_available_providers()`? | yes | yes | no |
| How you select it | `providers=["CPUExecutionProvider"]` | `providers=["MIGraphXExecutionProvider"]` | `register_execution_provider_library` + `add_provider_for_devices` |
| Real MIGraphX (`libmigraphx*.so`) | n/a | external, `LD_LIBRARY_PATH` | external, `LD_LIBRARY_PATH` |

The middle and right columns hit the identical MIGraphX libraries. That is the cleanest possible demonstration that in-tree vs plugin is purely about *where the adapter lives and how ORT finds it* — never about where MIGraphX lives. MIGraphX is always external.

You are now complete: you have run one model three ways and can point to the exact file and the exact call that differ between in-tree and plugin.
