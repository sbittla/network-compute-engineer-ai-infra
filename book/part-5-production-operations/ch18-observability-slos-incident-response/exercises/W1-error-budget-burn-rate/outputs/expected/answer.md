# W1 — Error budget and burn rate for chat-70b

SLO 99.9 % over 30 days (43,200 min); average 3,000 requests/min. Policy: Table 18.5. `[MODELED]`

**(a) Budget.** Requests = 3,000 × 43,200 = 129.6 × 10⁶. Budget = 0.001 × 129.6 × 10⁶ = **129,600
failed requests** ≡ 0.001 × 43,200 = **43.2 min** of total outage.

**(b) 0.6 % errors for 90 min.** Burn = 0.006 / 0.001 = **6**. Budget consumed = 6 × 90 / 43,200 =
**1.25 %** (check: 0.006 × 3,000 × 90 = 1,620 failures; 1,620 / 129,600 = 1.25 %). Window values at
t = 90 min (worst point):

| Condition | Window burns | Fires? |
|---|---|---|
| Page: 1 h > 14.4 and 5 m > 14.4 | 1 h = 6, 5 m = 6 | **No** |
| Page: 6 h > 6 and 30 m > 6 | 30 m = 6 (not > 6); 6 h = 0.006 × 90/360 / 0.001 = 1.5 | **No** |
| Ticket: 3 d > 1 and 6 h > 1 | 6 h = 1.5 > 1; 3 d = 0.006 × 90/4,320 / 0.001 = 0.125 | **No** |

Nothing fires, by design: a 1.25 % budget spend does not justify waking anyone (though the 30 m
window sits exactly on its threshold; any extra error would trip it).

**(c) 2 % errors for 90 min.** Burn = 0.02 / 0.001 = **20**. The 1 h window exceeds 1.44 % when
0.02 × t / 60 > 0.0144 → t > **43.2 min**; the 5 m window after 0.02 × t / 5 > 0.0144 → t > 3.6 min.
The condition is true from 43.2 min; with `for: 2m` the page fires at **≈ 45 min** after onset (plus up
to one evaluation interval). The 6 h / 30 m pair needs 0.02 × t / 360 > 0.006 → t > 108 min, after
the incident ends. Budget consumed = 20 × 90 / 43,200 = **4.17 %**.

**(d) Exhaustion at burn 6:** 30 days / 6 = **5 days (120 h)**.

**Common mistakes:** forgetting that the long window dilutes errors over its whole length; treating
"= threshold" as firing; computing the burn from the error count rather than the ratio.
`solve.py` evaluates every window and asserts the key.
