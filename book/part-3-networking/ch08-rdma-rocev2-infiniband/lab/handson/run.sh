#!/usr/bin/env bash
# Chapter 8 hands-on lab: real RDMA verbs on Soft-RoCE, unattended. Usage: bash run.sh [run-id]
# Writes results/<run-id>/ (environment.json, raw outputs per step, summary.json, report.md).
# One rxe device (ch08rxe0) on one veth end (ch08-v0, 10.208.0.1/32); every perftest runs server and
# client on this host, in loopback through the rxe software transport.
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$LAB/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
need_cmd rdma ibv_devinfo ibv_devices ibv_rc_pingpong ib_write_bw ib_write_lat ib_read_lat ib_send_lat ip setpriv ss bc python3

DEV=ch08rxe0
NETDEV=ch08-v0
PEER=ch08-v1
IP=10.208.0.1
FINAL="$(run_dir "$LAB" "${1:-}")"
# Raw outputs are written to a local staging directory first: the repository may sit on a 9P/drvfs
# mount (WSL2 /mnt/d), where a file create can fail transiently under memory pressure.
OUT="$(mktemp -d /tmp/ch08-run.XXXXXX)"
finish() { cp -r "$OUT"/. "$FINAL"/ 2>/dev/null || true; rm -rf "$OUT"; }
bash "$LAB/teardown.sh" >/dev/null 2>&1 || true
trap 'finish; bash "$LAB/teardown.sh" >/dev/null 2>&1 || true' EXIT
log() { echo "[ch08 $(date +%T)] $*"; }
log "results -> $FINAL (staged in $OUT)"

env_manifest "$OUT/environment.json" "uname -r" "dpkg-query -W -f='\${Version}' rdma-core" \
  "dpkg-query -W -f='\${Version}' perftest" "ip -V" "ulimit -l" "nproc" \
  "zcat /proc/config.gz 2>/dev/null | grep RDMA_RXE || echo rdma_rxe module"

PORT=18501
wait_listen() { for _ in $(seq 100); do ss -Hltn "sport = :$1" | grep -q . && return 0; sleep 0.1; done; return 1; }
# pt <out-prefix> <tool> [args...]: one perftest run, server and client on ch08rxe0, client rc in <out>.rc
pt() {
  local out="$1" tool="$2"; shift 2
  local port=$PORT; PORT=$((PORT + 1)); local rc=0
  echo "\$ $tool -d $DEV -p $port $* [server]  /  ... $IP [client]" >> "$(dirname "$out")/commands.txt"
  timeout 300 "$tool" -d "$DEV" -p "$port" "$@" > "$out.server.txt" 2>&1 &
  local sp=$!
  wait_listen "$port" || true
  timeout 300 "$tool" -d "$DEV" -p "$port" "$@" "$IP" > "$out.client.txt" 2>&1 || rc=$?
  wait "$sp" 2>/dev/null || true
  echo "$rc" > "$out.rc"
}
set_mtu() { ip link set "$NETDEV" mtu "$1"; ip link set "$PEER" mtu "$1"; sleep 0.5; }
stat_get() { rdma statistic show link "$DEV/1" | grep -o "$1 [0-9]*" | awk '{print $2}'; }

# ---------------------------------------------------------------- Step 1: build a Soft-RoCE device
log "Step 1: veth $NETDEV + rxe $DEV; rdma link, ibv_devinfo -v"
S="$OUT/step1-device"; mkdir -p "$S"
{ echo "\$ ibv_devices   (before)"; ibv_devices 2>&1 || true; } > "$S/ibv_devices-before.txt"
ip link add "$NETDEV" type veth peer name "$PEER"
ip addr add "$IP/32" dev "$NETDEV"
ip link set "$NETDEV" up; ip link set "$PEER" up
rdma link add "$DEV" type rxe netdev "$NETDEV"
sleep 1
{ echo "\$ rdma link show"; rdma link show; echo "\$ rdma dev show $DEV"; rdma dev show "$DEV"; } > "$S/rdma-link.txt"
{ echo "\$ ibv_devices"; ibv_devices; } > "$S/ibv_devices.txt"
ibv_devinfo -v -d "$DEV" > "$S/ibv_devinfo-v.txt"
ip -d link show "$NETDEV" > "$S/ip-link.txt"

# ---------------------------------------------------------------- Step 2: the GID table and a first RC QP
log "Step 2: GID table (sysfs) and ibv_rc_pingpong"
S="$OUT/step2-gids"; mkdir -p "$S"
P=/sys/class/infiniband/$DEV/ports/1
{
  echo "index gid type ndev"
  for g in "$P"/gids/*; do
    i="$(basename "$g")"; v="$(cat "$g" 2>/dev/null || true)"
    [ -z "$v" ] || [ "$v" = "0000:0000:0000:0000:0000:0000:0000:0000" ] && continue
    echo "$i $v $(cat "$P/gid_attrs/types/$i" 2>/dev/null | tr ' ' '_') $(cat "$P/gid_attrs/ndevs/$i" 2>/dev/null)"
  done | sort -n
} > "$S/gid-table.txt"
echo "\$ ibv_rc_pingpong -d $DEV -g 1 -n 1000 [server] / ... $IP [client]" > "$S/commands.txt"
timeout 60 ibv_rc_pingpong -d "$DEV" -g 1 -n 1000 -p 18500 > "$S/rc_pingpong.server.txt" 2>&1 &
sp=$!; wait_listen 18500 || true
rc=0; timeout 60 ibv_rc_pingpong -d "$DEV" -g 1 -n 1000 -p 18500 "$IP" > "$S/rc_pingpong.client.txt" 2>&1 || rc=$?
wait "$sp" 2>/dev/null || true; echo "$rc" > "$S/rc_pingpong.rc"

# ---------------------------------------------------------------- Step 3: bandwidth vs size at two netdev MTUs
log "Step 3: ib_write_bw -a at netdev MTU 1500 and 9000, 3 interleaved repetitions"
S="$OUT/step3-bandwidth"; mkdir -p "$S"
for m in 1500 9000; do set_mtu "$m"; ibv_devinfo -d "$DEV" > "$S/ibv_devinfo-netdev$m.txt"; done
for rep in 1 2 3; do
  for m in 1500 9000; do
    set_mtu "$m"
    pt "$S/write_bw_netdev${m}_rep$rep" ib_write_bw -x 1 -F -a -n 1000 --report_gbits
  done
done
# Packets per 64 KiB WRITE, from the rxe port counters (loopback: one port counts data and ACKs)
for m in 1500 9000; do
  set_mtu "$m"
  b="$(stat_get sent_pkts)"
  pt "$S/pkts_netdev$m" ib_write_bw -x 1 -F -s 65536 -n 10000
  a="$(stat_get sent_pkts)"
  echo "netdev_mtu=$m messages=10000 size=65536 sent_pkts_before=$b sent_pkts_after=$a" > "$S/pkts_netdev$m.counters.txt"
done
# A QP caught mid-test: rdma resource shows its number, type and state
set_mtu 9000
port=$PORT; PORT=$((PORT + 1))
timeout 60 ib_write_bw -d "$DEV" -x 1 -F -s 65536 -D 4 -p "$port" > "$S/qp_snapshot.server.txt" 2>&1 &
sp=$!; wait_listen "$port" || true
timeout 60 ib_write_bw -d "$DEV" -x 1 -F -s 65536 -D 4 -p "$port" "$IP" > "$S/qp_snapshot.client.txt" 2>&1 &
cp=$!; sleep 2.5
{ echo "\$ rdma resource show qp link $DEV/1"; rdma resource show qp link "$DEV/1"; } > "$S/rdma-res-qp.txt" 2>&1
wait "$cp" 2>/dev/null || true; wait "$sp" 2>/dev/null || true

# ---------------------------------------------------------------- Step 4: latency
log "Step 4: ib_write_lat, ib_read_lat, ib_send_lat -a (netdev MTU 9000)"
S="$OUT/step4-latency"; mkdir -p "$S"
for t in ib_write_lat ib_read_lat ib_send_lat; do pt "$S/${t#ib_}" "$t" -x 1 -F -a; done

# ---------------------------------------------------------------- Step 5: path MTU
log "Step 5: path MTU 256..4096 at netdev MTU 9000; -m 4096 at netdev MTU 1500"
S="$OUT/step5-mtu"; mkdir -p "$S"
set_mtu 9000
for rep in 1 2; do
  for pm in 256 512 1024 2048 4096; do
    b="$(stat_get sent_pkts)"
    pt "$S/path_mtu${pm}_rep$rep" ib_write_bw -x 1 -F -s 1048576 -D 3 -m "$pm" --report_gbits
    a="$(stat_get sent_pkts)"
    echo "sent_pkts_before=$b sent_pkts_after=$a" > "$S/path_mtu${pm}_rep$rep.counters.txt"
  done
done
set_mtu 1500
pt "$S/netdev1500_ask4096" ib_write_bw -x 1 -F -s 1048576 -D 3 -m 4096 --report_gbits
set_mtu 9000

# ---------------------------------------------------------------- Step 6: things that go wrong
log "Step 6: wrong device, no server, wrong GID index, locked-memory limit"
S="$OUT/step6-failures"; mkdir -p "$S"
rc=0; timeout 20 ib_write_bw -d mlx5_0 -x 1 -F -p 18590 "$IP" > "$S/wrong_device.client.txt" 2>&1 || rc=$?
echo "$rc" > "$S/wrong_device.rc"; echo "\$ ib_write_bw -d mlx5_0 -x 1 -F -p 18590 $IP" >> "$S/commands.txt"
rc=0; timeout 20 ib_write_bw -d "$DEV" -x 1 -F -p 18591 "$IP" > "$S/no_server.client.txt" 2>&1 || rc=$?
echo "$rc" > "$S/no_server.rc"; echo "\$ ib_write_bw -d $DEV -x 1 -F -p 18591 $IP   (no server)" >> "$S/commands.txt"
# GID index 7 is an empty table entry; on the client only, then on both ends
port=$PORT; PORT=$((PORT + 1))
timeout 20 ib_write_bw -d "$DEV" -x 1 -F -s 65536 -n 1000 -p "$port" > "$S/gid7_client_only.server.txt" 2>&1 &
sp=$!; wait_listen "$port" || true
rc=0; timeout 20 ib_write_bw -d "$DEV" -x 7 -F -s 65536 -n 1000 -p "$port" "$IP" > "$S/gid7_client_only.client.txt" 2>&1 || rc=$?
wait "$sp" 2>/dev/null || true; echo "$rc" > "$S/gid7_client_only.rc"
echo "\$ ib_write_bw -d $DEV -x 1 ... [server] / ib_write_bw -d $DEV -x 7 ... $IP [client]" >> "$S/commands.txt"
pt "$S/gid7_both" ib_write_bw -x 7 -F -s 65536 -n 1000
pt "$S/gid0_linklocal" ib_write_bw -x 0 -F -s 65536 -n 1000
# Locked memory: an 8 MiB buffer registered by an unprivileged server under several RLIMIT_MEMLOCK values
for lim in 4096 8192 16384 65536; do
  port=$PORT; PORT=$((PORT + 1))
  setpriv --reuid=65534 --regid=65534 --clear-groups bash -c \
    "ulimit -l $lim; echo \"ulimit -l = \$(ulimit -l) KiB, uid \$(id -u)\"; exec timeout 30 ib_write_bw -d $DEV -x 1 -F -s 8388608 -n 20 -p $port" \
    > "$S/memlock_nobody_$lim.server.txt" 2>&1 &
  sp=$!; wait_listen "$port" || true
  rc=0; timeout 30 ib_write_bw -d "$DEV" -x 1 -F -s 8388608 -n 20 -p "$port" "$IP" > "$S/memlock_nobody_$lim.client.txt" 2>&1 || rc=$?
  src=0; wait "$sp" 2>/dev/null || src=$?; echo "$src $rc" > "$S/memlock_nobody_$lim.rc"   # server rc, client rc
  echo "\$ setpriv --reuid=65534 ... bash -c 'ulimit -l $lim; ib_write_bw -d $DEV -x 1 -F -s 8388608 -n 20' [server]" >> "$S/commands.txt"
done
# The same 4 MiB-limited server as root: CAP_IPC_LOCK bypasses the limit
port=$PORT; PORT=$((PORT + 1))
bash -c "ulimit -l 4096; echo \"ulimit -l = \$(ulimit -l) KiB, uid \$(id -u)\"; exec timeout 30 ib_write_bw -d $DEV -x 1 -F -s 8388608 -n 20 -p $port" \
  > "$S/memlock_root_4096.server.txt" 2>&1 &
sp=$!; wait_listen "$port" || true
rc=0; timeout 30 ib_write_bw -d "$DEV" -x 1 -F -s 8388608 -n 20 -p "$port" "$IP" > "$S/memlock_root_4096.client.txt" 2>&1 || rc=$?
src=0; wait "$sp" 2>/dev/null || src=$?; echo "$src $rc" > "$S/memlock_root_4096.rc"
dmesg 2>/dev/null | grep -E "$DEV.*(reg_user_mr|err)" | tail -20 > "$S/dmesg-rxe.txt" || true

# ---------------------------------------------------------------- Step 7: the peer vanishes (ACK timeout)
log "Step 7: kill the responder mid-transfer; measure the retry interval and the time to failure"
S="$OUT/step7-ack-timeout"; mkdir -p "$S"
sample() {  # sample <csv> <seconds>: completer_retry_err and retry_exceeded_err every 50 ms
  local end; end=$(echo "$(date +%s.%N) + $2" | bc)
  echo "t_s,completer_retry_err,retry_exceeded_err" > "$1"
  while [ "$(echo "$(date +%s.%N) < $end" | bc)" = 1 ]; do
    echo "$(date +%s.%N),$(stat_get completer_retry_err),$(stat_get retry_exceeded_err)" >> "$1"; sleep 0.05
  done
}
for u in 14 16; do
  port=$PORT; PORT=$((PORT + 1))
  timeout 120 ib_write_bw -d "$DEV" -x 1 -F -s 65536 -n 2000000 -u "$u" -p "$port" > "$S/u$u.server.txt" 2>&1 &
  wait_listen "$port" || true
  srv="$(pgrep -f "^ib_write_bw -d $DEV .*-p $port\$" || true)"
  timeout 120 ib_write_bw -d "$DEV" -x 1 -F -s 65536 -n 2000000 -u "$u" -p "$port" "$IP" > "$S/u$u.client.txt" 2>&1 &
  cp=$!; sleep 2
  echo "kill_t_s=$(date +%s.%N)" > "$S/u$u.events.txt"; kill -9 "$srv"
  sample "$S/u$u.samples.csv" $([ "$u" = 14 ] && echo 4 || echo 8)
  { echo "client_alive_after_sampling=$(kill -0 "$cp" 2>/dev/null && echo yes || echo no)"; } >> "$S/u$u.events.txt"
  pkill -9 -f "^ib_write_bw -d $DEV .*-p $port $IP\$" 2>/dev/null || true
  wait "$cp" 2>/dev/null || true
  echo "\$ ib_write_bw -d $DEV -x 1 -F -s 65536 -n 2000000 -u $u -p $port [server, killed after 2 s] / ... $IP [client]" >> "$S/commands.txt"
done
# rdma_cm connection setup lets perftest set retry_cnt: 3 retries, then the QP must fail
port=$PORT; PORT=$((PORT + 1))
timeout 120 ib_write_bw -d "$DEV" -R --retry_count=3 -F -s 65536 -n 2000000 -p "$port" > "$S/cm_retry3.server.txt" 2>&1 &
sleep 1.5
srv="$(pgrep -f "^ib_write_bw -d $DEV -R .*-p $port\$" || true)"
b="$(stat_get retry_exceeded_err)"
timeout 120 ib_write_bw -d "$DEV" -R --retry_count=3 -F -s 65536 -n 2000000 -p "$port" "$IP" > "$S/cm_retry3.client.txt" 2>&1 &
cp=$!; sleep 2
k=$(date +%s.%N); kill -9 "$srv"
rc=0; wait "$cp" || rc=$?
e=$(date +%s.%N)
echo "kill_t_s=$k client_exit_t_s=$e client_rc=$rc retry_exceeded_before=$b retry_exceeded_after=$(stat_get retry_exceeded_err)" > "$S/cm_retry3.events.txt"
echo "\$ ib_write_bw -d $DEV -R --retry_count=3 -F -s 65536 -n 2000000 -p $port [server, killed after 2 s] / ... $IP [client]" >> "$S/commands.txt"
{ echo "\$ rdma statistic show link $DEV/1"; rdma statistic show link "$DEV/1"; } > "$OUT/counters-final.txt"

# ---------------------------------------------------------------- Summary
log "Summarize"
bash "$LAB/teardown.sh"
trap - EXIT
finish
python3 "$LAB/ch08_analyze.py" "$FINAL"
log "done: $FINAL"
