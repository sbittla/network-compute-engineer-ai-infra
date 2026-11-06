#!/usr/bin/env bash
# Chapter 9 hands-on lab: ECN and incast with tc, unattended. Usage: sudo bash run.sh [run-id]
# Writes results/<run-id>/ (environment.json, raw outputs per step, summary.json, report.md).
#   Step 1     the fabric, its base RTT and one flow through the bottleneck
#   Steps 2-6  an 8:1 incast into five queue configurations, 3 interleaved repetitions each:
#              droptail, red-ecn (the chapter's template, scaled), red-nonect (same queue, senders without
#              ECN), asfound (thresholds 10x too high), dctcp (DCTCP senders, step marking; if available)
#   Step 7     fan-in: N = 1, 4, 16 into droptail and red-ecn
# Environment overrides: CH09_SECS (incast length, default 15), CH09_REPS (default 3).
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$LAB/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
need_cmd iperf3 ethtool ip tc ping ss python3
SECS="${CH09_SECS:-15}" REPS="${CH09_REPS:-3}"
FINAL="$(run_dir "$LAB" "${1:-}")"
# Raw outputs are staged on the Linux file system first: the repository may sit on a 9P/drvfs mount
# (WSL2 /mnt/d), where many small writes are slow and a create can fail transiently.
OUT="$(mktemp -d /tmp/ch09-run.XXXXXX)"
finish() { cp -r "$OUT"/. "$FINAL"/ 2>/dev/null || true; rm -rf "$OUT"; }
bash "$LAB/teardown.sh" >/dev/null 2>&1 || true
trap 'finish; bash "$LAB/teardown.sh" >/dev/null 2>&1 || true' EXIT
log() { echo "[ch09 $(date +%T)] $*"; }
log "results -> $FINAL (staged in $OUT)"

modprobe -q tcp_dctcp 2>/dev/null || true
DCTCP=no; grep -qw dctcp /proc/sys/net/ipv4/tcp_available_congestion_control && DCTCP=yes
env_manifest "$OUT/environment.json" "uname -r" "iperf3 --version | head -1" "ip -V" "tc -V" "ethtool --version" \
  "cat /proc/sys/net/ipv4/tcp_available_congestion_control" \
  "grep -E '^(sch_tbf|sch_red|sch_netem|bridge|tcp_dctcp) ' /proc/modules | cut -d' ' -f1 | tr '\n' ' '" \
  "zcat /proc/config.gz 2>/dev/null | grep -E '^CONFIG_(NET_SCH_TBF|NET_SCH_RED|NET_SCH_NETEM|BRIDGE|TCP_CONG_DCTCP)=' | tr '\n' ' '"
log "DCTCP available: $DCTCP"

# ---------------------------------------------------------------- Step 1: the fabric
log "Step 1: namespaces, bridge, bottleneck; idle RTT; one flow"
S="$OUT/step1-fabric"; mkdir -p "$S"
bash "$LAB/net.sh" up 16 > "$S/net-up.txt"
bash "$LAB/net.sh" ecn 1
bash "$LAB/net.sh" show > "$S/fabric.txt" 2>&1
ip netns exec ch09-pr ping -D -n -i 0.02 -c 100 -Q 2 10.209.0.100 > "$S/ping_idle.txt" 2>&1
bash "$LAB/incast.sh" "$S/single-flow" 1 10 cubic

# ---------------------------------------------------------------- Steps 2-6: 8:1 incast, five configurations
log "Steps 2-6: 8:1 incast, ${SECS} s, $REPS interleaved repetitions per configuration"
S="$OUT/step2-incast"; mkdir -p "$S"
CFGS=(droptail red-ecn red-nonect asfound)
[ "$DCTCP" = yes ] && CFGS+=(dctcp)
cfg() {  # cfg <name> -> "profile ecn cc"
  case "$1" in
    droptail) echo "droptail 1 cubic" ;; red-ecn) echo "red 1 cubic" ;; red-nonect) echo "red 0 cubic" ;;
    asfound) echo "asfound 1 cubic" ;; dctcp) echo "dctcp 1 dctcp" ;;
  esac
}
one() {  # one <dir> <name> <N> <secs>
  local d="$1" name="$2" n="$3" secs="$4" prof ecn cc
  read -r prof ecn cc <<< "$(cfg "$name")"
  mkdir -p "$d"
  bash "$LAB/net.sh" queue "$prof" > "$d/queue-config.txt"
  bash "$LAB/net.sh" ecn "$ecn"
  echo "{\"config\": \"$name\", \"queue\": \"$prof\", \"tcp_ecn\": $ecn, \"cc\": \"$cc\", \"senders\": $n, \"seconds\": $secs}" > "$d/meta.json"
  bash "$LAB/incast.sh" "$d" "$n" "$secs" "$cc"
  sleep 1
}
: > "$S/order.txt"
k=${#CFGS[@]}
for rep in $(seq 1 "$REPS"); do
  for j in $(seq 0 $((k - 1))); do         # rotate the starting configuration each repetition
    name="${CFGS[$(((j + rep - 1) % k))]}"
    log "  rep $rep: $name"
    echo "${name}_rep$rep" >> "$S/order.txt"
    one "$S/${name}_rep$rep" "$name" 8 "$SECS"
  done
done

# ---------------------------------------------------------------- Step 7: fan-in
log "Step 7: fan-in N = 1, 4, 16 (droptail, red-ecn), 10 s each"
S="$OUT/step7-fanin"; mkdir -p "$S"
for n in 1 4 16; do
  for name in droptail red-ecn; do one "$S/${name}_n$n" "$name" "$n" 10; done
done

# ---------------------------------------------------------------- Summary
log "Summarize"
bash "$LAB/teardown.sh"
trap - EXIT
finish
python3 "$LAB/ch09_analyze.py" "$FINAL"
python3 "$LAB/check.py" "$FINAL" || true
log "done: $FINAL"
