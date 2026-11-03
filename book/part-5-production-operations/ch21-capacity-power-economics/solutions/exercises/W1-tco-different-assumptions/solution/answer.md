# W1 — TCO under different assumptions: worked solution

Source: manuscript Section 21.4 (Table 21.3 and the cost ladder). Unchanged inputs come from
`lab/data/assumptions.yaml` `[ILLUSTRATIVE]`. All results are `[MODELED]` and reproduced by `solve.py`.

Changed inputs: amortization 5 years (was 4); electricity $0.12/kWh (was $0.08); allocation 0.80 (was
0.85); goodput 0.90 (was 0.88); PUE 1.25 (canonical, unchanged).

Hardware capex = 32 × ($320k + $85k) + $2.0M storage = $14.96M.

| Component | Formula and substitution | $/yr |
|---|---|---|
| Capex amortization | $14.96M / 5 | 2,992,000 |
| Power | 32 × 8.5 kW × 1.12 = 304.64 kW IT × 1.25 × 8,760 h × $0.12 | 400,297 |
| Space | 32 × 10.2 × 1.12 = 365.57 kW × $130 × 12 | 570,286 |
| Support | 0.08 × $14.96M | 1,196,800 |
| Staff | 4 FTE × $240k | 960,000 |
| **Total** | | **6,119,383 ≈ $6.12M** |

Shares of the total: capex 48.9 %, support 19.6 %, staff 15.7 %, space 9.3 %, power 6.5 %.

**Unit costs.**

```text
nominal GPU-h/yr = 256 × 8,760 = 2,242,560
$/nominal GPU-h  = 6,119,383 / 2,242,560                    = $2.73
usable fraction  = 0.97 × 0.922 × 0.95                       = 0.8496
$/allocated GPU-h = 2.7287 / (0.8496 × 0.80) = 2.7287 / 0.680 = $4.01
$/useful GPU-h    = 4.0146 / 0.90                             = $4.46
```

**Interpretation.** Against the base case ($6.73M; $3.00 nominal and $4.72 useful), the longer
amortization cuts capex by $0.75M/yr. The 33 % higher electricity price adds only $0.10M, because power
is a small share. Lower allocation and higher goodput partly offset each other: 0.85 × 0.88 = 0.748 in
the base case against 0.80 × 0.90 = 0.720 here. Net: nominal −9.6 %, useful −6.1 %. The 5-year
assumption is only valid if the GPUs stay competitive and supported for 5 years (Section 21.4
production note).

**Common wrong answers**

- Replacing the 0.85 *inside* the usable fraction with 0.80 (or dropping the usable fraction), giving
  2.73 / 0.80 / 0.90 = $3.79. Allocation applies *after* the usable fraction.
- Applying the $0.12 price to provisioned 10.2 kW nodes ($0.48M). Energy uses sustained power.
- Forgetting the $2.0M storage capex in both amortization and support.
