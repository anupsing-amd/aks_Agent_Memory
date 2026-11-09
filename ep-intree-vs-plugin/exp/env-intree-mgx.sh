# Source this to use the in-tree MIGraphX venv (.venv-intree-mgx).
#   source ep-intree-vs-plugin/exp/env-intree-mgx.sh
# This ORT (onnxruntime-migraphx, ROCm 7.14) has the MIGraphX EP compiled in,
# selected by name. MIGraphX itself is still external: migraphx_libs on the path.
VENV_DIR=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/.venv-intree-mgx
SP=$VENV_DIR/lib/python3.12/site-packages
export ROCM_PATH=/scratch/anupsing/migraphx/rocm-10.1.0
export PATH="$ROCM_PATH/bin:$PATH"
# migraphx_libs: the real MIGraphX (external to ORT). ROCm 10.1 supplies the HIP
# runtime: its libhiprtc.so.7 / libamdhip64.so.7 are HIP major 7, which the
# ROCm 7.14 MIGraphX build loads. onnxruntime/capi holds libonnxruntime.so.1.23.2.
export LD_LIBRARY_PATH="$SP/migraphx_libs:$ROCM_PATH/lib:$ROCM_PATH/lib/rocm_sysdeps/lib:$ROCM_PATH/lib/llvm/lib:$SP/onnxruntime/capi"
export IMPY=$VENV_DIR/bin/python
