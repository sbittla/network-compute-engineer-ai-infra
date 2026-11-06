# 10.W1 — Cross-hall DR4 link budget `[MODELED]`

## (a)
- fiber = 0.42 km x 0.4 dB/km = 0.168 dB
- connectors = 4 x 0.5 dB = 2.0 dB; splices = 2 x 0.1 dB = 0.2 dB
- channel = 2.368 dB (limit 3.0 dB)
- Rx worst = -2.9 dBm - 2.368 dB = -5.268 dBm
- margin = -5.268 - (-5.9) = 0.632 dB

## (b) one dirty MPO pair (+1.0 dB)
- channel = 3.368 dB, 0.368 dB over budget
- Rx worst = -6.268 dBm, 0.368 dB below the receiver minimum
- with typical Tx 0.5 dBm the link would still show -2.868 dBm
- decision: Reject: clean or re-terminate and re-measure before acceptance

## (c)
- 10^(-5.268/10) = 0.2973 mW

## (d)
- measured loss = 0.6 - (-4.1) = 4.7 dB
- excess = 4.7 - 2.368 = 2.332 dB
- decision: Equal excess on all lanes -> shared element (MPO end-face at a mated pair, splice or trunk bend); drain, inspect jumpers and panel interfaces first
