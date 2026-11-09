"""Show how ORT reports an in-tree EP vs a plugin EP, before and after registering.

    source ep-intree-vs-plugin/exp/env-plugin.sh     # run from the plugin venv
    $PY exp/inspect_ort.py

In-tree EPs live in get_available_providers() from the start. A plugin appears only
in get_ep_devices(), and only after register_execution_provider_library.
"""
import os

import onnxruntime as ort

EP = "MIGraphXExecutionProvider"


def plugin_lib():
    if os.environ.get("MIGRAPHX_EP_LIB"):
        return os.environ["MIGRAPHX_EP_LIB"]
    import onnxruntime_ep_migraphx
    return onnxruntime_ep_migraphx.get_library_path()


def ep_device_names():
    return sorted({d.ep_name for d in ort.get_ep_devices()})


print("onnxruntime", ort.__version__)
print()
print("=== BEFORE registering anything ===")
print("get_available_providers() (in-tree):", ort.get_available_providers())
print("get_ep_devices() ep_names          :", ep_device_names())
print("MIGraphX available by name?        :", EP in ort.get_available_providers())

lib = plugin_lib()
try:
    ort.register_execution_provider_library(EP, lib)
except Exception as e:
    if "already registered" not in str(e).lower():
        raise

print()
print("=== AFTER register_execution_provider_library ===")
print("plugin library                     :", lib)
print("get_available_providers() (in-tree):", ort.get_available_providers())
print("get_ep_devices() ep_names          :", ep_device_names())
print()
print("takeaway:")
print(" - CPUExecutionProvider was in get_available_providers() from the start (in-tree).")
print(" - MIGraphXExecutionProvider never enters that list; it shows up as an EP device")
print("   only after you load its .so. That is the whole in-tree vs plugin difference.")
