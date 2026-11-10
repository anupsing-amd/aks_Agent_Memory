# Source this to use the ep-plugin-from-source environment (.venv-learn).
#   source ep-plugin-from-source/env-learn.sh
# Sets ROCm + MIGraphX library paths and defines LPY = the venv's python.
J=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
VENV_DIR=$J/.venv-learn
SP=$VENV_DIR/lib/python3.12/site-packages
export ROCM_PATH=/scratch/anupsing/migraphx/rocm-10.1.0
export PATH="$ROCM_PATH/bin:$PATH"
# migraphx_libs: MIGraphX runtime from the wheel. onnxruntime/capi: libonnxruntime.so.1 for the plugin.
# Override MGX_LIBS to point the EP at a different MIGraphX (e.g. your own build) without reinstalling.
export LD_LIBRARY_PATH="${MGX_LIBS:-$SP/migraphx_libs}:$ROCM_PATH/lib:$ROCM_PATH/lib/rocm_sysdeps/lib:$ROCM_PATH/lib/llvm/lib:$SP/onnxruntime/capi"
export LPY=$VENV_DIR/bin/python
