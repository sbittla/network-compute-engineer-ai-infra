# D1 - the inference pool `[MODELED]`

- Pool: 10 peak replicas + N+2 = 12 replicas = 96 GPUs -> 840,960 GPU-h/yr
- Average busy: 0.4 × 10 = 4 replicas -> 280,320 GPU-h (33.3 % of the pool)
- Idle: 560,640 GPU-h, of which 420,480 beyond the N+2 headroom
- Lent: 0.6 × idle = 336,384 GPU-h; useful at goodput 0.7 = **235,469 GPU-h** = **$1.12M/yr** at $4.75

| Option | Useful GPU-h/yr | Allocated fraction |
|---|---|---|
| 1 Dedicated | 280,320 | 33.3 % |
| 2 Shared | 515,789 | 73.3 % |
