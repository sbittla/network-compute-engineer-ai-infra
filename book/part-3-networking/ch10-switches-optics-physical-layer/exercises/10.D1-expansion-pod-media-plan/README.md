# 10.D1 — Media plan for ORION's expansion pod (★★★, L1)

**Type:** Design challenge · **Kind:** written · **Points:** 10

## Prompt

<!-- prompt:start -->
**10.D1 — Media plan for ORION's expansion pod.** Halcyon adds a 16-node pod. The new rail leaves sit
in a network rack 3 m from the new spines; the GPU racks are 25–40 m from the network rack; the pod
must connect to the existing spines in the old hall 350 m away. Choose a medium (DAC, AEC, AOC, SR8,
DR4, FR4) for (i) host links, (ii) new leaf ↔ new spine, (iii) new spine ↔ old spine/super-spine, and
choose single-port vs twin-port switch modules. Defend each choice on reach, power, failure modes,
sparing, and cleaning burden, and state what you would verify with the vendors.
*Evidence required:* a decision table (link class × medium × reason), an optics-power estimate with
stated per-module power, and the spare-part list implied by your choices.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/10.D1-expansion-pod-media-plan/` (instructor material in the full repository; removed from student releases).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`).
