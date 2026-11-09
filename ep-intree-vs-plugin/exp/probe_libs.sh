#!/usr/bin/env bash
# Look inside the libraries to see what is compiled in vs loaded externally.
#   source ep-intree-vs-plugin/exp/env-plugin.sh
#   bash exp/probe_libs.sh
# Uses the .venv-plugin site-packages so both libonnxruntime.so and the plugin are present.
set -u

SP=/scratch/anupsing/migraphx/JIRA/AIMIGRAPHX-1371/.venv-plugin/lib/python3.12/site-packages
ORT=$(ls "$SP"/onnxruntime/capi/libonnxruntime.so.1.* 2>/dev/null | head -1)
EP="$SP/onnxruntime_ep_migraphx/libmigraphx-ep.so"

echo "ORT core : $ORT"
echo "plugin   : $EP"
echo

echo "=== 1. The CPU EP name is baked INTO libonnxruntime.so (in-tree) ==="
# The CPU adapter is internal (not an exported dynamic symbol), so grep the strings.
strings "$ORT" 2>/dev/null | grep -i "CPUExecutionProvider" | sort -u | head -3
echo "(the provider name lives inside ORT itself; it resolves by name, no external lib)"
echo

echo "=== 2. MIGraphX is NOT inside libonnxruntime.so ==="
n=$(nm -D -C "$ORT" 2>/dev/null | grep -ci "migraphx")
if [ "$n" -eq 0 ]; then
  echo "0 migraphx symbols in libonnxruntime.so  <-- ORT only knows how to talk to an EP, not MIGraphX"
else
  echo "unexpected: found $n migraphx symbols in ORT core"
fi
echo

echo "=== 3. The plugin .so depends on the EXTERNAL MIGraphX libs ==="
ldd "$EP" 2>/dev/null | grep -iE "migraphx|onnxruntime" | head
echo "(libmigraphx*.so resolve from migraphx_libs, external to both ORT and the plugin)"
echo

echo "=== 4. The plugin exports the ORT plugin ABI entry points ==="
nm -D -C "$EP" 2>/dev/null | grep -iE "CreateEpFactories|ReleaseEpFactory" | head
echo "(these fixed entry points are how ORT >= 1.24 loads and drives any plugin EP)"
