"""Look at what an OrtValue is: bytes with a shape, a type, and a location (CPU or device).

    $LPY ep-plugin-from-source/exp/inspect_ortvalue.py

No MIGraphX needed; this is pure onnxruntime + numpy.
"""
import numpy as np
import onnxruntime as ort

a = np.arange(12, dtype=np.float16).reshape(3, 4)
print("numpy array:")
print(a)
print("  dtype", a.dtype, "shape", a.shape, "C-contiguous", a.flags["C_CONTIGUOUS"])
print("  strides (bytes):", a.strides, " -> step to next row =", a.strides[0], "bytes = 4 fp16 values")

# An OrtValue is onnxruntime's tensor. from_numpy keeps the same bytes.
ov = ort.OrtValue.ortvalue_from_numpy(a)
print("\nOrtValue:")
print("  shape", ov.shape())
print("  data type", ov.data_type())
print("  device", ov.device_name())            # 'cpu' here
print("  back to numpy equal:", np.array_equal(ov.numpy(), a))

# A non-contiguous view: every other column. The bytes do not move; the strides describe the gaps.
view = a[:, ::2]
print("\nstrided view a[:, ::2]:")
print(view)
print("  shape", view.shape, "strides (bytes)", view.strides, "C-contiguous", view.flags["C_CONTIGUOUS"])
print("  elements =", view.size, " but it points into the original", a.size, "-element buffer")
print("\nTakeaway: a tensor is (bytes) + (shape) + (strides) + (where it lives).")
print("A buffer's size in bytes is NOT always shape-product * itemsize when strides have gaps.")
