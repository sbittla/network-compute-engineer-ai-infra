#!/usr/bin/env bash
# Chapter 16 hands-on lab: install what the acceptance suite needs (idempotent, pinned) and print the versions.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
FIO_VERSION="3.36-1ubuntu0.1"   # Ubuntu 24.04 (noble-updates); other distributions: any fio >= 3.28 works
pkgs=()
dpkg -s fio >/dev/null 2>&1 || pkgs+=("fio=$FIO_VERSION")
for p in ethtool iproute2 util-linux; do dpkg -s "$p" >/dev/null 2>&1 || pkgs+=("$p"); done
if [ "${#pkgs[@]}" -gt 0 ]; then
  apt-get -o DPkg::Lock::Timeout=600 update -qq
  DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq "${pkgs[@]}" >/dev/null \
    || DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq fio ethtool iproute2 util-linux >/dev/null
fi

. "$ROOT/scripts/handson/venv.sh"   # shared PyTorch venv (torch 2.5.1+cu124)

echo "fio:        $(fio --version)"
echo "ethtool:    $(ethtool --version)"
echo "python:     $(python3 --version)"
echo "torch:      $("$HANDSON_PY" -c 'import torch; print(torch.__version__, "cuda", torch.version.cuda)')"
echo "nvidia-smi: $(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null || echo 'none: the GPU stages need an NVIDIA GPU')"
echo "dcgmi:      $(command -v dcgmi || echo 'not installed (DCGM supports data-centre GPUs on bare-metal Linux; the suite reports it N/A)')"
echo "setup complete"
