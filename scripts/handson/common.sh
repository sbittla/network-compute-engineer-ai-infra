# Shared helpers for the single-machine hands-on labs (docs/HANDS_ON_LABS.md). Source it from a lab script:
#   . "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/scripts/handson/common.sh"
set -euo pipefail

HANDSON_GPU_LOCK=/tmp/handson-gpu.lock
HANDSON_DOCKER_LOCK=/tmp/handson-docker.lock

die() { echo "ERROR: $*" >&2; exit 1; }
need_root() { [ "$(id -u)" -eq 0 ] || die "this step needs root: run with sudo"; }
# sudo resets PATH, which drops WSL2's /usr/lib/wsl/lib (where nvidia-smi lives); put it back.
[ -d /usr/lib/wsl/lib ] && case ":$PATH:" in *:/usr/lib/wsl/lib:*) ;; *) export PATH="$PATH:/usr/lib/wsl/lib" ;; esac
need_gpu() { command -v nvidia-smi >/dev/null && nvidia-smi -L >/dev/null 2>&1 || die "no NVIDIA GPU visible (nvidia-smi failed)"; }
need_docker() { docker info >/dev/null 2>&1 || die "Docker is not running"; }
need_cmd() { for c in "$@"; do command -v "$c" >/dev/null || die "missing command: $c (run setup.sh)"; done; }

# One GPU job at a time on the shared card; one cluster/fabric bring-up at a time on Docker.
with_gpu_lock() { flock "$HANDSON_GPU_LOCK" "$@"; }
with_docker_lock() { flock "$HANDSON_DOCKER_LOCK" "$@"; }

# environment.json for an evidence bundle: env_manifest <out-file> [extra tool commands...]
env_manifest() {
  local out="$1"; shift
  python3 - "$out" "$@" <<'PY'
import json, os, platform, shutil, subprocess, sys, datetime
out, extra = sys.argv[1], sys.argv[2:]
def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"unavailable: {e}"
env = {
    "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "kernel": platform.release(),
    "os": sh("grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\"'"),
    "wsl": "microsoft" in platform.release().lower() or os.path.exists("/dev/dxg"),
    "cpu": sh("lscpu | grep 'Model name' | sed 's/.*: *//'"),
    "cpus": os.cpu_count(),
    "mem_gib": round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30, 1),
    "gpu": sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader") if shutil.which("nvidia-smi") else None,
    "python": platform.python_version(),
    "tools": {c: sh(c) for c in extra},
}
json.dump(env, open(out, "w"), indent=2)
PY
}

# results/<run-id>/ under the lab: run_dir <lab-dir> [run-id]
run_dir() { local d="$1/results/${2:-$(hostname)-$(date +%Y%m%d-%H%M%S)}"; mkdir -p "$d"; echo "$d"; }
