#!/usr/bin/env bash
# Chapter 15 hands-on lab: install vLLM in its own venv and cache the pinned model. Idempotent.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
. "$HERE/lab.env"

need_gpu
need_cmd python3 flock curl

if [ ! -x "$CH15_VENV/bin/python" ]; then
  python3 -m venv "$CH15_VENV" 2>/dev/null || { apt-get install -y -qq python3-venv >/dev/null && python3 -m venv "$CH15_VENV"; }
fi
if ! "$CH15_VENV/bin/python" -c "import vllm,sys; sys.exit(vllm.__version__ != '$CH15_VLLM_VERSION')" 2>/dev/null; then
  echo "installing vllm==$CH15_VLLM_VERSION into $CH15_VENV (several GB; first time only)"
  "$CH15_VENV/bin/pip" install -q --upgrade "pip==25.3"
  "$CH15_VENV/bin/pip" install -q "vllm==$CH15_VLLM_VERSION"
fi

# Model weights, pinned to one revision, cached under ~/.cache/huggingface.
"$CH15_VENV/bin/python" - "$CH15_MODEL" "$CH15_MODEL_REVISION" <<'PY'
import sys
from huggingface_hub import snapshot_download
p = snapshot_download(sys.argv[1], revision=sys.argv[2],
                      allow_patterns=["*.json", "*.safetensors", "*.txt", "LICENSE"])
print("model cached at", p)
PY

"$CH15_VENV/bin/python" - <<'PY'
import importlib.metadata as m
for p in ["vllm", "torch", "transformers", "aiohttp", "huggingface_hub"]:
    print(f"{p}=={m.version(p)}")
import torch
print("cuda available:", torch.cuda.is_available(), "torch cuda:", torch.version.cuda)
PY
echo "setup OK"
