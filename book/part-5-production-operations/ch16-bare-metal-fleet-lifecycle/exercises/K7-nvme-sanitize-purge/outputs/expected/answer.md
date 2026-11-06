# K7 — NVMe crypto erase in NIST SP 800-88 terms

**Category: Purge.** NIST SP 800-88 defines Clear (logical techniques against simple recovery,
e.g. overwriting user-addressable storage), Purge (techniques that make recovery infeasible even
with laboratory methods), and Destroy. An NVMe Sanitize cryptographic erase (`nvme sanitize
--sanact=4`, where supported) or block erase is a Purge method.

**Why it beats overwriting the file system before retirement.**
- An SSD remaps logical blocks to physical NAND pages. Over-provisioned space, retired/remapped
  bad blocks, and stale copies left by wear levelling are not addressable through the file
  system, so a file-level overwrite never reaches them.
- Data outside the file system (other partitions, swap, metadata areas, unallocated space) is
  also missed.
- Crypto erase destroys the media encryption key, so every block on the device, addressable or
  not, becomes unreadable at once; block erase resets all NAND blocks. Both act on the whole
  device, and the sanitize operation continues across power cycles until it completes.

**What gets recorded (the sanitization certificate, Section 16.10):** serial number of every
sanitized device, method (crypto erase / block erase / destroy), tool and version, operator,
date, and the verification result (`nvme sanitize-log` showing completion). The lab's `retire`
guard refuses the transition without a certificate ID (`SANITIZATION_MISSING`). Drives that cannot
be purged or fail verification are physically destroyed.

**Safety and common mistakes.** Identify drives by serial, not by device name, and only on nodes
that are `drained`/`repair` and approved for retirement. Do not call a file-system wipe "Purge",
and do not forget the BMC (credentials) and TPM in the decommissioning checklist.

Source: Section 16.10.
