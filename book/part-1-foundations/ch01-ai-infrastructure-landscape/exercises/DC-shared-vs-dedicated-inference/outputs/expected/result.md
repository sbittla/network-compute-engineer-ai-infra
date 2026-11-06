# DC — cost arithmetic `[MODELED]`

- pool: 64 GPUs × $3.0 × 8760 h = $1,681,920/year
- reclaimable by sharing at 60 % inference load: <= $672,768/year
- dedicated pool avoids 64 backend NICs, 64 rail-leaf ports, 128 optics
- pool decode capacity: 26,960 tokens/s
