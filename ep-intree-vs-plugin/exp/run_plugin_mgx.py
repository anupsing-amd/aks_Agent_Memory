"""Run tiny.onnx on the MIGraphX plugin EP.

    source ep-intree-vs-plugin/exp/env-plugin.sh
    $PY exp/run_plugin_mgx.py

The MIGraphX EP is a plugin: its adapter lives in libmigraphx-ep.so, not in ORT.
So you must (1) register the library at runtime, then (2) attach its device to a
SessionOptions. Contrast with run_intree_cpu.py, which did neither.
"""
import os

import numpy as np
import onnxruntime as ort

EP = "MIGraphXExecutionProvider"
here = os.path.dirname(os.path.abspath(__file__))
model = os.path.join(here, "tiny.onnx")


def plugin_lib():
    """Path to libmigraphx-ep.so (env override wins, else the installed wheel)."""
    if os.environ.get("MIGRAPHX_EP_LIB"):
        return os.environ["MIGRAPHX_EP_LIB"]
    import onnxruntime_ep_migraphx
    return onnxruntime_ep_migraphx.get_library_path()


print("onnxruntime", ort.__version__)
# Before registering, the plugin is NOT an available provider. That is the difference.
print("available (in-tree) providers:", ort.get_available_providers())
print("MIGraphX in that list before register?:", EP in ort.get_available_providers())

# (1) Load the plugin .so at runtime.
lib = plugin_lib()
try:
    ort.register_execution_provider_library(EP, lib)
except Exception as e:
    if "already registered" not in str(e).lower():
        raise
print("registered:", lib)

# (2) Find the EP's device and attach it to the session.
dev = next((d for d in ort.get_ep_devices() if d.ep_name == EP), None)
if dev is None:
    raise SystemExit("no MIGraphX EP device found; run exp/inspect_ort.py to debug")

so = ort.SessionOptions()
so.add_provider_for_devices([dev], {"device_id": "0"})   # values must be strings
sess = ort.InferenceSession(model, so)
print("session providers:", sess.get_providers())

x = np.array([[-2, -0.5, 1, 3]], np.float16)
y = sess.run(None, {"x": x})[0]
ref = np.maximum(x, 0) + 1

print("x   =", x.tolist())
print("y   =", y.tolist(), "(from the MIGraphX plugin EP)")
print("ref =", ref.tolist())
print("match:", np.allclose(y, ref))
print("ran on MIGraphX EP:", sess.get_providers()[0] == EP)
