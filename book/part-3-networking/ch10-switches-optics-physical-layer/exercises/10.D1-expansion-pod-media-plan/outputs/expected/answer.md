# 10.D1 — Media plan for ORION's expansion pod (model answer)

Accept any well-defended alternative. Reach, power and cost are `[ILLUSTRATIVE]` (Tables 10.2, 10.3
and 10.9); verify every number with the vendors.

**Decision table**

| Link class | Choice | Reason (reach · power · failure modes · sparing · cleaning) |
|---|---|---|
| (i) Host links, 25–40 m | 400G-DR4 + SMF MPO-12 jumpers via structured cabling (alternative: AOC) | Beyond passive DAC (≈ 2–3 m) and AEC (≈ 5–7 m) reach. DR4 matches ORION's existing single optic type, so one spare pool. Failure modes: contaminated MPO end-faces → cleaning burden. AOC avoids cleaning but needs a spare per length and is replaced as a whole assembly. |
| (ii) New leaf ↔ new spine, ≈ 3 m | AEC (passive DAC only if ≤ 2–3 m with routing slack) | Lowest power and highest reliability (no lasers, no end-faces). Must verify AEC/DAC support on both platforms and the NOS release. |
| (iii) New spine ↔ old hall, 350 m | 400G-DR4 over SMF trunk (FR4 if trunk fiber is scarce) | 350 m is inside DR4's 500 m reach, but patch panels and splices eat the 3.0 dB budget: budget it with the 10.W1 method (e.g. 0.14 dB fiber + 4 × 0.5 dB + splices ≈ 2.3 dB → only ≈ 0.6 dB margin; insist on low-loss MPO, ≤ 0.35 dB per pair). FR4 uses 2 fibers instead of 8 and duplex LC is easier to clean. |
| Switch modules | Single-port modules (ORION standard) | Twin-port halves the module count and slightly reduces power per port, but doubles the blast radius of one module failure (two links drained) and adds a new spare type. Use twin-port only if port density forces it. |

**Optics-power estimate** (`[ILLUSTRATIVE]` per-module power: DR4 ≈ 12 W, AEC ≈ 3 W per end):

```text
host links   : 16 nodes × 8 links × 2 ends        = 256 DR4 modules × 12 W ≈ 3.07 kW
leaf↔spine   : 8 leaves × 16 uplinks = 128 links  = 256 AEC ends × 3 W     ≈ 0.77 kW
cross-hall   : e.g. 64 links × 2 ends             = 128 DR4 modules × 12 W ≈ 1.54 kW
total optics/active-cable power ≈ 5.4 kW  (vs ≈ 3.1 kW more if leaf↔spine also used DR4)
```

(Assumes rail leaves at 1:1 with 16 downlinks each; the cross-hall count depends on the super-spine
design and is stated as an assumption.)

**Spare-part list.** DR4 modules (3 % of installed, ≥ 2; e.g. ⌈384 × 0.03⌉ = 12); MPO-12 jumpers in each
used length (2 %, ≥ 2 per length); AEC assemblies in each used length (≥ 2 per length); one pre-imaged
spare switch per model; cleaning kit (one-click MPO and LC cleaners), inspection probe tips, labels.

**Verify with vendors.** Supported cable/optic list per platform and NOS release; AEC power and FEC
mode compatibility (host and switch both RS(544,514)); DR4 insertion-loss spec for the cross-hall
trunk; MPO connector loss grade; twin-port module availability and lead times; DOM support for AECs.
