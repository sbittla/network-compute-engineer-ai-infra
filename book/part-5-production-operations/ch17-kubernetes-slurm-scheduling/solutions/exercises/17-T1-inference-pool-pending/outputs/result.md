# 17-T1 reconciliation `[ILLUSTRATIVE]`

- allocated = 27 (= quota used 27)
- dashboard free = 21 = orion-n26 4, orion-n27 5, orion-n29 4, orion-n31 8
- physically idle = 64 − 27 = 37; hidden by allocatable 0: {'orion-n28': 8, 'orion-n30': 8}
- usable for the inference replica (minus dedicated n31): {'orion-n26': 4, 'orion-n27': 5, 'orion-n29': 4} → no node fits 8
- quota after request: 35 ≤ 48 (not the cause)
