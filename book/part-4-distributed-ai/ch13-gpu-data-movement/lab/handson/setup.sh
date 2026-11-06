#!/usr/bin/env bash
# Chapter 13 hands-on lab: check the GPU and prepare the shared PyTorch environment, then print the versions.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_gpu
need_cmd flock nvidia-smi
. "$ROOT/scripts/handson/venv.sh"   # shared PyTorch venv: torch 2.5.1+cu124, numpy 2.1.3 (pinned there)

echo "python:  $("$HANDSON_PY" --version)"
echo "torch:   $("$HANDSON_PY" -c 'import torch; print(torch.__version__, "cuda", torch.version.cuda)')"
echo "numpy:   $("$HANDSON_PY" -c 'import numpy; print(numpy.__version__)')"
echo "gpu:     $(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader)"
echo "cpus:    $(nproc)"
echo "shm:     $(df -h /dev/shm | awk 'NR==2 {print $2 " /dev/shm (DataLoader workers pass batches through it)"}')"
echo "setup complete"
