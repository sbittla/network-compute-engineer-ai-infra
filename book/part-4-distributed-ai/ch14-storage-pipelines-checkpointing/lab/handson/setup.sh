#!/usr/bin/env bash
# Chapter 14 hands-on lab: install what the lab needs (idempotent, pinned) and print the versions.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
FIO_VERSION="3.36-1ubuntu0.1"   # Ubuntu 24.04 (noble-updates); other distributions: any fio >= 3.28 works

if ! dpkg -s fio >/dev/null 2>&1; then
  apt-get -o DPkg::Lock::Timeout=600 update -qq
  if ! DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq "fio=$FIO_VERSION" >/dev/null; then
    echo "fio $FIO_VERSION not available here; installing the distribution's fio instead" >&2
    DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq fio >/dev/null
  fi
fi

. "$ROOT/scripts/handson/venv.sh"   # shared PyTorch venv (torch 2.5.1+cu124)

echo "fio:     $(fio --version)"
echo "python:  $(python3 --version)"
echo "torch:   $("$HANDSON_PY" -c 'import torch; print(torch.__version__, "cuda", torch.version.cuda)')"
echo "dcp:     async_save available = $("$HANDSON_PY" -c 'import torch.distributed.checkpoint as d; print(hasattr(d, "async_save"))')"
if command -v nvidia-smi >/dev/null; then
  echo "gpu:     $(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader)"
else
  echo "gpu:     none visible (the checkpoint steps need an NVIDIA GPU)"
fi
echo "setup complete"
