#!/usr/bin/env bash
# Chapter 11 hands-on lab: install (idempotently) what the lab needs and print the versions.
# Everything lives in the shared venv (scripts/handson/venv.sh): PyTorch 2.5.1 (CUDA 12.4 build) with
# torchrun, gloo and NCCL. No system packages, no root, no Docker.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
. "$ROOT/scripts/handson/venv.sh"
need_cmd flock timeout
"$HANDSON_PY" - <<'PY'
import torch, torch.distributed as dist
print("torch", torch.__version__, "| gloo", dist.is_gloo_available(), "| nccl", dist.is_nccl_available(),
      "| cuda", torch.cuda.is_available(), "| nccl version", torch.cuda.nccl.version() if torch.cuda.is_available() else "-")
assert dist.is_gloo_available(), "this lab needs the gloo backend"
PY
[ -x "$HANDSON_VENV/bin/torchrun" ] || die "torchrun not found in $HANDSON_VENV"
echo "torchrun: $HANDSON_VENV/bin/torchrun"
echo "CPUs: $(nproc)  memory: $(free -m | awk '/Mem:/ {print $2}') MiB"
if nvidia-smi -L >/dev/null 2>&1; then nvidia-smi -L; else echo "no GPU: step 4 will be skipped"; fi
echo "setup OK"
