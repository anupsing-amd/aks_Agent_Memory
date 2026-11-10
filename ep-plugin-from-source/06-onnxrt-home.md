# 06. Give the EP build a copy of ONNX Runtime it can compile against

The EP is a plugin that talks to ONNX Runtime through a published C API. Compiling the EP needs the same two things lecture 05 needed for MIGraphX:

1. ONNX Runtime **headers**, so the compiler knows the function names (`OrtGetApiBase`, `RegisterExecutionProviderLibrary`, and the rest).
2. The ONNX Runtime **library**, `libonnxruntime.so`, so the link step can point at the real code.
3. A **CMake description file**, so `find_package(onnxruntime)` succeeds. Lecture 05 explains what that sentence means.

The Python wheel you installed in lecture 02 contains only the library, buried inside `site-packages/onnxruntime/capi/`. A wheel is a zip of whatever the package needs at runtime. It ships no headers and no CMake file, because a Python user never compiles anything.

This lecture builds a folder, called `onnxrt_home`, that looks like an installed ONNX Runtime. You do **not** compile ONNX Runtime. Compiling it takes a long time and you already have a working library.

## Why the header version and the library version must be the same

A header describes an API version. The library implements an API version. If you compile against headers from version 27 and then load a library from version 29, the function layout in memory can differ. The program compiles, then crashes or reads garbage at runtime. That contract between header and library is called the ABI.

Your wheel is ONNX Runtime `1.29.0`. So the headers must be from the `1.29.0` source tag, and the library must be the wheel's `libonnxruntime.so.1.29.0`. Same number on both sides.

The folder ends up as:

```text
onnxrt_home/
  include/onnxruntime_c_api.h          headers, copied from the v1.29.0 git tag
  include/onnxruntime_cxx_api.h
  lib/libonnxruntime.so.1.29.0         the library, copied from your wheel
  lib/libonnxruntime.so.1              a name the linker expects (a symlink)
  lib/cmake/onnxruntime/onnxruntimeConfig.cmake   written by hand, ~10 lines
```

The CMake file is short because the EP only needs three facts: the version is `1.29.0`, the library file is this path, and the headers are in `include/`.

## What the script actually downloads

`make_onnxrt_home.sh` clones the ONNX Runtime git repo at tag `v1.29.0`, but only the one directory of public headers (`include/onnxruntime/core/session`). A normal clone would pull the whole compiler, the Python bindings, and years of history. A sparse, shallow clone pulls that one directory at that one tag. It is a few megabytes.

Two headers you may see mentioned in the EP repo, `onnxruntime_config.h` and `onnxruntime_typeinfo.h`, belong to the Windows DirectX provider. This build does not compile that provider, so those files are never included.

## Experiment: build the folder, then test it before the long compile

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
bash ep-plugin-from-source/exp/make_onnxrt_home.sh
bash ep-plugin-from-source/exp/abi_probe.sh
```

The first script only copies and writes files. The second script is the test, and it answers the only question that matters: do these headers and this library agree?

It compiles a 15-line C++ program, [exp/abi_probe.cc](exp/abi_probe.cc):

- The program includes `onnxruntime_c_api.h` from `onnxrt_home/include` and prints `ORT_API_VERSION`. That number is compiled into the program from the header. For these headers it is `29`.
- It then loads `libonnxruntime.so` and asks the running library two things: its version string, and whether it implements API 29.

You want:

```text
compiled against ORT_API_VERSION = 29
runtime build string             = 1.29.0
runtime provides this API version: yes
...
onnxruntime_VERSION = 1.29.0
gate passed
```

Read the three lines as: "I compiled against API 29. The library I linked is build 1.29.0. That library says it really does provide API 29." The last check asks CMake to run `find_package(onnxruntime)` against this folder, the same call lecture 07 will make. `gate passed` means both checks worked, so the long EP compile will get past the "find ONNX Runtime" step.

If the numbers ever disagree, the headers came from the wrong tag. The fix is to point `ORT_TAG` at the tag that matches the wheel. You do not need that here.

You can stop here. Next lecture is the first real compile in this series.
