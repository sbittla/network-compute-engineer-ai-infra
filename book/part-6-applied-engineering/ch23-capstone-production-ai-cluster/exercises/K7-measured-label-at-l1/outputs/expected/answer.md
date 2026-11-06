# K7 — Which numbers may be `[MEASURED]` at tier L1

**Source:** manuscript Section 23.7 (realism boundary under "Scaling efficiency"); docs/LAB_STANDARDS.md;
key K7.

Rule: `[MEASURED]` means the number was observed on the system it describes, in an environment that a
manifest records. At L1 a laptop really measures things that happen *on the laptop*; it cannot measure
GPU, NIC, NVLink or fabric performance.

| Item | May it be `[MEASURED]` at L1? | Correct label | Why |
|---|---|---|---|
| (a) Linter runtime on a laptop | **Yes** | `[MEASURED]` (cite the manifest: CPU, OS, Python version, bundle) | The laptop ran the linter; the runtime is a real observation of that system. The reference bundle's B-06 row is exactly this |
| (b) NCCL bus bandwidth from a model | No | `[MODELED]` | Computed from a formula and assumed bandwidth; nothing was observed |
| (c) Parse time of a 1 GB telemetry file | **Yes**, for the laptop's parse time | `[MEASURED]` | A real measurement of the parser on that machine; it must not be presented as the production collector's throughput |
| (d) TTFT from a serving simulator | No | `[SIMULATED]` | The simulator's output depends on its model; state what it does not capture (real kernels, batching scheduler, network jitter) |

**Common wrong answers.** Labelling (d) `[MEASURED]` "because we ran it" — running a simulator measures
the simulator, not the serving system. Labelling (a) or (c) `[MODELED]` out of excess caution loses the
only legitimate measurements an L1 capstone has. Labelling (b) `[MEASURED]` is the defect the lab's
EVID-004 rule catches (a physical fabric claim from an L1 tier), and under `capstones/RUBRIC.md` it caps
the measurement dimension.
