# 12.18 — Why a 3 % misalignment cost on an idle fabric can be much larger in production

**On an idle fabric** the misaligned traffic that leaves on the "wrong" rail crosses the spines, and on
a non-blocking 1:1 fabric with nothing else running there is spare spine capacity: the extra hop adds a
little latency, so the benchmark shows ≈ 3 %.

**In production** three things change:

1. **The spines are shared.** Rail-aligned jobs barely use the spines; a misaligned job pushes its
   traffic through them alongside every other job's cross-rail and all-to-all traffic. Spine links that
   were idle in the benchmark are now contended, so the misaligned job's bandwidth drops and it slows
   others too.
2. **ECMP collisions and congestion.** RoCEv2 flows are few and large (low entropy); hashing several onto
   one spine uplink overloads it (Chapter 7), and the resulting ECN marks and PFC pauses (Chapter 9) spread
   to other flows on the same queues. An idle benchmark rarely shows collisions.
3. **Host-side costs.** A misaligned GPU↔NIC path crosses PCIe switches or the inter-socket link (`SYS`),
   which disables GPUDirect RDMA by default and stages data through host memory; under production load
   the host memory bandwidth and the inter-socket link are also used by data loading and checkpointing,
   so the penalty grows.

Synchronous training also amplifies any per-rank slowdown: the slowest rank sets the step time (Chapter
11), so a misalignment affecting a few ranks costs the whole job. Validate alignment from INFO logs and
counters, not from one idle benchmark.
