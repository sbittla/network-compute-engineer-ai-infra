# 14.12 — The resume that trained worse (★★★, L1)

Type: troubleshooting · Kind: computed

## Prompt

<!-- prompt:start -->
**14.12 The resume that trained worse** ★★★ · L1
After a node failure at 03:13, W-TRAIN restarted automatically at 03:28, at the same 256-GPU
layout using a replacement node from Halcyon's spare pool outside ORION-256 (Section 14.12, Step 7),
and has been running for two hours. The training loss before the failure was 1.82 and falling; since the restart it has been
2.25–2.31 and is not recovering. Evidence available:

```text
03:02:11 rank0 ckpt step=88290 phase=snapshot blocking_s=0.65
03:02:30 rank0 ckpt step=88290 phase=commit completion_s=18.9
03:12:55 rank0 ckpt step=88327 phase=snapshot blocking_s=0.66
03:13:02 scheduler: node orion-n21 NOT_RESPONDING; job 4471 failed
03:26:10 restart-controller: resolved checkpoint via /pfs/ckpt/w-train/latest -> step_088327
03:27:21 rank0 load step=88327 shards_loaded=256 missing=0 warnings=31
03:28:00 rank0 step=88328 loss=2.27
```

```console
$ ls /pfs/ckpt/w-train/step_088327/ | head -3; ls /pfs/ckpt/w-train/step_088327/ | wc -l
manifest.json
shard_000.bin
shard_001.bin
257
$ ls /pfs/ckpt/w-train/step_088327/COMMIT
ls: cannot access '/pfs/ckpt/w-train/step_088327/COMMIT': No such file or directory
```

(a) Apply the diagnostic loop: state the symptom, rank at least three hypotheses, and give the
discriminating evidence for each. (b) What is the most likely root cause, and what would the 31 load
warnings probably say? (c) What is the safe recovery action now, and what does it cost in GPU-hours?
(d) What two changes prevent recurrence? *Evidence required:* hypothesis table, the recovery
decision with arithmetic, and the two changes mapped to Section 14.10.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/incident_analysis.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
