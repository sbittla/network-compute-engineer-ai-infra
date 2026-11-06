# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `dataset reproducible` | PASS dataset reproducible: generator reproduces committed data byte-for-byte (sha256 3087f4fb0560) |
| `T1 plan hygiene` | PASS T1 plan hygiene: 12 quarters after removing the exact duplicate; conflicting duplicate raises=True |
| `T2 usable fraction + kW per GPU` | PASS T2 usable fraction + kW per GPU: usable fraction=0.8496 (expect 0.8496); IT kW/GPU=1.428 (expect 1.428) |
| `T2 quarterly forecast` | PASS T2 quarterly forecast: 2028Q2 energized/stranded=560/464; 2028Q3 usable 475.8 vs required 494.1 -> SHORTFALL |
| `T2 first shortfall + order deadlines` | PASS T2 first shortfall + order deadlines: first shortfall=2028Q3; order-by={'gpus': '2028Q1', 'network': '2028Q2', 'facility_power': '2027Q3'} |
| `T3 TCO and cost per GPU-hour` | PASS T3 TCO and cost per GPU-hour: ORION-256 TCO $6.73M/yr; $/GPU-h nominal 3.00, allocated 4.16, useful 4.72 (expect 3.00/4.16/4.72) |
| `T4 design comparison` | PASS T4 design comparison: A 87 nodes, 26.69/$M, 395.6/MW; B 62 nodes, 31.49/$M, 645.0/MW |
| `T5 power-capping trade-off` | PASS T5 power-capping trade-off: 700 W: 2/rack, throughput 32.0; 650 W: 3/rack, throughput 47.52; best cap 650 W |
| `T6 misleading-nominal flags` | PASS T6 misleading-nominal flags: {'STRANDED_GPUS': ['2028Q2', '2028Q3', '2029Q2'], 'RESERVE_SHORTFALL': ['2028Q3', '2029Q4'], 'PER_GPU_COST_MISLEADS': ['B-liquid-nextgen']} |
