# 8.6 — Reading `ibstat` (worked solution)

Relies on manuscript Section 8.5 ("The subnet manager", "Reading an InfiniBand port") and Section
8.10 (tools and the evidence they give).

## Port 1: `State: Initializing`, `Physical state: LinkUp`, `Base lid: 0`

- **Reading:** the physical layer is fine. The link trained with its partner (LinkUp). But the logical
  port has never been brought to Active: it has no LID (0), so no subnet manager has configured it.
  An IB port moves Initializing → Armed → Active only when the **subnet manager (SM)** assigns a LID and
  programs the port.
- **Most likely failing component:** the **subnet manager**. It may not be running, there may be no
  master SM on this subnet, the SM may not have swept since the port came up, or a partition/SM
  configuration problem may be excluding the port.
- **First command:** `sminfo`. Is there a master SM, and at which LID, GUID, priority and state? Then
  read the SM's log on the SM host (for example `/var/log/opensm.log`), or compare `SM lid` in `ibstat`
  on a working port of the same fabric.

## Port 2: `State: Down`, `Physical state: Polling`

- **Reading:** the port is transmitting training sequences and hears nothing back. There is **no link
  partner**.
- **Most likely failing component:** the **cable or transceiver** (unseated, damaged, wrong type), or
  the **remote switch port** (disabled, failed, or a different speed/width).
- **First command:** look from the fabric side. `iblinkinfo` (or `ibnetdiscover`) from a node with a
  working port shows whether the switch port facing this HCA is down, disabled or polling. Then inspect
  the physical layer: reseat or swap the cable or optic and check its DOM (Chapter 10). The
  vendor-specific `mlxlink -d <dev>` gives detailed link-training and cable information, labelled
  `[VENDOR-SPEC, 2026-10]`.

## Common mistakes

Blaming the SM for the Polling port: the SM cannot help when there is no physical link. Blaming the
cable for the Initializing port: LinkUp proves the cable works. Inventing commands or flags (for
example `ibstat --fix`), which costs 25 % under the marking conventions.
