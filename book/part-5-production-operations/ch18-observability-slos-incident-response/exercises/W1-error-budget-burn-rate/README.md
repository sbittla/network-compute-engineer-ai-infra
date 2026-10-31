# W1 · Error budget and burn rate for chat-70b (★★ · L1)

Type: worked-problem · Kind: computed · Points: 10

<!-- prompt:start -->
**W1 ★★ L1 — Error budget and burn rate.** `chat-70b` has a 99.9 % availability SLO over 30 days and
serves an average 3,000 requests per minute.
(a) Compute the budget in failed requests and in equivalent minutes of total outage.
(b) A bad config causes 0.6 % errors for 90 minutes. Compute the burn rate and the fraction of budget
consumed. Does either page condition of Table 18.5, or the ticket condition, fire during those 90
minutes?
(c) Repeat for 2 % errors for 90 minutes; if a page fires, when (minutes after onset, including
`for: 2m`)?
(d) At the burn rate of (b), how long until the budget is exhausted?
*Evidence required:* every formula, substitution, and result; a yes/no with the window values for each
alert condition.
<!-- prompt:end -->

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
