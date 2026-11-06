#!/usr/bin/env bash
# Chapter 21 hands-on lab: check the GPU and prepare the shared PyTorch environment. Idempotent.
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$LAB/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_gpu
need_cmd flock python3
. "$ROOT/scripts/handson/venv.sh"   # creates ~/.venvs/ai-infra-handson (pinned torch 2.5.1+cu124) on first use
echo "nvidia-smi: $(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader)"
"$HANDSON_PY" - <<'PY'
import torch
assert torch.cuda.is_available(), "PyTorch cannot see the GPU"
p = torch.cuda.get_device_properties(0)
print(f"torch {torch.__version__} (CUDA {torch.version.cuda}); {p.name}, sm_{p.major}{p.minor}, {p.multi_processor_count} SMs, {p.total_memory / 2**30:.1f} GiB")
assert torch.cuda.is_bf16_supported(), "this lab needs BF16 (Ampere or newer)"
PY
echo "setup OK"
