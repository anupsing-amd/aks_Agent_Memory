#!/bin/bash
# Turn your existing MIGraphX build into an "install": a prefix with headers and a
# CMake package config, which is what the EP build's --migraphx_home needs.
# This reads your build tree and writes to a NEW prefix. It does not change AMDMIGraphX sources.
set -euo pipefail

MGX_SRC=${MGX_SRC:-/scratch/anupsing/migraphx/AMDMIGraphX}
PREFIX=${PREFIX:-/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/AMDMIGraphX_install}
export PATH=/scratch/anupsing/migraphx/.venv/bin:$PATH   # a cmake that can read this build

echo "installing MIGraphX from $MGX_SRC/build -> $PREFIX"
cmake --install "$MGX_SRC/build" --prefix "$PREFIX"

echo
echo "CMake package:"; ls "$PREFIX/lib/cmake/migraphx"
echo "C API header:";  ls "$PREFIX/include/migraphx/migraphx.h"
echo
echo "migraphx_home = $PREFIX"
