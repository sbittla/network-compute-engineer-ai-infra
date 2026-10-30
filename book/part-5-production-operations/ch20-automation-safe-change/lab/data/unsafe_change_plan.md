# CHG-2026-1107 - Enable 4096 RDMA MTU, new RoCE QoS profile, and NIC firmware on ORION

Owner: J. Rivera (Fabric team)
Ticket: CHG-2026-1107, approved by the Change Advisory Board on 2026-11-03
Window: Friday 2026-11-06, 16:30-17:00 local time
Communication: Training Infra, Platform, and SRE on-call notified 48 h ahead in #orion-ops; status-page notice posted

## Summary

Raise the RDMA path MTU from 1024 to 4096 on all 32 HX8 nodes and push the new RoCE QoS profile
(DSCP 26 -> TC 3 lossless with PFC, CNP DSCP 48 -> TC 6 strict priority) to all 8 rail leaves.
Also upgrade NIC firmware to 28.43.1014 at the same time, since the nodes are being touched anyway.

## Procedure

1. SSH to each rail leaf and paste the new QoS profile from the wiki page (it takes effect immediately).
2. From the jump host, run:
   for n in $(cat all_nodes.txt); do ssh $n 'sudo ./set_mtu.sh 4096 && sudo ./fw_update.sh 28.43.1014 && sudo reboot' & done
3. Wait for the nodes to come back.
4. Start a training job and check that the dashboards look good.

## Rollback

If something goes wrong, revert the switch config by hand and re-image the affected nodes.

## Risk

Low. The same change was tried on a lab node last month.
