#!/usr/bin/env bash
# One-time fixup for the in-tree MIGraphX venv.
#   bash ep-intree-vs-plugin/exp/fixup_intree_mgx.sh
#
# The ROCm 7.14 migraphx_libs wheel ships versioned sonames (libmigraphx_gpu.so.2016000),
# but MIGraphX's dynamic_loader dlopen()s the UNVERSIONED names (libmigraphx_gpu.so).
# Create the unversioned symlinks so the GPU target can load. Analogous to the
# libonnxruntime.so.1 symlink the plugin venv needs.
set -eu

ML=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/.venv-intree-mgx/lib/python3.12/site-packages/migraphx_libs

for f in libmigraphx.so.2016000 libmigraphx_gpu.so.2016000 libmigraphx_ref.so.2016000 \
         libmigraphx_onnx.so.2016000 libmigraphx_tf.so.2016000; do
  [ -e "$ML/$f" ] && ln -sf "$f" "$ML/${f%.2016000}"
done
ln -sf libmigraphx_c.so.3 "$ML/libmigraphx_c.so"

echo "symlinks created in $ML:"
ls -la "$ML" | grep -E '\-> ' | grep -i migraphx
