#!/usr/bin/env bash
# Ch 4 hands-on setup: the shared PyTorch venv and (optionally) Nsight Systems. Idempotent.
#   bash setup.sh                 # venv + Nsight Systems CLI (about 420 MB download, once)
#   CH04_NSYS=0 bash setup.sh     # venv only; the lab then skips the Nsight Systems steps
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
need_gpu
need_cmd python3 flock curl

# Pinned Nsight Systems build from NVIDIA's CUDA repository (the WSL-Ubuntu and Ubuntu repos carry the same .deb).
NSYS_VER="2025.6.3"
NSYS_DEB="nsight-systems-2025.6.3_2025.6.3.541-1_amd64.deb"
NSYS_URL="https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/$NSYS_DEB"
CACHE=/var/cache/ch04-handson

. "$ROOT/scripts/handson/venv.sh"
"$HANDSON_PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible to PyTorch'; print('torch', torch.__version__, 'cuda', torch.version.cuda, torch.cuda.get_device_name())"

if [ "${CH04_NSYS:-1}" = "1" ]; then
  if command -v nsys >/dev/null && nsys --version | grep -q "$NSYS_VER"; then
    echo "nsys already installed: $(nsys --version)"
  else
    need_root
    mkdir -p "$CACHE"
    [ -s "$CACHE/$NSYS_DEB" ] || curl -sSfL -o "$CACHE/$NSYS_DEB" "$NSYS_URL"
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$CACHE/$NSYS_DEB" >/dev/null
    echo "installed: $(nsys --version)"
  fi
  nsys status -e | sed -n '1,4p' || true
else
  echo "CH04_NSYS=0: skipping Nsight Systems; run.sh will skip the nsys steps"
fi
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
echo "setup OK"
