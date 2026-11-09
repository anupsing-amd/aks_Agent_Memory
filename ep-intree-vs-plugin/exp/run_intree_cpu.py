"""Run tiny.onnx on the in-tree CPU execution provider.

    <venv-python> exp/run_intree_cpu.py

The CPU EP is in-tree: its adapter is compiled into libonnxruntime.so. You pick it
by name, with no registration and no runtime library loading. This script proves that
by showing the provider is already in get_available_providers() before you do anything.
"""
import os

import numpy as np
import onnxruntime as ort

here = os.path.dirname(os.path.abspath(__file__))
model = os.path.join(here, "tiny.onnx")

# In-tree EPs are known the instant ORT is imported. Nothing was registered.
print("onnxruntime", ort.__version__)
print("available (in-tree) providers:", ort.get_available_providers())
print("ort.get_ep_devices()",ort.get_ep_devices())
print("registered anything? no")

# Select the EP purely by name.
sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
print("session providers:", sess.get_providers())

x = np.array([[-2, -0.5, 1, 3]], np.float16)
y = sess.run(None, {"x": x})[0]
ref = np.maximum(x, 0) + 1

print("x   =", x.tolist())
print("y   =", y.tolist(), "(from the in-tree CPU EP)")
print("ref =", ref.tolist(), "(y = max(x,0)+1)")
print("match:", np.allclose(y, ref))
