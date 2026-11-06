#!/usr/bin/env bash
# Ch 6 hands-on setup: the shared PyTorch venv (pinned in scripts/handson/venv.sh). Idempotent; nothing else to install.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
need_gpu
need_cmd python3 flock nvidia-smi
. "$ROOT/scripts/handson/venv.sh"
"$HANDSON_PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible to PyTorch'; print('torch', torch.__version__, 'cuda', torch.version.cuda, torch.cuda.get_device_name())"
nvidia-smi --query-gpu=name,driver_version,clocks.max.sm,clocks.max.memory,power.limit --format=csv
echo "setup OK"
