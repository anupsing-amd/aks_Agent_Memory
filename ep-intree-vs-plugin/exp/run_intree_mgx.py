"""Run tiny.onnx on the in-tree MIGraphX execution provider.

    source ep-intree-vs-plugin/exp/env-intree-mgx.sh
    $IMPY exp/run_intree_mgx.py

This ORT (onnxruntime-migraphx, ROCm 7.14) has the MIGraphX EP COMPILED IN. So it is
selected exactly like the CPU EP in run_intree_cpu.py: by name, with no registration
and no register_execution_provider_library. Contrast with run_plugin_mgx.py, which
reaches the same MIGraphX backend but must load a .so at runtime.
"""
import os

import numpy as np
import onnxruntime as ort

EP = "MIGraphXExecutionProvider"
here = os.path.dirname(os.path.abspath(__file__))
model = os.path.join(here, "tiny.onnx")

# In-tree proof: MIGraphX is already an available provider, no registration done.
print("onnxruntime", ort.__version__)
print("available (in-tree) providers:", ort.get_available_providers())
print("MIGraphX available by name?:", EP in ort.get_available_providers())
print("registered anything? no")

# Select by name, just like the CPU EP.
sess = ort.InferenceSession(model, providers=[EP, "CPUExecutionProvider"])
print("session providers:", sess.get_providers())

x = np.array([[-2, -0.5, 1, 3]], np.float16)
y = sess.run(None, {"x": x})[0]
ref = np.maximum(x, 0) + 1

print("x   =", x.tolist())
print("y   =", y.tolist(), "(from the in-tree MIGraphX EP)")
print("ref =", ref.tolist())
print("match:", np.allclose(y, ref))
print("ran on MIGraphX EP:", sess.get_providers()[0] == EP)
