# 14.3 result `[MODELED]`

| Component | B/param | Checkpointed |
|---|---|---|
| bf16_weights | 2 | yes |
| bf16_gradients | 2 | no |
| fp32_master_weights | 4 | yes |
| adam_m_fp32 | 4 | yes |
| adam_v_fp32 | 4 | yes |

Training state 16 B/param; checkpoint 14 B/param (gradients recomputed).
W-TRAIN: 7e+10 × 14 B = 980 GB
