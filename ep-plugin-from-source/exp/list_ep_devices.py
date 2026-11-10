"""List the execution-provider devices ONNX Runtime can see.

Registers the MIGraphX plugin EP library, then prints every OrtEpDevice.
Run it after `source scripts/env.sh` so the ROCm and MIGraphX libraries are on the path.

    $PY ep-plugin-from-source/exp/list_ep_devices.py
"""
import os

import onnxruntime as ort

print("onnxruntime", ort.__version__)


def find_plugin_lib():
    """Path to libmigraphx-ep.so. Env override wins, else the installed package."""
    if os.environ.get("MIGRAPHX_EP_LIB"):
        return os.environ["MIGRAPHX_EP_LIB"]
    import onnxruntime_ep_migraphx  # shipped by the EP wheel
    return onnxruntime_ep_migraphx.get_library_path()


EP = "MIGraphXExecutionProvider"
lib = find_plugin_lib()
print("plugin library:", lib)

# Registering is idempotent-ish: a second call raises "already registered".
try:
    ort.register_execution_provider_library(EP, lib)
except Exception as e:
    if "already registered" not in str(e).lower():
        raise

for d in ort.get_ep_devices():
    hw = d.device
    arch = d.ep_metadata.get("arch") if hasattr(d, "ep_metadata") else None
    print(f"- ep_name={d.ep_name!r} vendor={d.ep_vendor!r} "
          f"hw_type={hw.type} arch={arch}")

if not any(d.ep_name == EP for d in ort.get_ep_devices()):
    print("WARNING: no MIGraphXExecutionProvider device. Check GPU discovery / env.sh.")
