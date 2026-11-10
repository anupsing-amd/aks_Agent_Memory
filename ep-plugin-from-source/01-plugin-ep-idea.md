# 01. What a plugin execution provider is

ONNX Runtime (ORT) runs a model. It does not run every operation itself. It hands groups of operations to a backend called an execution provider (EP). The CPU EP runs them on the CPU. The MIGraphX EP sends a subgraph to MIGraphX, which compiles it into GPU kernels. This series is about that MIGraphX EP: how it is packaged, how it is built, and how it moves data.

## Two ways an EP can be attached

**In-tree.** The EP is compiled into ONNX Runtime's own library. You pick it by naming it in a list when you create the session:

```python
ort.InferenceSession("model.onnx", providers=["MIGraphXExecutionProvider"])
```

This is how ROCm 7.2 shipped the MIGraphX EP. The provider name only works if that build of ORT already contains the EP.

**Plugin.** The EP is a separate shared library, `libmigraphx-ep.so`. ONNX Runtime does not contain it. You tell ORT to load it at runtime, then attach it to the session. This is how ROCm 10.1 ships it, and it is what you will build. Two calls do it:

```python
ort.register_execution_provider_library("MIGraphXExecutionProvider", "/path/to/libmigraphx-ep.so")
# ... then find the device this EP runs on and attach it to a SessionOptions
so.add_provider_for_devices([ep_device], {"device_id": "0"})
```

The plugin interface is an agreement, an ABI, between ORT and the library. ORT calls fixed entry points in the `.so`: a factory that creates the EP (`OrtEpFactory`), the EP object itself (`OrtEp`), the thing that runs a compiled subgraph (`OrtNodeComputeInfo`), and the thing that copies tensors to and from the device (`OrtDataTransferImpl`). Those names are listed at the top of the EP's [README.md](../src/onnxruntime-ep-amdgpu/README.md). The ABI was added in ONNX Runtime 1.24. Any ORT from 1.24 on can load a plugin EP built against it; that is the whole point of a plugin.

```mermaid
flowchart LR
  app["your Python"] --> ort["ONNX Runtime"]
  ort -->|"loads at runtime"| so["libmigraphx-ep.so"]
  so --> mgx["MIGraphX (black box)"]
  mgx --> hip["ROCm / GPU"]
```

You will meet `OrtNodeComputeInfo` again in lecture 08: its `Compute` function is where the input and output buffers are handed to MIGraphX, and buffers are the thing you want to understand.

## Experiment: see the plugin on this box

This does not need the new venv yet. It uses the existing `.venv` and the already-installed plugin, just to show you a registered EP device.

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
source scripts/env.sh
$PY ep-plugin-from-source/exp/list_ep_devices.py
```

Expected output: the ONNX Runtime version, then a line for the `MIGraphXExecutionProvider` device with its vendor and the GPU arch `gfx1151`. If you see that line, ORT has loaded `libmigraphx-ep.so` and discovered your GPU through it. That is a plugin EP, registered and ready.

Read [exp/list_ep_devices.py](exp/list_ep_devices.py). It is about 15 lines: find the library, register it, print the devices. Lecture 03 does the same thing from a clean venv you built, and then actually runs a model through it.

You can stop here.
