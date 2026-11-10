"""IO binding: give ONNX Runtime the exact input and output buffers to use.

    $LPY ep-plugin-from-source/exp/iobind.py

Runs tiny.onnx on the MIGraphX EP two ways:
  1) plain sess.run (ORT allocates the output for you)
  2) io_binding with a pre-made output OrtValue you own
Both must agree. This is the mechanism the real model's DiT/VAE runners use.
"""
import os
import sys

import numpy as np
import onnxruntime as ort

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ep import register, migraphx_device  # noqa: E402

here = os.path.dirname(os.path.abspath(__file__))
model = os.path.join(here, "tiny.onnx")

register()
dev = migraphx_device()
if dev is None:
    raise SystemExit("no MIGraphX EP device; see exp/list_ep_devices.py")
so = ort.SessionOptions()
so.add_provider_for_devices([dev], {"device_id": "0"})
sess = ort.InferenceSession(model, so)

x = np.array([[-2, -0.5, 1, 3]], np.float16)

# 1) ORT allocates the output
y_run = sess.run(None, {"x": x})[0]

# 2) you provide both buffers as CPU OrtValues and bind them
xv = ort.OrtValue.ortvalue_from_numpy(x)
yv = ort.OrtValue.ortvalue_from_numpy(np.zeros((1, 4), np.float16))
b = sess.io_binding()
b.bind_ortvalue_input("x", xv)
b.bind_ortvalue_output("y", yv)       # ORT writes the result into this exact buffer
sess.run_with_iobinding(b)
y_bind = yv.numpy()

print("sess.run     y =", y_run.tolist())
print("io_binding   y =", y_bind.tolist())
print("agree:", np.allclose(y_run, y_bind))
print("\nThe output buffer 'yv' had to exist before the run, at the right shape and size.")
print("Lecture 08 shows the EP doing this allocation on the GPU side, and what breaks when")
print("the size it allocates does not match the shape MIGraphX writes.")
