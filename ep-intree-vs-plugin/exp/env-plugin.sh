# Source this to use the plugin venv (.venv-plugin).
#   source ep-intree-vs-plugin/exp/env-plugin.sh
# Sets ROCm + MIGraphX library paths and defines PY = the venv's python.
VENV_DIR=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/.venv-plugin
SP=$VENV_DIR/lib/python3.12/site-packages
export ROCM_PATH=/scratch/anupsing/migraphx/rocm-10.1.0
export PATH="$ROCM_PATH/bin:$PATH"
# migraphx_libs: the real MIGraphX runtime from the wheel (external to ORT and to the EP).
# onnxruntime/capi: holds libonnxruntime.so.1 that the plugin links against.
export LD_LIBRARY_PATH="$SP/migraphx_libs:$ROCM_PATH/lib:$ROCM_PATH/lib/rocm_sysdeps/lib:$ROCM_PATH/lib/llvm/lib:$SP/onnxruntime/capi"
export PY=$VENV_DIR/bin/python
