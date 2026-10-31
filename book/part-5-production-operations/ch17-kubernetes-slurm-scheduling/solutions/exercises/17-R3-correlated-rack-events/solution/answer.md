# 17-R3 — Rack events are not independent

**The assumption.** Section 17.6 models a job spanning *k* racks as hit with probability
1 − (1 − p)^k ≈ k·p, which assumes each rack fails independently, so packing a gang into fewer racks
lowers its exposure.

**Why it is false on ORION (any one):**
- a **shared CDU loop or PDU** feeding several racks: one coolant or power event takes out rack-05
  and rack-06 together;
- a **frontend leaf pair** serving several racks (storage and control traffic);
- a **Chapter 16 upgrade wave** or a facilities maintenance window defined over several racks at once.

With a shared domain, two racks on the same CDU behave like *one* failure domain: a job packed into
those two racks has exposure ≈ p_domain, while a job "spread" across two racks on different CDUs has
≈ 2·p_domain; but a job split across one rack on each of two domains that each serve many racks is
exposed to both. Rack count is the wrong unit.

**Modified rule.** Define placement domains by *shared infrastructure* (CDU loop, PDU feed, leaf
pair, maintenance wave) from the inventory; **compact gangs within one domain** (a training job
loses all progress since the last checkpoint if any member fails, so fewer domains is better);
**spread replicas of a service across domains** (the opposite rule: inference availability needs
independence between replicas). Wave planning (Chapter 16) should cap nodes per domain, not only per
rack.
