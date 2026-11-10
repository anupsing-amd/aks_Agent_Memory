# 04. Tensors, OrtValue, and IO binding

Everything the EP does is move tensors and run kernels. Before reading the EP's buffer code in lecture 08, you need a clear picture of what a tensor is and how ONNX Runtime passes one around. No MIGraphX internals here, just the data.

## A tensor is four things

A tensor is a block of numbers plus how to read it:

- **bytes**: the actual numbers in memory.
- **type**: what each number is, for example fp16 (2 bytes each).
- **shape**: the dimensions, for example `[3, 4]`.
- **strides**: how many steps in memory to move to the next element along each dimension.

Shape and strides are separate on purpose. A `[3, 4]` fp16 array that is packed has a row stride of 4 elements: the next row starts 4 values later. But you can also have a tensor whose strides leave gaps, because it points into a bigger buffer. That tensor has fewer elements than the buffer it lives in.

That gap is the whole story of the AIMIGRAPHX-1371 bug, and the reason this lecture exists. Hold the idea: **the number of elements times the item size is not always the number of bytes the buffer spans.**

## OrtValue: ONNX Runtime's tensor

In Python, ONNX Runtime wraps a tensor in an `OrtValue`. It has a shape, a type, and a location, called its device. A CPU `OrtValue` lives in normal memory. A device `OrtValue` lives on the GPU. When you call `sess.run(feed)` with plain numpy, ORT makes CPU `OrtValue`s for you, runs, and gives you numpy back.

## IO binding: you choose the buffers

Normally ORT allocates the output buffer itself. IO binding is when you hand ORT the exact input and output buffers to use, as `OrtValue`s you made. You do this to avoid copies, or to keep a tensor on the GPU across many runs. The key point for this series: with IO binding, **the output buffer must already exist at the right size before the run.** Something has to decide that size. On the GPU side, inside the EP, that decision is the bug in the ticket.

## Experiment A: look at a tensor

```bash
source ep-plugin-from-source/env-learn.sh
$LPY ep-plugin-from-source/exp/inspect_ortvalue.py
```

It prints a packed `[3, 4]` array (row stride 8 bytes = 4 fp16 values), wraps it in an `OrtValue`, then makes a strided view `a[:, ::2]`: shape `[3, 2]`, 6 elements, but still pointing into the original 12-element buffer, and not contiguous. That is the gap, in the smallest possible form.

## Experiment B: bind the output yourself

```bash
$LPY ep-plugin-from-source/exp/iobind.py
```

It runs `tiny.onnx` on the MIGraphX EP two ways: once letting ORT allocate the output, once binding a `yv` output buffer you created. Both give `[[1, 1, 2, 4]]`. The lesson is not the number, it is that `yv` had to be the right size up front. Read [exp/iobind.py](exp/iobind.py): `bind_ortvalue_output("y", yv)` is you telling ORT "write the result here."

In lecture 08 you will see the EP do exactly this on the GPU: ask ONNX Runtime for an output buffer, size it, and hand it to MIGraphX to write into. When the size and the shape disagree, the write runs off the end.

You can stop here.
