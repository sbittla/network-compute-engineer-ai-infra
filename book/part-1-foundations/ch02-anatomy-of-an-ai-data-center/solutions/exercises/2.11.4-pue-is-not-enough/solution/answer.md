# 2.11.4 — "PUE is 1.25, so efficiency is fine"

PUE is facility power divided by IT power, so it only measures the overhead of delivering watts to the IT
equipment. For an AI cluster that misses most of what matters. First, it says nothing about **IT
efficiency**: how much useful training progress each IT watt buys. A cluster at 1.25 PUE that runs
W-TRAIN at 40 % MFU with 92 % goodput and 80 % allocation turns only ≈ 29 % of its peak into durable
progress (Section 2.9); fixing allocation, MFU or a feed-loss cap is often worth more than a PUE point.
It also ignores power drawn by idle but powered GPUs. Second, it says nothing about **transients**: the
synchronized step-boundary swings that breakers, UPSs and generators must ride through. Third, it says
nothing about **stranded capacity**: power and cooling reserved by 2N redundancy and margins that can
never be used. ORION's 65.55 kW per side carries a 45.1 kW design load, so a third of the provisioned
capacity is stranded by design. A complete efficiency statement adds work per IT kWh, utilization and
goodput, and the stranded fraction.
