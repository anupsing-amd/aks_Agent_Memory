"""Build a tiny ONNX model: y = relu(x) + 1, fp16, shape [1, 4].

Writes ep-intree-vs-plugin/exp/tiny.onnx. Used by run_intree_cpu.py and run_plugin_mgx.py.
Small on purpose: one easy-to-predict output so you can check the EP by hand.
"""
import os

import numpy as np
from onnx import TensorProto, helper, numpy_helper, save

SHAPE = [1, 4]
nodes = [
    helper.make_node("Relu", ["x"], ["r"]),
    helper.make_node("Add", ["r", "one"], ["y"]),
]
graph = helper.make_graph(
    nodes,
    "tiny",
    [helper.make_tensor_value_info("x", TensorProto.FLOAT16, SHAPE)],
    [helper.make_tensor_value_info("y", TensorProto.FLOAT16, SHAPE)],
    [numpy_helper.from_array(np.array([1], np.float16), "one")],
)
model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
model.ir_version = 9

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiny.onnx")
save(model, out)
print("wrote", out)
print("meaning: y = max(x, 0) + 1")
