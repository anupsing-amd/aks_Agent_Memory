# 05. Put your MIGraphX build where the EP can find it

Lectures 01–04 used MIGraphX that was already installed inside a Python wheel. From here you compile the EP yourself. The EP is a C++ program. To compile it, the compiler has to be told two things about MIGraphX:

1. **Where the headers are.** A header is a `.h` file. It lists the function names the EP is allowed to call, such as "compile this graph" and "run this program". The compiler reads headers. It does not read them at runtime.
2. **Where the compiled libraries are.** A library here is a `.so` file: the MIGraphX code, already compiled. The EP links against it, which means the finished `libmigraphx-ep.so` will load those `.so` files when it runs.

You already compiled MIGraphX. The result sits in `/scratch/anupsing/migraphx/AMDMIGraphX/build`. This lecture does not compile anything again. It copies the finished public pieces into one clean folder the EP build knows how to search.

## Two folders, two jobs

**The build folder** (`AMDMIGraphX/build`) is the workshop. Compiling a big C++ project produces thousands of intermediate files: one `.o` per source file, dependency logs, and the `.so` files mixed in with all of that. It works for the people who built MIGraphX. Another project cannot reliably guess which file in there is the public library and which file is a temporary.

**The install folder** is a copy of only the public pieces, laid out the way every C++ project expects:

```text
AMDMIGraphX_install/
  include/migraphx/migraphx.h     the headers
  lib/libmigraphx*.so             the libraries
  lib/cmake/migraphx/*.cmake      a short description, explained below
```

The path of that folder is called the **prefix**. "Prefix" just means "the root I chose". Installing with prefix `/usr` would drop headers into `/usr/include`. You do not want that: it would mix your build into the system. The prefix here is a private folder, `JIRA/AIMIGRAPHX-1371/AMDMIGraphX_install`. Nothing outside that folder changes. Your MIGraphX source tree is not modified.

## What CMake is, in one pass

CMake is the program that reads a project's build recipe (a file named `CMakeLists.txt`) and writes the actual compile commands. You do not write those commands by hand. The recipe says things like "I need MIGraphX" and CMake goes and finds it.

The line the EP's recipe uses is:

```cmake
find_package(migraphx REQUIRED)
```

`find_package` means: look through a list of folders for a small text file that describes this library. For MIGraphX that file is `lib/cmake/migraphx/migraphx-config.cmake`. The file tells CMake the version, which `.so` to link, and which `include/` to use. The build folder does not have this file in that place. The install step writes it. That is the whole reason this lecture exists.

`REQUIRED` means: stop the build if you cannot find it. So if lecture 05 is skipped, lecture 07 fails immediately with "Could not find migraphx" instead of failing halfway through a long compile.

## Experiment

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
bash ep-plugin-from-source/exp/install_migraphx.sh
```

The script runs one command:

```bash
cmake --install /scratch/anupsing/migraphx/AMDMIGraphX/build \
      --prefix /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/AMDMIGraphX_install
```

`cmake --install` reads the build folder and copies the finished pieces into `--prefix`. It finishes in seconds because the compiling already happened days ago. Then the script lists the two things lecture 07 will look for:

```text
CMake package: migraphx-config.cmake  migraphx-config-version.cmake  migraphx-targets.cmake
C API header:  .../AMDMIGraphX_install/include/migraphx/migraphx.h
```

Open the header if you want to see what "a header" is: it is plain text, full of function declarations. You will not edit it.

In lecture 07 that prefix is passed as `--migraphx_home`. The EP recipe searches there, finds `migraphx-config.cmake`, and links a target called `migraphx::c` (the C API of MIGraphX, which is the surface the EP calls).

You can stop here. Next lecture does the same job for ONNX Runtime, which is missing its headers entirely.
