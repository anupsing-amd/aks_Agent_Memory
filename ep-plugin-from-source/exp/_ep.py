"""Shared helpers for the ep-plugin-from-source experiments: find and register the MIGraphX plugin EP."""
import os

import onnxruntime as ort

EP = "MIGraphXExecutionProvider"


def find_plugin_lib():
    """Path to libmigraphx-ep.so. MIGRAPHX_EP_LIB overrides; else the installed wheel."""
    if os.environ.get("MIGRAPHX_EP_LIB"):
        return os.environ["MIGRAPHX_EP_LIB"]
    import onnxruntime_ep_migraphx
    return onnxruntime_ep_migraphx.get_library_path()


def register():
    """Register the plugin library (safe to call more than once). Returns the path."""
    lib = find_plugin_lib()
    try:
        ort.register_execution_provider_library(EP, lib)
    except Exception as e:
        if "already registered" not in str(e).lower():
            raise
    return lib


def migraphx_device():
    """The OrtEpDevice for the MIGraphX EP, or None if the GPU was not discovered."""
    for d in ort.get_ep_devices():
        if d.ep_name == EP:
            return d
    return None
