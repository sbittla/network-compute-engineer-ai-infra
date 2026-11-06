# K6 — Redfish resources and the staged-versus-running trap

| Task | Redfish resource / action (Section 16.3) |
|---|---|
| (a) One-time PXE boot | `PATCH /redfish/v1/Systems/{id}` with `{"Boot": {"BootSourceOverrideTarget": "Pxe", "BootSourceOverrideEnabled": "Once"}}` (UEFI systems may also set `BootSourceOverrideMode: UEFI`) |
| (b) Reset the system | `POST /redfish/v1/Systems/{id}/Actions/ComputerSystem.Reset` with a `ResetType` such as `ForceRestart`, `GracefulRestart`, or `On` (allowed values are listed in the action's `ResetType@Redfish.AllowableValues`) |
| (c) List installed firmware | `GET /redfish/v1/UpdateService/FirmwareInventory` (one member per component, each with a `Version`) |

**Why automation must read back the running version.** Many firmware images (BIOS, BMC, CPLD, NIC,
GPU VBIOS) are *staged*: the update service writes the image to a second bank or a staging area,
and it activates only after a reboot, a BMC reset, or a full AC power cycle. The update task can
report `Completed` while the old image is still the one running. If automation records the
staged version as "installed", the inventory and the compatibility check are wrong, and a node can
be enabled on a bundle it is not actually running. The safe sequence is: stage → activate
(reset or AC cycle as the component requires) → `GET FirmwareInventory` and compare every
component with the target bundle → only then run re-acceptance. The before/after inventory is
also the audit evidence of the upgrade campaign (exercise M2).

**Common wrong answers.** Using IPMI `chassis bootdev pxe` for (a) (valid IPMI, but the question
asks for Redfish); trusting the task status instead of the inventory read-back.

Source: Section 16.3 (Listing for one-time UEFI PXE boot, reset, and firmware inventory); Section
16.8 (audit evidence).
