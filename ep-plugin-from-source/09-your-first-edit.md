# 09. Change one line, rebuild, run

The point of this lecture is the loop you will use on every real change: edit one file, compile only what that file affects, run the same tiny model, read the result. It uses the function you just read in lecture 08.

## The edit

Open `src/onnxruntime-ep-amdgpu/src/migraphx/mgx_ep.cc` and find `GetGpuInputData`, around line 395. This is the function that copies a CPU input up to the GPU. Right after it has computed how many bytes to copy, add a print:

```cpp
    const std::size_t bytes{prog_shape.bytes()};
    auto& buf{cs.cpu_input_upload_bufs[name]};
    std::cerr << "[my-ep] uploading input '" << name << "' " << bytes
              << " bytes host->device\n";
```

`std::cerr` prints to the error stream, which you see in the terminal even when normal output is buffered. If the compiler says `cerr` is unknown, add `#include <iostream>` at the top of the file. The header is usually already visible through other headers, so try the line first.

## Why the rebuild is quick

Lecture 07's first build compiled every file because nothing existed yet. Ninja records which `.o` came from which `.cc`. You changed `mgx_ep.cc`, so the next build recompiles that one file and links `libmigraphx-ep.so` again. The protobuf and onnx libraries are already built and are left alone. That is why lectures 05 and 06 were worth doing once: CMake still knows where MIGraphX and ONNX Runtime are, and Ninja still has the rest of the objects.

```bash
cd /scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371
bash ep-plugin-from-source/exp/build_ep.sh
```

In the output, look for a line compiling `mgx_ep.cc.o` and a line linking `libmigraphx-ep.so`. You should not see it rebuilding all 600 files.

## Run the same model and read your line

```bash
cd ep-plugin-from-source
source env-learn.sh
export MIGRAPHX_EP_LIB=$(find ../build.EP.MGX -name libmigraphx-ep.so | head -1)
"$LPY" exp/run_mgx.py
```

```text
[my-ep] uploading input 'x' 8 bytes host->device
y   = [[1.0, 1.0, 2.0, 4.0]] (from the MIGraphX EP)
```

The `8` is the whole lecture in one number. Input `x` is four fp16 values, and fp16 is 2 bytes, so the upload is 8 bytes. The print fires from inside your rebuilt `.so`, on the path lecture 08 described, and the numbers still match the CPU run.

Delete the line when you are done looking at it. It runs on every inference, and you do not want it in a change you share.

## Where this leaves you

- The same kind of print in `CopyTensors` (`src/shared/hip/data_transfer.cc`) shows you which copies happen for a run: CPU to GPU, GPU to CPU, or GPU to GPU.
- The two things lecture 08 told you to watch, the byte count and which stream a copy waits on, are the shape of the bugs in this code. The 1371 ticket was a byte count decided from lengths while the shape still carried strides.
- The repo you will actually work in is [onnxruntime-ep-amdgpu](https://github.com/onnxruntime/onnxruntime-ep-amdgpu). `mgx_ep.cc`, `allocator.cc`, and `data_transfer.cc` there are the files you just read.
