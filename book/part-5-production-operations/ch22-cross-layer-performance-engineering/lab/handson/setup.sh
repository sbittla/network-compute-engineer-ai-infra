#!/usr/bin/env bash
# Ch 22 hands-on setup: the shared PyTorch venv plus iproute2 (ip, tc + netem), taskset and ping. Idempotent.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
# sudo resets PATH (secure_path); WSL2 keeps nvidia-smi in /usr/lib/wsl/lib.
[ -d /usr/lib/wsl/lib ] && export PATH="$PATH:/usr/lib/wsl/lib"
need_root
need_gpu
missing=()
command -v ip >/dev/null && command -v tc >/dev/null || missing+=(iproute2)
command -v taskset >/dev/null || missing+=(util-linux)
command -v ping >/dev/null || missing+=(iputils-ping)
command -v flock >/dev/null || missing+=(util-linux)
if [ "${#missing[@]}" -gt 0 ]; then
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${missing[@]}" >/dev/null
fi
modprobe sch_netem 2>/dev/null || true
. "$ROOT/scripts/handson/venv.sh"
"$HANDSON_PY" -c "import torch, numpy; assert torch.cuda.is_available(); print('torch', torch.__version__, 'numpy', numpy.__version__, torch.cuda.get_device_name())"
# netem works in a throwaway namespace?
ip netns add ch22-probe
ip -n ch22-probe link add ch22-pa type veth peer name ch22-pb
if ip netns exec ch22-probe tc qdisc add dev ch22-pa root netem delay 1ms 2>/dev/null; then
  ip netns del ch22-probe; echo "netem OK"
else
  ip netns del ch22-probe
  die "tc netem is unavailable (CONFIG_NET_SCH_NETEM, module sch_netem). Stock Ubuntu and WSL2 kernels load it on demand;
a custom kernel needs its modules installed or NETEM built in."
fi
echo "CPUs: $(nproc); the lab pins the job to CPUs ${CH22_CPUS_A:-8-11} (and ${CH22_CPUS_B:-12-15} for the fix)"
echo "$(ip -V); $(taskset --version)"
echo "setup OK"
