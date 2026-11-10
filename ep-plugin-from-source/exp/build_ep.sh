#!/bin/bash
# Build the MIGraphX plugin EP from source: libmigraphx-ep.so + a pip wheel.
# Inputs: the onnxrt_home from lecture 06, the MIGraphX install from lecture 05.
set -euo pipefail

J=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
SRC=${SRC:-$J/src/onnxruntime-ep-amdgpu}
ONNXRT_HOME=${ONNXRT_HOME:-$J/onnxrt_home}
MIGRAPHX_HOME=${MIGRAPHX_HOME:-$J/AMDMIGraphX_install}
ROCM_PATH=${ROCM_PATH:-/scratch/anupsing/migraphx/rocm-10.1.0}
BUILD_DIR=${BUILD_DIR:-$J/build.EP.MGX}
VENV=${VENV:-/scratch/anupsing/migraphx/.venv}   # a python with cmake+ninja on PATH

# Tools the build and the wheel-packaging step need in that python.
PY=$VENV/bin/python3
uv pip install --python "$PY" pip wheel build setuptools patchelf >/dev/null

export PATH=$ROCM_PATH/bin:$VENV/bin:$PATH
export ROCM_PATH
export CXXFLAGS="-D__HIP_PLATFORM_AMD__=1 -w"   # -w hushes third-party warnings

cd "$SRC"
./build.sh --config Release --cmake_generator Ninja \
  --onnxrt_home   "$ONNXRT_HOME" \
  --use_migraphx  --migraphx_home "$MIGRAPHX_HOME" \
  --hip_path      "$ROCM_PATH" \
  --compile_no_warning_as_error \
  --parallel 24 \
  --build_dir     "$BUILD_DIR" \
  --build_wheel

echo "=== outputs ==="
find "$BUILD_DIR/Release/src/migraphx" -name libmigraphx-ep.so
find "$BUILD_DIR" -name "*.whl"
