#!/usr/bin/env python3
"""Generate the Chapter 19 incident dataset: a synthetic ORION-XL (512 x HX8 = 4,096 GPU) training
incident with one flaky HCA link, one GPU ECC (row-remap) fault, and an NCCL timeout, plus an FMEA
register and a multi-tenant isolation configuration.  [SIMULATED]

Files written to ../data (or --out):
  rank_map.csv            rank -> node, GPU UUID/BDF, NUMA, HCA/BDF, rail, leaf switch/port, backend IP
  rank_progress.csv       per-rank flight-recorder summary at the time of the hang
  gpu_health.csv          per-GPU ECC / row-remapper snapshot (job nodes + spare pool)
  host_nic_snapshot.csv   per-HCA counters and transceiver DOM for pipeline stage 3 nodes (+ orionxl-n451)
  switch_port_counters.csv cumulative counters every 10 min for three leaves
  events.jsonl            kernel, NCCL, switch, scheduler, checkpoint events
  checkpoints.csv         checkpoint records for attempt 2
  restart_history.csv     job attempts in the last 24 h
  spares.csv              spare-pool state
  hypotheses.yaml         hypotheses raised in the incident channel
  fmea.csv                failure-mode register (with planted inconsistencies)
  tenants.yaml            tenant isolation configuration (with planted violations)
  isolation_policy.yaml   the platform's isolation policy

Deterministic (seed 19); regenerating produces byte-identical files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 19
DAY = "2026-10-20"
NODES = 512
GPUS = 8
TP, PP, DP = 8, 8, 64
GPU_BDF = ["0000:18:00.0", "0000:2a:00.0", "0000:3a:00.0", "0000:5d:00.0",
           "0000:9a:00.0", "0000:ab:00.0", "0000:ba:00.0", "0000:db:00.0"]
HCA_BDF = ["0000:19:00.0", "0000:29:00.0", "0000:3b:00.0", "0000:5c:00.0",
           "0000:9b:00.0", "0000:aa:00.0", "0000:bb:00.0", "0000:da:00.0"]
FLAKY_NODE, FLAKY_RAIL = 211, 5
ECC_NODE, ECC_GPU = 388, 3
FIRST_REPORTER = 102
AER_NODE = 450
HANG_TS = f"{DAY}T03:41:02Z"


def node_name(n: int) -> str:
    return f"orionxl-n{n + 1:03d}"


def uuid_for(node: str, gpu: int) -> str:
    h = hashlib.sha256(f"{node}/{gpu}".encode()).hexdigest()
    return f"GPU-{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def backend_ip(n: int, rail: int) -> str:
    """ORION-XL canonical host-link block 10.(130+rail).0.0/16: host side of a /31 = 10.(130+R).(n // 128).((n % 128) * 2 + 1)."""
    return f"10.{130 + rail}.{n // 128}.{(n % 128) * 2 + 1}"


def leaf_of(n: int, rail: int) -> tuple[str, str]:
    return f"orionxl-be-leaf-p{n // 32:02d}-r{rail}", f"Ethernet{n % 32 + 1}/1"


def ts(hhmmss: str) -> str:
    return f"{DAY}T{hhmmss}Z"


def gen_rank_map() -> pd.DataFrame:
    rows = []
    for n in range(NODES):
        for g in range(GPUS):
            leaf, port = leaf_of(n, g)
            rows.append((n * GPUS + g, node_name(n), g, n // DP, n % DP, uuid_for(node_name(n), g), GPU_BDF[g],
                         0 if g < 4 else 1, f"mlx5_{g}", HCA_BDF[g], g, leaf, port, backend_ip(n, g)))
    return pd.DataFrame(rows, columns=["rank", "node", "local_rank", "pp_stage", "dp_index", "gpu_uuid", "gpu_bdf",
                                       "numa", "hca", "hca_bdf", "rail", "leaf", "leaf_port", "backend_ip"])


def gen_rank_progress(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for r in range(NODES * GPUS):
        n, g = divmod(r, GPUS)
        stuck = (n // DP == FLAKY_NODE // DP) and g == FLAKY_RAIL
        done = 88212 if stuck else 88213
        enq = done + 1
        t = 3 * 3600 + 51 * 60 + 2 + rng.uniform(0.0, 7.0)  # watchdog fires ~600 s after its own last enqueue
        if n == FIRST_REPORTER and g == 1:
            t = 3 * 3600 + 51 * 60 + 1.80
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        rows.append((r, "dp" if stuck else "pp", done, enq, "waiting", f"{DAY}T{int(h):02d}:{int(m):02d}:{s:06.3f}Z"))
    return pd.DataFrame(rows, columns=["rank", "blocked_pg", "last_completed_seq", "last_enqueued_seq", "state",
                                       "watchdog_timeout_ts"])


def gen_gpu_health(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    hosts = [(node_name(n), n) for n in range(NODES)] + [(f"orionxl-s{i:02d}", None) for i in range(8)]
    for host, _ in hosts:
        for g in range(GPUS):
            sbe = int(rng.choice([0, 0, 0, 0, 0, 1, 2, 3]))
            dbe, rc, ru, pend, fail = 0, 0, 0, "No", "No"
            if host == node_name(ECC_NODE) and g == ECC_GPU:
                sbe, pend = 1412, "Yes"
            if host == node_name(45) and g == 6:      # remap applied long ago: healthy, monitor only
                sbe, rc = 4, 1
            if host == "orionxl-s00" and g == 2:            # spare that failed acceptance (see spares.csv)
                dbe, ru, fail = 2, 0, "Yes"
            rows.append((host, g, uuid_for(host, g), GPU_BDF[g], sbe, dbe, rc, ru, pend, fail))
    return pd.DataFrame(rows, columns=["node", "gpu", "gpu_uuid", "gpu_bdf", "ecc_sbe_volatile", "ecc_dbe_volatile",
                                       "remapped_rows_correctable", "remapped_rows_uncorrectable",
                                       "remap_pending", "remap_failure"])


def gen_host_nic(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    nodes = list(range(192, 256)) + [AER_NODE]
    for n in nodes:
        for g in range(GPUS):
            ld, sym, rcv, tx, rx, lat = 0, 0, 0, rng.normal(-1.6, 0.25), rng.normal(-1.9, 0.3), 0
            if n == FLAKY_NODE and g == FLAKY_RAIL:
                ld, sym, rcv, tx, rx, lat = 4, 0, 0, -5.8, -2.1, 61   # weak host transmitter (fleet ~ -1.6 dBm)
            if n in (FLAKY_NODE - 1, FLAKY_NODE + 1) and g == FLAKY_RAIL:
                lat = 23  # ring neighbours retried towards the dead peer
            rows.append((node_name(n), f"mlx5_{g}", ld, sym, rcv, round(float(tx), 2), round(float(rx), 2), lat))
    return pd.DataFrame(rows, columns=["node", "hca", "link_downed", "symbol_error", "port_rcv_errors",
                                       "module_tx_power_dbm", "module_rx_power_dbm", "local_ack_timeout_err"])


FLAPS = [("01:12:44", "01:12:58"), ("02:47:03", "02:47:09"), ("03:29:50", "03:29:55"), ("03:41:02", "03:41:16")]


def gen_switch_counters(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    leaves = [("orionxl-be-leaf-p06-r5", 5, 6), ("orionxl-be-leaf-p07-r5", 5, 7), ("orionxl-be-leaf-p03-r1", 1, 3)]
    times = pd.date_range(f"{DAY}T00:00:00Z", f"{DAY}T04:30:00Z", freq="10min")
    for leaf, rail, grp in leaves:
        for p in range(32):
            n = grp * 32 + p
            fec = sym = ld = 0
            pfc = int(rng.integers(1_000, 5_000))
            for t in times:
                pfc += int(rng.integers(2_000, 9_000))
                if n == FLAKY_NODE and rail == FLAKY_RAIL:
                    hhmm = t.strftime("%H:%M:%S")
                    prev = (t - pd.Timedelta(minutes=10)).strftime("%H:%M:%S")
                    ld = sum(1 for a, _ in FLAPS if a <= hhmm)
                    burst = any(prev < a <= hhmm for a, _ in FLAPS)
                    fec += int(rng.integers(900, 2_500)) + (40_000 if burst else 0)
                    sym += int(rng.integers(5_000, 12_000))
                    rxp = -6.0 + rng.normal(0, 0.25)   # marginal: around DR4 sensitivity (~ -5.9 dBm)
                else:
                    fec += int(rng.integers(0, 2))
                    rxp = -1.8 + rng.normal(0, 0.3)
                rows.append((t.strftime("%Y-%m-%dT%H:%M:%SZ"), leaf, f"Ethernet{p + 1}/1", node_name(n),
                             f"mlx5_{rail}", "up", ld, fec, sym, round(float(rxp), 2), pfc))
    return pd.DataFrame(rows, columns=["ts", "switch", "port", "peer_node", "peer_hca", "oper_status",
                                       "link_down_count", "fec_uncorrectable_blocks", "symbol_errors",
                                       "rx_power_dbm_min_lane", "pfc_pause_rx_frames"])


def gen_events(rm: pd.DataFrame) -> list[dict]:
    ev: list[dict] = []

    def add(t: str, source: str, host: str, msg: str, **kw: object) -> None:
        e: dict = {"ts": ts(t), "source": source, "host": host, "message": msg}
        e.update(kw)
        ev.append(e)

    fl = node_name(FLAKY_NODE)
    nb_lo, nb_hi = node_name(FLAKY_NODE - 1), node_name(FLAKY_NODE + 1)
    ip = lambda n: backend_ip(n, FLAKY_RAIL)  # noqa: E731
    leaf, port = leaf_of(FLAKY_NODE, FLAKY_RAIL)
    # Attempt 1 (job 900198) hang on the first long flap
    add("23:10:05", "slurm", "slurmctld", "job 900198 started on 512 nodes orionxl-n[001-512] (attempt 1)", job="900198")
    ev[-1]["ts"] = "2026-10-19T23:10:05Z"  # previous day
    for a, b in FLAPS:
        add(a, "kernel", fl, f"mlx5_core {HCA_BDF[FLAKY_RAIL]} ens{FLAKY_RAIL}np0: Link down")
        add(a, "switch-syslog", leaf, f"{port} (peer {fl} mlx5_{FLAKY_RAIL}) oper-status changed to DOWN")
        add(b, "kernel", fl, f"mlx5_core {HCA_BDF[FLAKY_RAIL]} ens{FLAKY_RAIL}np0: Link up")
        add(b, "switch-syslog", leaf, f"{port} (peer {fl} mlx5_{FLAKY_RAIL}) oper-status changed to UP")
    for t, job in (("01:12:53", "900198"), ("03:41:11", "900211")):
        for host, local, peer in ((nb_lo, nb_lo, ip(FLAKY_NODE)), (nb_hi, nb_hi, ip(FLAKY_NODE)),
                                  (fl, fl, ip(FLAKY_NODE - 1))):
            r = int(rm[(rm.node == local) & (rm.local_rank == FLAKY_RAIL)]["rank"].iloc[0])
            add(t, "nccl", host, f"{host}:{3000 + r % 997}:{3100 + r % 991} [{FLAKY_RAIL}] NCCL WARN NET/IB : Got "
                f"completion from peer {peer}<{40000 + r % 1000}> with status=12 opcode=0 len=0 vendor err 129 "
                f"(Send) hca mlx5_{FLAKY_RAIL}", job=job, rank=r)
    add("01:23:00", "pytorch", node_name(17), "[Rank 137] Watchdog caught collective operation timeout: "
        "WorkNCCL(SeqNum=40112, OpType=ALLREDUCE, Timeout(ms)=600000) ran for 600010 milliseconds before timing out.",
        job="900198", rank=137)
    add("01:23:40", "slurm", "slurmctld", "job 900198 FAILED (NCCL watchdog timeout) - auto-requeue policy: "
        "restart same allocation from latest checkpoint ckpt-0081 (01:00)", job="900198")
    add("01:40:02", "slurm", "slurmctld", "job 900211 started on 512 nodes orionxl-n[001-512] (attempt 2, restart of 900198)",
        job="900211")
    add("01:52:10", "trainer", node_name(0), "job 900211 resumed from ckpt-0081 at step 151200; first step completed",
        job="900211")
    # background PCIe AER corrected errors on an unrelated node's NIC (recurring)
    for t in ("00:10:12", "00:52:40", "01:31:05", "02:14:55", "02:58:20", "03:40:31", "04:19:44"):
        add(t, "kernel", node_name(AER_NODE), f"pcieport 0000:{0x98:02x}:01.0: AER: Corrected error received: "
            f"{HCA_BDF[4]}; PCIe Bus Error: severity=Corrected, type=Physical Layer, (Receiver ID); "
            f"device [15b3:1021] error status/mask=00000001/00000000 [ 0] RxErr")
    # GPU ECC / row-remap event on orionxl-n389 GPU3
    add("02:58:41", "kernel", node_name(ECC_NODE),
        f"NVRM: Xid (PCI:{GPU_BDF[ECC_GPU][:10]}): 63, pid='<unknown>', name=<unknown>, Row remapping event: "
        f"correctable-error row marked for remapping; GPU reset required to activate")
    add("02:58:41", "dcgm", node_name(ECC_NODE), f"DCGM health: GPU {ECC_GPU} memory WARN: row remap pending "
        f"(uuid {uuid_for(node_name(ECC_NODE), ECC_GPU)})")
    # Spine PFC burst after the link drop (ECMP/rail reconvergence)
    add("03:41:20", "telemetry", "orionxl-be-spine-p06-03", "PFC pause RX on priority 3 rose 38x for 70 s on ports facing orionxl-be-leaf-p06-r5")
    # Watchdog timeouts: first reporter is unrelated rank 817
    add("03:51:01", "pytorch", node_name(FIRST_REPORTER), "[Rank 817] Watchdog caught collective operation timeout: "
        "WorkNCCL(SeqNum=88214, OpType=SEND, Timeout(ms)=600000) ran for 600003 milliseconds before timing out.",
        job="900211", rank=817)
    for r in (1693, 1685, 1701, 0, 2048, 4095):
        seq = 88213 if r in (1693, 1685, 1701) else 88214
        op = "ALLREDUCE" if r in (1693, 1685, 1701) else "SEND"
        add("03:51:05", "pytorch", rm.loc[r, "node"], f"[Rank {r}] Watchdog caught collective operation timeout: "
            f"WorkNCCL(SeqNum={seq}, OpType={op}, Timeout(ms)=600000) ran for 600008 milliseconds before timing out.",
            job="900211", rank=r)
    add("03:52:15", "slurm", "slurmctld", "job 900211 FAILED (NCCL watchdog timeout); auto-requeue HELD by "
        "retry policy pending incident review INC-3107", job="900211")
    # checkpoints
    for t, cid, ok in (("02:10:00", "ckpt-0082", True), ("02:40:00", "ckpt-0083", True), ("03:10:00", "ckpt-0084", True),
                       ("03:40:00", "ckpt-0085", False)):
        add(t, "trainer", node_name(0), f"{cid}: async save started")
        if ok:
            add(t[:3] + f"{int(t[3:5]) + 1:02d}:12", "trainer", node_name(0), f"{cid}: shards 4096/4096 written; "
                f"metadata committed; save complete")
        else:
            add("03:40:58", "trainer", node_name(0), f"{cid}: shards 4096/4096 written; metadata commit in progress")
    ev.sort(key=lambda e: (e["ts"], e["source"], e["host"]))
    return ev


CHECKPOINTS = """\
ckpt_id,job,step,start_ts,end_ts,status,shards_expected,shards_written,metadata_committed
ckpt-0081,900198,151200,2026-10-20T01:00:00Z,2026-10-20T01:01:12Z,complete,4096,4096,true
ckpt-0082,900211,151593,2026-10-20T02:10:00Z,2026-10-20T02:11:12Z,complete,4096,4096,true
ckpt-0083,900211,151696,2026-10-20T02:40:00Z,2026-10-20T02:41:12Z,complete,4096,4096,true
ckpt-0084,900211,151799,2026-10-20T03:10:00Z,2026-10-20T03:11:12Z,complete,4096,4096,true
ckpt-0085,900211,151902,2026-10-20T03:40:00Z,2026-10-20T03:40:58Z,complete,4096,4096,false
"""

RESTART_HISTORY = """\
job,attempt,start_ts,end_ts,end_reason,implicated_nodes,auto_restarted
900198,1,2026-10-19T23:10:05Z,2026-10-20T01:23:40Z,nccl_timeout,,true
900211,2,2026-10-20T01:40:02Z,2026-10-20T03:52:15Z,nccl_timeout,,false
"""

SPARES = """\
node,state,last_acceptance,notes
orionxl-s00,acceptance_failed,2026-10-19,GPU2 uncorrectable ECC during burn-in; RMA open
orionxl-s01,ready,2026-10-18,
orionxl-s02,in_repair,2026-10-15,PSU replacement
orionxl-s03,ready,2026-10-18,
orionxl-s04,ready,2026-10-17,
orionxl-s05,reserved,2026-10-17,held for inference failover
orionxl-s06,ready,2026-10-16,
orionxl-s07,ready,2026-10-16,
"""

HYPOTHESES = """\
# Hypotheses raised in #inc-3107 between 03:52 and 04:05. Each names one component.
hypotheses:
  - {id: H1, kind: link, node: orionxl-n212, hca: mlx5_5, text: "orionxl-n212 rail-5 HCA link is flapping and caused the hang"}
  - {id: H2, kind: gpu, node: orionxl-n389, gpu: 3, text: "orionxl-n389 GPU3 ECC fault (Xid 63) caused the hang"}
  - {id: H3, kind: first_reporter, node: orionxl-n103, rank: 817, text: "rank 817 timed out first, so orionxl-n103 is the culprit"}
  - {id: H4, kind: aer, node: orionxl-n451, hca: mlx5_4, text: "PCIe AER errors on orionxl-n451's NIC caused the hang"}
  - {id: H5, kind: fabric_pfc, switch: orionxl-be-spine-p06-03, text: "a PFC storm on orionxl-be-spine-p06-03 caused the hang"}
  - {id: H6, kind: switch, switch: orionxl-be-leaf-p06-r5, text: "orionxl-be-leaf-p06-r5 is failing"}
"""

FMEA = """\
id,component,failure_mode,effect,severity,occurrence,detection,detection_control
F01,GPU,Uncorrectable ECC / row-remap failure,Rank crash; job restarts from checkpoint,7,6,3,DCGM health + Xid alert
F02,GPU,Fell off bus (Xid 79),Node unusable; job restarts,7,4,2,Xid alert + node health check
F03,HCA/link,Intermittent link flap (optic/HCA),NCCL hang until watchdog; whole job stalls 10 min then restarts,8,7,6,link-down log only; no flap-rate alert
F04,Node,PSU failure with power capping,Straggler slows whole job,6,4,5,BMC SEL; no power-limit alert
F05,Rack,PDU breaker trip,4 nodes lost; job restarts; possible second trip on restart inrush,8,3,4,PDU telemetry alert
F06,Leaf switch,Switch reboot / ASIC fault,32 nodes lose one rail; all jobs on that rail stall,9,3,3,gNMI oper-status ON_CHANGE alert
F07,CDU,Pump failure in coolant distribution unit,Rack-row thermal shutdown within minutes,10,2,2,none
F08,Storage,Metadata server failover,Checkpoint save/restore stalls; RPO grows,7,4,5,checkpoint duration SLO alert
F09,Scheduler,slurmctld failover,No new job starts for minutes; running jobs unaffected,4,3,3,HA heartbeat alert
F10,Control plane,etcd quorum loss (Kubernetes),Inference rollouts and scaling blocked; running pods continue,8,2,4,etcd health alert
F11,Optics,Transceiver aging (RX power drift),Rising FEC errors then flaps,6,0,5,DOM threshold ticket
F12,Firmware,NIC firmware / driver mismatch after upgrade,Degraded RDMA throughput or failures fleet-wide,9,3,7,compat matrix check at provisioning only
"""

TENANTS = """\
# Tenant isolation configuration for ORION-XL (shared training + inference platform)
# network.vrf / network.vni: Ethernet isolation (frontend and RoCE backend; VXLAN/EVPN VNI per tenant).
# network.ib_pkey: InfiniBand partition key, used only for tenants placed on the IB-fabric variant;
#   the subnet manager assigns it and IB switches enforce it on ingress when partition enforcement is on.
tenants:
  - name: acme-research
    idp_group: grp-acme
    k8s_namespaces: [acme-train, acme-dev]
    slurm_account: acme
    rbac_bindings:
      - {subject: "group:grp-acme", role: tenant-admin, scope: "namespace:acme-train"}
      - {subject: "sa:acme-train:trainer", role: cluster-admin, scope: cluster}
    network: {vrf: VRF-ACME, vni: 10010, ib_pkey: "0x8001", frontend_vlan: 210}
    storage:
      exports: [{path: /lustre/projects/acme, mode: rw}]
      encryption_key_id: kms/acme-01
    gpu: {allocation_mode: whole, shared_with: [], scrub_on_release: true}
    secrets: {backend: vault, path_prefix: kv/tenants/acme-research/}
    audit: {sink: siem-central, retention_days: 400}
  - name: borealis
    idp_group: grp-borealis
    k8s_namespaces: [borealis]
    slurm_account: borealis
    rbac_bindings:
      - {subject: "group:grp-borealis", role: tenant-admin, scope: "namespace:borealis"}
    network: {vrf: VRF-BOREALIS, vni: 10020, ib_pkey: "0x8002", frontend_vlan: 220}
    storage:
      exports: [{path: /lustre/projects, mode: ro}]
      encryption_key_id: kms/borealis-01
    gpu: {allocation_mode: whole, shared_with: [], scrub_on_release: false}
    secrets: {backend: vault, path_prefix: kv/tenants/}
    audit: {sink: siem-central, retention_days: 400}
  - name: cobalt-inference
    idp_group: grp-cobalt
    k8s_namespaces: [cobalt-serve]
    slurm_account: cobalt
    rbac_bindings:
      - {subject: "group:grp-cobalt", role: tenant-admin, scope: "namespace:cobalt-serve"}
    network: {vrf: VRF-COBALT, vni: 10020, ib_pkey: "0x8001", frontend_vlan: 230}
    storage:
      exports: [{path: /lustre/projects/cobalt, mode: rw}]
      encryption_key_id: kms/cobalt-01
    gpu: {allocation_mode: timeslice, shared_with: [borealis], scrub_on_release: true}
    secrets: {backend: vault, path_prefix: kv/tenants/cobalt-inference/}
    audit: {sink: siem-central, retention_days: 30}
"""

POLICY = """\
# ORION-XL tenant isolation policy (what check_isolation() enforces)
min_audit_retention_days: 365
forbidden_roles_for_tenant_subjects: [cluster-admin]
unique_per_tenant: [vrf, vni, ib_pkey, frontend_vlan]
gpu_cross_tenant_sharing_requires: mig
scrub_on_release_required: true
secrets_prefix_must_end_with_tenant_name: true
storage_exports_must_not_overlap_other_tenants: true
"""


def write_all(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    rm = gen_rank_map()
    rm.to_csv(out / "rank_map.csv", index=False, lineterminator="\n")
    gen_rank_progress(rng).to_csv(out / "rank_progress.csv", index=False, lineterminator="\n")
    gen_gpu_health(rng).to_csv(out / "gpu_health.csv", index=False, lineterminator="\n")
    gen_host_nic(rng).to_csv(out / "host_nic_snapshot.csv", index=False, lineterminator="\n")
    gen_switch_counters(rng).to_csv(out / "switch_port_counters.csv", index=False, lineterminator="\n")
    with open(out / "events.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for e in gen_events(rm):
            fh.write(json.dumps(e, sort_keys=True) + "\n")
    for name, text in (("checkpoints.csv", CHECKPOINTS), ("restart_history.csv", RESTART_HISTORY),
                       ("spares.csv", SPARES), ("hypotheses.yaml", HYPOTHESES), ("fmea.csv", FMEA),
                       ("tenants.yaml", TENANTS), ("isolation_policy.yaml", POLICY)):
        (out / name).write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    write_all(p.parse_args().out)
    print("ok")


if __name__ == "__main__":
    main()
