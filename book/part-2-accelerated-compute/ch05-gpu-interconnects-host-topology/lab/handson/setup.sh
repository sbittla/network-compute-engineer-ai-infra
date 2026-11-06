#!/usr/bin/env bash
# Chapter 5 hands-on lab: install the topology tools the lab reads (idempotent, pinned) and print the versions.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
need_gpu
# Ubuntu 24.04 (noble) versions; on another distribution the lab accepts that distribution's packages.
PKGS=("pciutils=1:3.10.0-2build1" "numactl=2.0.18-1ubuntu0.24.04.1" "hwloc=2.10.0-1build1")
missing=()
for p in "${PKGS[@]}"; do dpkg -s "${p%%=*}" >/dev/null 2>&1 || missing+=("$p"); done
if [ "${#missing[@]}" -gt 0 ]; then
  apt-get -o DPkg::Lock::Timeout=600 update -qq
  if ! DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq "${missing[@]}" >/dev/null; then
    echo "pinned versions not available here; installing the distribution's packages instead" >&2
    DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq "${missing[@]%%=*}" >/dev/null
  fi
fi
need_cmd taskset flock lspci numactl lstopo-no-graphics nvidia-smi

. "$ROOT/scripts/handson/venv.sh"   # shared PyTorch venv (torch 2.5.1+cu124), used by the bandwidth steps

echo "pciutils: $(dpkg-query -W -f='${Version}' pciutils)"
echo "numactl:  $(dpkg-query -W -f='${Version}' numactl)"
echo "hwloc:    $(dpkg-query -W -f='${Version}' hwloc)"
echo "procps:   $(vmstat -V | head -1)"
echo "torch:    $("$HANDSON_PY" -c 'import torch; print(torch.__version__, "cuda", torch.version.cuda)')"
if command -v nvidia-smi >/dev/null; then
  echo "gpu:      $(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader)"
else
  echo "gpu:      none visible: this lab needs an NVIDIA GPU"
fi
echo "setup complete"
