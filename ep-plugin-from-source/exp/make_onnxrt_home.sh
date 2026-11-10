#!/bin/bash
# Assemble an "onnxrt_home": the ONNX Runtime headers + library + CMake package that the
# EP build needs for --onnxrt_home. No ONNX Runtime compile. The headers come from the
# matching source tag (v1.29.0), the library from the wheel you already installed.
set -euo pipefail

J=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
HOME_DIR=${HOME_DIR:-$J/onnxrt_home}
WORK=${WORK:-$J/build-ort-home}
ORT_TAG=${ORT_TAG:-v1.29.0}
WHEEL_SO=${WHEEL_SO:-$J/.venv-learn/lib/python3.12/site-packages/onnxruntime/capi/libonnxruntime.so.1.29.0}

# 1. Headers: sparse, blobless, shallow clone of just the public session headers at the matching tag.
mkdir -p "$WORK"; cd "$WORK"
if [ ! -d ortsrc/include/onnxruntime/core/session ]; then
    rm -rf ortsrc
    git clone --depth 1 --branch "$ORT_TAG" --filter=blob:none --sparse \
        https://github.com/microsoft/onnxruntime.git ortsrc
    (cd ortsrc && git sparse-checkout set include/onnxruntime/core/session)
fi
SRC=$WORK/ortsrc/include/onnxruntime/core/session

# 2. Lay out the install prefix: flat include/, lib/ with the wheel's .so, and a CMake package.
rm -rf "$HOME_DIR"; mkdir -p "$HOME_DIR/include" "$HOME_DIR/lib/cmake/onnxruntime"
cp "$SRC"/*.h "$HOME_DIR/include/"
cp "$SRC"/*.inc "$HOME_DIR/include/" 2>/dev/null || true
cp -P "$WHEEL_SO" "$HOME_DIR/lib/libonnxruntime.so.1.29.0"
ln -sf libonnxruntime.so.1.29.0 "$HOME_DIR/lib/libonnxruntime.so.1"
ln -sf libonnxruntime.so.1.29.0 "$HOME_DIR/lib/libonnxruntime.so"

cat > "$HOME_DIR/lib/cmake/onnxruntime/onnxruntimeConfig.cmake" <<'EOF'
# Minimal package so find_package(onnxruntime) works for building a plugin EP.
set(onnxruntime_VERSION 1.29.0)
get_filename_component(_ort_root "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)
add_library(onnxruntime::onnxruntime SHARED IMPORTED)
set_target_properties(onnxruntime::onnxruntime PROPERTIES
    IMPORTED_LOCATION "${_ort_root}/lib/libonnxruntime.so.1.29.0"
    IMPORTED_SONAME "libonnxruntime.so.1"
    INTERFACE_INCLUDE_DIRECTORIES "${_ort_root}/include")
EOF
cat > "$HOME_DIR/lib/cmake/onnxruntime/onnxruntimeConfigVersion.cmake" <<'EOF'
set(PACKAGE_VERSION 1.29.0)
if(PACKAGE_VERSION VERSION_LESS PACKAGE_FIND_VERSION)
  set(PACKAGE_VERSION_COMPATIBLE FALSE)
else()
  set(PACKAGE_VERSION_COMPATIBLE TRUE)
  if(PACKAGE_VERSION VERSION_EQUAL PACKAGE_FIND_VERSION)
    set(PACKAGE_VERSION_EXACT TRUE)
  endif()
endif()
EOF

echo "onnxrt_home ready at $HOME_DIR"
echo "headers: $(ls "$HOME_DIR/include" | wc -l)   lib: $(ls "$HOME_DIR/lib"/libonnxruntime.so* | wc -l)"
