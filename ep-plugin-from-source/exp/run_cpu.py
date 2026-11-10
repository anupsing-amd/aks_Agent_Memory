"""Run tiny.onnx on the CPU execution provider and check the result.

    $PY ep-plugin-from-source/exp/run_cpu.py

Expects tiny.onnx next to this file (make_tiny_model.py writes it).
"""
import os

import numpy as np
import onnxruntime as ort

here = os.path.dirname(os.path.abspath(__file__))
model = os.path.join(here, "tiny.onnx")

sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
print("providers:", sess.get_providers())

x = np.array([[-2, -0.5, 1, 3]], np.float16)
y = sess.run(None, {"x": x})[0]
ref = np.maximum(x, 0) + 1

print("x   =", x.tolist())
print("y   =", y.tolist(), "(from onnxruntime)")
print("ref =", ref.tolist(), "(y = max(x,0)+1)")
print("match:", np.allclose(y, ref))
