#!/bin/bash
# Prove the assembled onnxrt_home before the big EP build:
#   1) compile + link + run abi_probe.cc against it
#   2) confirm find_package(onnxruntime) resolves
set -euo pipefail
J=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
HOME_DIR=${HOME_DIR:-$J/onnxrt_home}
WORK=$J/build-ort-home
export PATH=/scratch/anupsing/migraphx/.venv/bin:$PATH   # a recent cmake

echo "=== 1. ABI probe (compile, link, run) ==="
g++ "$J/ep-plugin-from-source/exp/abi_probe.cc" -I"$HOME_DIR/include" -L"$HOME_DIR/lib" -lonnxruntime \
    -Wl,-rpath,"$HOME_DIR/lib" -o "$WORK/abi_probe"
"$WORK/abi_probe"

echo; echo "=== 2. find_package(onnxruntime) ==="
T=$WORK/findtest; rm -rf "$T"; mkdir -p "$T"
cat > "$T/CMakeLists.txt" <<'EOF'
cmake_minimum_required(VERSION 3.20)
project(findtest CXX)
find_package(onnxruntime REQUIRED)
message(STATUS "onnxruntime_VERSION = ${onnxruntime_VERSION}")
EOF
cmake -S "$T" -B "$T/b" -DCMAKE_PREFIX_PATH="$HOME_DIR" 2>&1 | grep -E "onnxruntime_VERSION|Error" 
echo "gate passed"
