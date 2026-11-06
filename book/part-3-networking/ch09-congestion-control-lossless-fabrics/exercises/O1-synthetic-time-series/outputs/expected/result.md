# O1 — result `[SIMULATED]`

Episodes found: 100–158 s, 250–318 s, 400–468 s (520–558 s is busy but not an episode).

## incast

- root leaf-r3 eth1/5: tx_gbps 393.62, rx_gbps 147.41, q_tc3_max_kb 1,426.10, ecn_marked_tc3_rate 0.00, pfc_tx_p3_rate 0.00, pfc_rx_p3_rate 0.00
- sender port leaf-r3 eth1/1: tx_gbps 160.43, rx_gbps 33.38, q_tc3_max_kb 11.05, ecn_marked_tc3_rate 0.00, pfc_tx_p3_rate 19,145.25, pfc_rx_p3_rate 0.00
- leaf-r3 uplink eth1/33: tx_gbps 96.94, rx_gbps 81.52, q_tc3_max_kb 10.90, ecn_marked_tc3_rate 0.00, pfc_tx_p3_rate 0.00, pfc_rx_p3_rate 0.00
- orion-n05 mlx5_3 (NP): tx_gbps 147.41, rx_gbps 393.62, pfc_tx_p3_rate 0.00, pfc_rx_p3_rate 0.00, cnp_sent_rate 10.75

## pause_propagation

- root leaf-r3 eth1/10: tx_gbps 394.08, rx_gbps 159.41, q_tc3_max_kb 1,373.60, ecn_marked_tc3_rate 0.00, pfc_tx_p3_rate 0.00, pfc_rx_p3_rate 0.00
- leaf-r3 uplink eth1/33 (to spine-1): tx_gbps 95.02, rx_gbps 198.18, q_tc3_max_kb 9.50, ecn_marked_tc3_rate 0.00, pfc_tx_p3_rate 7,965.50, pfc_rx_p3_rate 0.00
- spine-1 eth1/25 (to leaf-r3): tx_gbps 198.18, rx_gbps 95.02, q_tc3_max_kb 2,491.10, ecn_marked_tc3_rate 5,948,586.00, pfc_tx_p3_rate 0.00, pfc_rx_p3_rate 7,965.50
- spine-2 eth1/25 (to leaf-r3): tx_gbps 194.44, rx_gbps 93.33, q_tc3_max_kb 2,357.90, ecn_marked_tc3_rate 5,994,750.43, pfc_tx_p3_rate 0.00, pfc_rx_p3_rate 8,249.50
- leaf-r4 uplink eth1/33 (to spine-1): tx_gbps 195.02, rx_gbps 103.89, q_tc3_max_kb 1,879.10, ecn_marked_tc3_rate 5,886,255.50, pfc_tx_p3_rate 0.00, pfc_rx_p3_rate 4,780.00
- leaf-r4 eth1/1 (to orion-n01): tx_gbps 171.19, rx_gbps 52.68, q_tc3_max_kb 9.40, ecn_marked_tc3_rate 0.00, pfc_tx_p3_rate 2,649.50, pfc_rx_p3_rate 0.00

## pfc_storm

- leaf-r3 eth1/12 (to orion-n12): tx_gbps 0.03, rx_gbps 0.03, q_tc3_max_kb 3,995.00, ecn_marked_tc3_rate 0.00, pfc_tx_p3_rate 0.00, pfc_rx_p3_rate 23,730.00
- orion-n12 mlx5_3 (storm source): tx_gbps 0.03, rx_gbps 0.03, pfc_tx_p3_rate 23,730.00, pfc_rx_p3_rate 0.00, cnp_sent_rate 0.00
- leaf-r3 eth1/3 (to orion-n03): tx_gbps 158.63, rx_gbps 35.82, q_tc3_max_kb 12.60, ecn_marked_tc3_rate 0.00, pfc_tx_p3_rate 6,171.00, pfc_rx_p3_rate 0.00

## not_an_episode_520_558

- leaf-r4 eth1/7 (to orion-n07): tx_gbps 380.97, rx_gbps 160.78, q_tc3_max_kb 211.50, ecn_marked_tc3_rate 45,816.75, pfc_tx_p3_rate 0.00, pfc_rx_p3_rate 0.00
