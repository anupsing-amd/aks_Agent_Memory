"""Run tiny.onnx on the MIGraphX plugin EP and compare to the CPU answer.

    $PY ep-plugin-from-source/exp/run_mgx.py

Shows the two plugin-EP calls: register the library, then attach the device to a
SessionOptions with add_provider_for_devices (string option values only).
"""
import os
import sys

import numpy as np
import onnxruntime as ort

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ep import register, migraphx_device, EP  # noqa: E402

here = os.path.dirname(os.path.abspath(__file__))
model = os.path.join(here, "tiny.onnx")

lib = register()
print("registered:", lib)
dev = migraphx_device()
if dev is None:
    raise SystemExit("no MIGraphX EP device found; run exp/list_ep_devices.py to debug")

so = ort.SessionOptions()
so.add_provider_for_devices([dev], {"device_id": "0"})   # values must be strings
sess = ort.InferenceSession(model, so)
print("providers:", sess.get_providers())

x = np.array([[-2, -0.5, 1, 3]], np.float16)
y = sess.run(None, {"x": x})[0]
ref = np.maximum(x, 0) + 1

print("x   =", x.tolist())
print("y   =", y.tolist(), "(from the MIGraphX EP)")
print("ref =", ref.tolist())
print("match:", np.allclose(y, ref))
print("ran on MIGraphX EP:", sess.get_providers()[0] == EP)
