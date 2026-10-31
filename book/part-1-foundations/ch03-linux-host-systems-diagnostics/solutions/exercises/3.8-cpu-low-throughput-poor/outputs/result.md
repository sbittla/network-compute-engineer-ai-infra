# 3.8 — orion-n12 `[MODELED]` from `[SIMULATED]` data

- nvme3n1 r_await 48.6 ms vs siblings 0.21 ms (231×)
- md0 delivers 435.2 MB/s; at a 40 % shortfall the loader needs ≈ 725 MB/s
- Little's law nvme3n1: 830/s × 0.048600000000000004 s = 40.34 (aqu-sz 40.34)
- vmstat b live [14, 14, 16, 17], mean 15.25; 6.81 % of 224 CPUs vs %iowait 6.9
- PID memory remote to its CPUs: 98.9 % (affinity 0-55,112-167)
- GPU utilization 55-60 %
