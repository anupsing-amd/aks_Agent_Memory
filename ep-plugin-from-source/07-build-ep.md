# 07. Compile the EP

You now have both libraries the EP compiles against:

- `--migraphx_home` from lecture 05, your MIGraphX install folder.
- `--onnxrt_home` from lecture 06, the ONNX Runtime headers plus library.

This lecture compiles the EP source into the one file lectures 01–03 were loading from a wheel: `libmigraphx-ep.so`.

## What "compile from source" means here

The EP repo is C++ text. A compiler (`clang++`, from your ROCm install) turns each `.cc` file into a `.o` file, then a linker joins those `.o` files, plus MIGraphX and ONNX Runtime, into one shared library. "Shared library" is the `.so`: a file of machine code that ONNX Runtime loads at runtime with `register_execution_provider_library`, which you already called in lecture 03.

You do not invoke the compiler yourself. Two tools do it:

- **CMake** reads `CMakeLists.txt`, checks that MIGraphX, ONNX Runtime, and ROCm exist, and writes a build plan. This is the configure step. It is fast and prints a lot of `-- Found ...` lines.
- **Ninja** carries out that plan: it compiles every `.cc` and links the `.so`. This is the slow step. The first run compiles the EP and also a few libraries the EP vendors (protobuf, onnx, abseil, flatbuffers). Later runs compile only the files you changed. Lecture 09 relies on that.

`build.sh` is a small wrapper around `tools/ci_build/build.py`. The script in this lecture calls it with four arguments, and each one answers a question the recipe asks:

| Argument | Question it answers |
|---|---|
| `--onnxrt_home onnxrt_home` | Where are the ONNX Runtime headers and library? |
| `--use_migraphx --migraphx_home AMDMIGraphX_install` | Build the MIGraphX EP, and where is MIGraphX installed? |
| `--hip_path rocm-10.1.0` | Where is the ROCm/HIP compiler and runtime? HIP is how this code talks to the GPU. |
| `--build_wheel` | After the `.so` exists, also zip it into a Python wheel. |

`--compile_no_warning_as_error` is there because the third-party code the build downloads has warnings, and the default is to treat every warning as a failed build.

## What you get back

Two files:

```text
build.EP.MGX/Release/src/migraphx/libmigraphx-ep.so
build.EP.MGX/Release/dist/onnxruntime_ep_migraphx-1.0.0-cp312-cp312-manylinux_2_28_x86_64.whl
```

The `.so` is the EP. The wheel is a zip with that `.so` plus a short `__init__.py`. The Python file's only job is to answer "where is the `.so`?" through `get_library_path()`, so registration stays a one-liner. The wheel from ROCm and the wheel you just built are the same kind of package. Yours is simply built on this machine from this source tree.

While packaging the wheel, the script runs `patchelf` to write a search path into the `.so` so it can find `libonnxruntime.so` and the MIGraphX libraries next to it at runtime. If `patchelf` is missing, that step exits with code 1 and prints nothing, because the build script catches the error and discards the message. `build_ep.sh` installs `patchelf` first so you do not hit that.

## Experiment: compile

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
bash ep-plugin-from-source/exp/build_ep.sh
```

The first run takes several minutes. Most of that time is protobuf and onnx, not the EP itself. It is done when the script prints both paths.

## Experiment: run lecture 03's model on the file you just built

Lecture 03 loaded whatever `libmigraphx-ep.so` the wheel shipped. The helper [exp/_ep.py](exp/_ep.py) checks the environment variable `MIGRAPHX_EP_LIB` first. Point it at your file and rerun the same script:

```bash
cd ep-plugin-from-source
source env-learn.sh
export MIGRAPHX_EP_LIB=$(find ../build.EP.MGX -name libmigraphx-ep.so | head -1)
"$LPY" exp/run_mgx.py
```

```text
registered: .../build.EP.MGX/Release/src/migraphx/libmigraphx-ep.so
providers: ['MIGraphXExecutionProvider', 'CPUExecutionProvider']
y   = [[1.0, 1.0, 2.0, 4.0]] (from the MIGraphX EP)
match: True
ran on MIGraphX EP: True
```

`registered:` must be your build path. `match: True` means your compiled EP produced the same numbers as the CPU run from lecture 02. Same model, same inputs, your binary.

## Optional: install the wheel the way lecture 02 installed the ROCm wheel

```bash
uv venv --python 3.12 venv-ep
uv pip install --python venv-ep/bin/python --no-deps \
    build.EP.MGX/Release/dist/onnxruntime_ep_migraphx-*.whl
venv-ep/bin/python -c "import onnxruntime_ep_migraphx as m; print(m.get_library_path())"
```

That prints the installed copy of `libmigraphx-ep.so`. Running a model from that venv still needs `onnxruntime` installed there and the MIGraphX libraries on `LD_LIBRARY_PATH`, which `env-learn.sh` already sets. For the rest of the series, pointing `MIGRAPHX_EP_LIB` at the build tree is enough.

Next: open the source you just compiled and follow one tensor from CPU memory onto the GPU and back.
