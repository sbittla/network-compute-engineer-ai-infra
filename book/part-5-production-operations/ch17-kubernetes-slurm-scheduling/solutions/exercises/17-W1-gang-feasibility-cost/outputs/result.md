# 17-W1 result `[MODELED]`

1. naive 60 GPUs; eligible 52 (draining p07 excluded)
2. whole eligible nodes ['p01', 'p02', 'p10'] → largest gang 24 GPUs
3. 4-node gang: Fragmentation
4. best fit for 6 GPUs: p05 (leftovers [('p05', 0), ('p12', 1), ('p01', 2), ('p02', 2), ('p10', 2)])
5. 32 GPUs stranded × 5 h = 160 GPU-hours = $480
6. 128 × (45/2 + 15) min = 80 GPU-hours per preemption
