"""Exercise 20-M1 — reference idempotent backend-network validator, exercised on an L1 fixture.

    python solve.py --out DIR

The validator reads the same machine-readable outputs it would read on a host (`ip -j link show`,
`ethtool -i`, `ibv_devinfo`, `/sys/class/net/<netdev>/speed`), but from a captured fixture defined
below (one ORION HX8 node, 8 backend NICs; orion-n06's reimage drift of Section 20.11: one NIC at
IP MTU 1,500 with RDMA active_mtu dragged to 1,024). It then runs the sequence the prompt asks for
and asserts the key's contract (solutions/exercises-key.md, Section 20.5):

  run 1  validate             -> drift found, exit 1, no mutation
  run 2  --apply (dry run)    -> 1 planned action, recorded as dry-run, fixture unchanged, exit 1
  run 3  --apply --no-dry-run -> 1 action changed (IP MTU only), read-back in sync, exit 0
  run 4  --apply --no-dry-run -> 0 actions (provable no-op), exit 0
  run 5  ibv_devinfo missing  -> exit 2 (cannot determine), never "in sync"

Evidence label: [SIMULATED] (fixture, not a host).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

TARGET = "orion-n06"
DESIRED = {"host_mtu": 9_000, "rdma_active_mtu": 4_096, "speed_mbps": 400_000}
APPROVED_FW = ("28.42.1000", "28.43.1014")      # lab policy.approved_nic_firmware (Chapter 16 matrix)
IB_MTUS = (256, 512, 1_024, 2_048, 4_096)
ROCE_HEADERS = 64                               # Section 20.5.1 header budget (IPv4)
PORT_MAX_RDMA_MTU = 4_096


def _fixture() -> dict:
    """Captured outputs for 8 backend NICs (mlx5_0..7 / eth0..7); frontend NICs are not listed."""
    nics = {}
    for i in range(8):
        mtu = 1_500 if i == 3 else 9_000
        nics[f"eth{i}"] = {
            "ibdev": f"mlx5_{i}",
            "ip_j_link": json.dumps([{"ifname": f"eth{i}", "mtu": mtu, "operstate": "UP"}]),
            "ethtool_i": f"driver: mlx5_core\nversion: 24.10\nfirmware-version: 28.43.1014 (MT_0000000838)\nbus-info: 0000:{0x1a + i:02x}:00.0\n",
            "sys_speed": "400000\n",
        }
    return {"target": TARGET, "nics": nics, "tools": ["ip", "ethtool", "ibv_devinfo"]}


def _active_mtu(netdev_mtu: int) -> int:
    """RoCE active_mtu = min(port max, largest IB MTU fitting under the netdev MTU after headers)."""
    fitting = [m for m in IB_MTUS if m + ROCE_HEADERS <= netdev_mtu]
    return min(PORT_MAX_RDMA_MTU, max(fitting)) if fitting else 0


class FixtureHost:
    """Adapter with the same interface a LinuxHost adapter would have (run a read command; set MTU)."""

    def __init__(self, fx: dict) -> None:
        self.fx = fx
        self.writes = 0

    def run(self, cmd: list[str]) -> str:
        if cmd[0] not in self.fx["tools"]:
            raise FileNotFoundError(cmd[0])
        if cmd[:3] == ["ip", "-j", "link"]:
            return self.fx["nics"][cmd[-1]]["ip_j_link"]
        if cmd[:2] == ["ethtool", "-i"]:
            return self.fx["nics"][cmd[2]]["ethtool_i"]
        if cmd[0] == "ibv_devinfo":
            nic = next(n for n in self.fx["nics"].values() if n["ibdev"] == cmd[2])
            mtu = json.loads(nic["ip_j_link"])[0]["mtu"]
            return f"hca_id: {cmd[2]}\n\tport:\t1\n\t\tstate:\t\tPORT_ACTIVE (4)\n\t\tmax_mtu:\t\t4096 (5)\n\t\tactive_mtu:\t\t{_active_mtu(mtu)} (x)\n"
        raise ValueError(cmd)

    def read_sys(self, path: str) -> str:
        return self.fx["nics"][path.split("/")[4]]["sys_speed"]

    def set_mtu(self, netdev: str, mtu: int) -> None:   # the only mutating call
        link = json.loads(self.fx["nics"][netdev]["ip_j_link"])
        link[0]["mtu"] = mtu
        self.fx["nics"][netdev]["ip_j_link"] = json.dumps(link)
        self.writes += 1


def observe(host: FixtureHost, netdev: str, ibdev: str) -> dict:
    link = json.loads(host.run(["ip", "-j", "link", "show", "dev", netdev]))[0]
    fw = re.search(r"^firmware-version:\s*(\S+)", host.run(["ethtool", "-i", netdev]), re.M).group(1)
    active = int(re.search(r"active_mtu:\s+(\d+)", host.run(["ibv_devinfo", "-d", ibdev])).group(1))
    speed = int(host.read_sys(f"/sys/class/net/{netdev}/speed"))
    return {"host_mtu": link["mtu"], "rdma_active_mtu": active, "nic_firmware": fw, "speed_mbps": speed}


def validate(host: FixtureHost, apply: bool = False, dry_run: bool = True) -> tuple[int, list[dict]]:
    audit: list[dict] = []
    drift_found = False
    try:
        for netdev, nic in sorted(host.fx["nics"].items()):
            obs = observe(host, netdev, nic["ibdev"])
            checks = dict(DESIRED)
            for key, want in checks.items():
                ok = obs[key] == want
                drift_found |= not ok
                audit.append({"target": host.fx["target"], "netdev": netdev, "key": key, "before": obs[key],
                              "after": want, "result": "in_sync" if ok else "drift"})
            fw_ok = obs["nic_firmware"] in APPROVED_FW
            drift_found |= not fw_ok
            audit.append({"target": host.fx["target"], "netdev": netdev, "key": "nic_firmware",
                          "before": obs["nic_firmware"], "after": list(APPROVED_FW),
                          "result": "in_sync" if fw_ok else "drift"})
            if apply and obs["host_mtu"] != DESIRED["host_mtu"]:      # remediate IP MTU only
                rec = {"target": host.fx["target"], "netdev": netdev, "key": "host_mtu", "action": "set_mtu",
                       "before": obs["host_mtu"], "after": DESIRED["host_mtu"]}
                if dry_run:
                    audit.append({**rec, "result": "dry-run"})
                else:
                    host.set_mtu(netdev, DESIRED["host_mtu"])
                    back = observe(host, netdev, nic["ibdev"])          # read-back verification
                    audit.append({**rec, "result": "changed" if back["host_mtu"] == DESIRED["host_mtu"] else "failed",
                                  "readback_rdma_active_mtu": back["rdma_active_mtu"]})
        if apply and not dry_run:   # re-validate after changes so the exit code reflects final state
            final = [observe(host, n, v["ibdev"]) for n, v in sorted(host.fx["nics"].items())]
            drift_found = any(o[k] != w for o in final for k, w in DESIRED.items()) or \
                any(o["nic_firmware"] not in APPROVED_FW for o in final)
    except (FileNotFoundError, KeyError, AttributeError) as exc:
        audit.append({"target": host.fx["target"], "key": "*", "result": "cannot_determine",
                      "error": f"{type(exc).__name__}: {exc}"})
        return 2, audit
    return (1 if drift_found else 0), audit


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    fx = _fixture()
    pristine = copy.deepcopy(fx)
    host = FixtureHost(fx)
    runs = {}
    runs["run1_validate"] = validate(host)
    assert host.fx == pristine and host.writes == 0, "validation must not mutate"
    runs["run2_apply_dry_run"] = validate(host, apply=True)
    assert host.fx == pristine and host.writes == 0, "apply defaults to dry run"
    runs["run3_apply"] = validate(host, apply=True, dry_run=False)
    runs["run4_apply_again"] = validate(host, apply=True, dry_run=False)
    broken = copy.deepcopy(pristine)
    broken["tools"] = ["ip", "ethtool"]
    runs["run5_missing_tool"] = validate(FixtureHost(broken))

    def actions(audit, result):
        return sum(1 for a in audit if a.get("action") and a["result"] == result)

    summary = {name: {"exit_code": rc, "drift_lines": sum(1 for a in au if a["result"] == "drift"),
                      "dry_run_actions": actions(au, "dry-run"), "changed_actions": actions(au, "changed"),
                      "audit_lines": len(au)} for name, (rc, au) in runs.items()}

    # --- assertions encoding the key's contract (20-M1) -------------------------------------------
    assert summary["run1_validate"]["exit_code"] == 1
    assert summary["run1_validate"]["drift_lines"] == 2          # eth3 host_mtu 1,500 and its active_mtu 1,024
    assert summary["run2_apply_dry_run"]["dry_run_actions"] == 1 and summary["run2_apply_dry_run"]["exit_code"] == 1
    assert summary["run3_apply"]["changed_actions"] == 1 and summary["run3_apply"]["exit_code"] == 0
    assert host.writes == 1, "only the one IP MTU write is ever made"
    readback = next(a for a in runs["run3_apply"][1] if a.get("action"))["readback_rdma_active_mtu"]
    assert readback == 4_096, "active_mtu follows the netdev MTU on RoCE (read-back)"
    assert summary["run4_apply_again"]["changed_actions"] == 0 and summary["run4_apply_again"]["dry_run_actions"] == 0
    assert summary["run4_apply_again"]["exit_code"] == 0
    assert summary["run5_missing_tool"]["exit_code"] == 2

    for name, (_, audit) in runs.items():
        (out / f"{name}.jsonl").write_text("".join(json.dumps(a, sort_keys=True) + "\n" for a in audit),
                                           encoding="utf-8")
    result = {"exercise": "20-M1", "evidence_label": "[SIMULATED]", "units": "exit codes, action counts",
              "inputs": {"target": TARGET, "desired": DESIRED, "approved_firmware": list(APPROVED_FW),
                         "fixture_drift": "eth3 IP MTU 1500 (active_mtu 1024)"},
              "steps": summary, "answer": {"sequence_exit_codes": [s["exit_code"] for s in summary.values()],
                                           "second_apply_actions": 0, "writes_total": host.writes,
                                           "readback_rdma_active_mtu": readback},
              "tolerance": "exact"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 20-M1 — validator runs on the L1 fixture `[SIMULATED]`", "",
          "| Run | Exit | Drift lines | Dry-run actions | Changed actions | Audit lines |", "|---|---|---|---|---|---|"]
    md += [f"| {n} | {s['exit_code']} | {s['drift_lines']} | {s['dry_run_actions']} | {s['changed_actions']} | {s['audit_lines']} |"
           for n, s in summary.items()]
    md += ["", f"Read-back after the fix: eth3 active_mtu = {readback}. Total writes: {host.writes}.", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
