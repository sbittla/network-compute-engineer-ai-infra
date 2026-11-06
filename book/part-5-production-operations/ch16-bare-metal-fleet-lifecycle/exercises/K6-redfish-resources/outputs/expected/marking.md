# Marking scheme: K6 Redfish resources and the staged-versus-running trap

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** Three resource paths or actions from Section 16.3; the staged-vs-running explanation.

| Criterion | Points |
|---|---|
| (a) PATCH Systems/{id} Boot.BootSourceOverrideTarget = Pxe, Enabled = Once | 1 |
| (b) POST Systems/{id}/Actions/ComputerSystem.Reset with a ResetType | 1 |
| (c) GET /redfish/v1/UpdateService/FirmwareInventory | 1 |
| Explains staged images activate only after reboot/AC cycle, so the running version must be read back | 2 |
