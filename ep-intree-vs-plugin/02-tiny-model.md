# 02. One tiny model, two EPs

Before touching venvs, make the model. The whole point of the series is to send the *same* model through an in-tree EP and a plugin EP and see that only the attachment differs, not the result. So the model must be tiny and its answer must be predictable by hand.

## The model

`y = relu(x) + 1`, in fp16, shape `[1, 4]`. Two nodes: a `Relu`, then an `Add` of a constant `1`.

```python
nodes = [
    helper.make_node("Relu", ["x"], ["r"]),
    helper.make_node("Add", ["r", "one"], ["y"]),
]
```

Predict it by hand for `x = [-2, -0.5, 1, 3]`:

- `relu` clamps negatives to 0 -> `[0, 0, 1, 3]`
- `+ 1` -> `[1, 1, 2, 4]`

So the correct output is `[[1.0, 1.0, 2.0, 4.0]]`, whatever EP runs it. Hold that number; you will check both runs against it.

## Experiment: write the model

This needs `numpy` and `onnx`, which you will install into the first venv in lecture 03. If you want to run it right now with any existing venv that has those, you can; otherwise wait for lecture 03 to install them, then come back and run:

```bash
cd /scratch/anupsing/migraphx/aks_Agent_Memory/ep-intree-vs-plugin
<some-python-with-onnx> exp/make_tiny_model.py
```

Expected:

```text
wrote .../ep-intree-vs-plugin/exp/tiny.onnx
meaning: y = max(x, 0) + 1
```

Read [exp/make_tiny_model.py](exp/make_tiny_model.py). It is ~25 lines: build two nodes, name the input `x` and output `y`, bake in the constant `one`, save `tiny.onnx`.

You can stop here. Lecture 03 builds the in-tree venv and actually runs this.
