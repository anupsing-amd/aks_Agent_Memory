# 08. Follow one tensor through the EP

Lecture 04 said a tensor is bytes, a type, a shape, and strides, and that it lives either in CPU memory or in GPU memory. This lecture is those words as C++ inside the `.so` you built. Every path below is relative to `src/onnxruntime-ep-amdgpu/`.

ONNX Runtime owns the model and the input and output tensors. MIGraphX owns the compiled program and only accepts GPU pointers. The EP stands between them. It has three jobs:

1. **Allocate.** When ONNX Runtime asks for GPU memory, return a pointer from the GPU.
2. **Copy.** When ONNX Runtime asks to move a tensor between CPU and GPU, copy the bytes.
3. **Compute.** For one fused subgraph: make sure every input pointer is on the GPU, run the MIGraphX program, and leave the outputs in the buffers ONNX Runtime allocated.

A pointer here is just an address. `hipMalloc` asks the GPU driver for memory and gives back the address. `hipFree` gives it back. `hipMemcpy` copies bytes from one address to another. The direction matters: `hipMemcpyHostToDevice` is CPU to GPU, `hipMemcpyDeviceToHost` is GPU to CPU, `hipMemcpyDeviceToDevice` stays on the GPU.

## 1. Allocate — `src/shared/hip/allocator.cc`

ONNX Runtime never calls `hipMalloc` itself. It calls the EP's allocator, and the allocator is a thin wrapper:

```cpp
// Allocator::Alloc
HIP_CALL_THROW(hipMalloc(&p, size));   // GPU memory, returned to ORT
// Allocator::Free
(void)hipFree(p);                      // ORT is done with it
```

There is a second allocator, `PinnedAllocator`, which uses `hipHostMalloc`. That is ordinary CPU memory marked so the GPU can read it faster. Copies between pinned CPU memory and the GPU skip a bounce buffer, so they are cheaper. The `(void)` in front of `hipFree` deliberately ignores the error code: this function is not allowed to throw, and an error reported by throwing would abort the process.

## 2. Copy — `src/shared/hip/data_transfer.cc`

ONNX Runtime asks "can you copy from this device to that device?" through `CanCopy` (line 11). This EP answers yes when at least one side is an AMD GPU: CPU to GPU, GPU to CPU, and GPU to GPU.

`CopyTensors` (line 33) does the copy. The pattern is the same every time. Get the destination address, get the source address, get the number of bytes, pick the direction:

```cpp
void* dst_data = dst.GetTensorMutableData<void*>();
const void* src_data = src.GetTensorData<const void*>();
const size_t bytes = src.GetTensorSizeInBytes();

hipMemcpy(dst_data, src_data, bytes, hipMemcpyHostToDevice);                  // CPU -> GPU
hipMemcpyWithStream(dst_data, src_data, bytes, hipMemcpyDeviceToHost, stream); // GPU -> CPU
```

Two details in this function are where real bugs come from.

**The byte count comes from the tensor, and the tensor can be smaller than the buffer it points into.** `GetTensorSizeInBytes()` is element count times element size. Lecture 04's strided view had 6 elements sitting inside a 12-element buffer. Copying "the tensor's bytes" and copying "the whole buffer" are different numbers. The 1371 fault is this family of bug: MIGraphX described an output with strides that covered about 20 MB, and the EP allocated the output from the element count, about 10 MB. The copy then wrote past the end of the 10 MB buffer.

**Copies and compute run on streams, and streams do not wait for each other by default.** A stream is a queue of GPU work. The EP's compute runs on its own queue. A plain `hipMemcpy` uses a different queue, the default one, and the default queue does not wait for the compute queue. So a GPU-to-CPU read uses `hipMemcpyWithStream` on the queue ONNX Runtime names (lines 78–85). Reading on the default queue can return values the GPU has not finished writing. The comments in this file describe races that have actually shipped.

## 3. Compute — `src/migraphx/mgx_ep.cc`

When ONNX Runtime runs the fused subgraph it handed to this EP, `Compute` walks every parameter of the MIGraphX program and files it as an input or an output.

**Inputs, `GetGpuInputData`, around line 395.** MIGraphX will only read a GPU address. The function asks ONNX Runtime where the tensor already is:

```cpp
const auto mem = input_tensor.GetTensorMemoryInfo();
if (mem.GetDeviceType() != OrtMemoryInfoDeviceType_CPU) {
    return const_cast<void*>(input_tensor.GetTensorRawData());  // already on the GPU
}
// Otherwise it is in CPU memory. Allocate a GPU buffer once and reuse it.
const std::size_t bytes = prog_shape.bytes();
auto& buf = cs.cpu_input_upload_bufs[name];
if (buf.data == nullptr || buf.size_bytes < bytes) {
    if (buf.data) (void)hipFree(buf.data);
    hipMalloc(&ptr, bytes);
    buf.data = ptr;
    buf.size_bytes = bytes;
}
hipMemcpyAsync(buf.data, src, bytes, hipMemcpyHostToDevice, stream);
return buf.data;
```

`prog_shape.bytes()` is the size MIGraphX computed for that parameter, which includes strides. The buffer is cached on the parameter name, so the second run of the same model reuses the allocation and only copies. `hipMemcpyAsync` enqueues the copy on the compute stream, so the copy finishes before the program reads it.

The pointer then goes to MIGraphX paired with the shape (around line 1601):

```cpp
compute_params.add(name.c_str(), migraphx::argument{prog_shape, input_data});
```

A `migraphx::argument` is lecture 04's tensor on the MIGraphX side: a shape (type, lengths, strides) plus an address. The EP's job at this line is to make the address and the shape describe the same memory.

**Outputs, around line 1610.** For each output, the EP asks ONNX Runtime for the destination tensor, giving it the lengths. ONNX Runtime allocates that tensor (through the allocator in section 1, or from a buffer you bound yourself in lecture 04) and the EP takes the address:

```cpp
auto output_tensor = kernel_context.GetOutput(output_index, tensor_shape.data(), tensor_shape.size());
void* output_data  = output_tensor.GetTensorMutableRawData();
compute_params.add(name.c_str(), migraphx::argument{argument_shape, output_data});
```

`GetOutput` is called with the lengths only. That is the line behind the 1371 bug: the allocation is sized from the lengths, while `argument_shape` still carries the strides of the view. When those two disagree, MIGraphX writes more bytes than ONNX Runtime reserved.

**Run, around line 1626.**

```cpp
auto prog_outputs = program.run_async(compute_params, hip_stream);
hipStreamSynchronize(hip_stream);
```

`run_async` enqueues the program on the EP's stream and returns before the GPU is done. Anything MIGraphX allocated itself is then copied into ONNX Runtime's output tensors with a device-to-device copy. `hipStreamSynchronize` waits until that stream is idle. It is the same rule as in the copy code: ONNX Runtime reads the outputs from another path that does not wait on this stream, so the EP waits itself.

## What to remember

The EP allocates GPU memory, copies bytes in a named direction on a named stream, and pairs every pointer with a shape before and after `run_async`. The bugs in this code are a wrong byte count, a copy that does not wait for the compute that fills it, or a pointer paired with a shape that describes a different region. The 1371 ticket is the third one, at `GetOutput`.

Next, optional: change one line, rebuild, and see your own text come out of a GPU run.
