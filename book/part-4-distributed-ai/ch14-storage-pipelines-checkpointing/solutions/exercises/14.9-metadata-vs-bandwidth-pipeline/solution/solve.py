"""14.9 -- Metadata-bound vs bandwidth-bound data pipeline on 16 HX8 nodes. [MODELED]

Usage: python solve.py --out DIR
Inputs (prompt, [ILLUSTRATIVE]): 2,000 images/s per GPU, 8 GPUs/node, 16 nodes, 40e6 images of 120 KB,
MDS 50,000 open/s, PFS read 160 GB/s; open 4.0 ms, read 0.6 ms, close 0.2 ms; 512 MiB shards read in
16 MiB requests of 12 ms. HX8 local NVMe 8 × 3.84 TB (docs/REFERENCE_CLUSTER.md).
"""
import argparse
import json
from pathlib import Path

GPUS_PER_NODE, NODES = 8, 16
IMG_PER_GPU = 2000
IMG_B = 120e3
N_IMAGES = 40e6
MDS_OPEN_PER_S = 50_000
PFS_READ_BPS = 160e9
OPEN_S, READ_S, CLOSE_S = 4.0e-3, 0.6e-3, 0.2e-3
SHARD_B = 512 * 2**20
REQ_B = 16 * 2**20
REQ_S = 12e-3
NVME_PER_NODE_B = 8 * 3.84e12


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    img_node = GPUS_PER_NODE * IMG_PER_GPU
    bps_node = img_node * IMG_B
    img_cl, bps_cl = img_node * NODES, bps_node * NODES
    per_sample = OPEN_S + READ_S + CLOSE_S
    inflight_files = img_node * per_sample
    max_img_node = MDS_OPEN_PER_S / NODES
    img_per_shard = SHARD_B / IMG_B
    opens_node = img_node / img_per_shard
    share = bps_cl / PFS_READ_BPS
    req_rate = bps_node / REQ_B
    inflight_shard = req_rate * REQ_S
    dataset = N_IMAGES * IMG_B
    stage_total = dataset * NODES
    stage_s = stage_total / PFS_READ_BPS

    # Key 14.9 values (tolerances in the units shown).
    checks = [(img_node, 16000, 0), (bps_node / 1e9, 1.92, 0.005), (img_cl, 256000, 0), (bps_cl / 1e9, 30.7, 0.05),
              (inflight_files, 76.8, 0.05), (max_img_node, 3125, 0), (max_img_node / img_node * 100, 19.5, 0.05),
              (img_per_shard, 4474, 1), (opens_node, 3.6, 0.05), (opens_node * NODES, 57, 0.5), (share * 100, 19, 0.5),
              (req_rate, 114, 0.5), (inflight_shard, 1.4, 0.05), (dataset / 1e12, 4.8, 0.01),
              (stage_total / 1e12, 76.8, 0.05), (stage_s, 480, 0.5)]
    for got, want, tol in checks:
        assert abs(got - want) <= tol, (got, want)
    assert dataset < NVME_PER_NODE_B

    cls = {"file_per_image": "metadata-bound", "shards": "bandwidth-bound (far from limit)",
           "local_staging": "fits on NVMe; one-off bandwidth-bound copy"}
    ans = {"a_img_per_s_node": img_node, "a_GBps_node": round(bps_node / 1e9, 2), "a_img_per_s_cluster": img_cl,
           "a_GBps_cluster": round(bps_cl / 1e9, 1), "b_inflight_per_node": round(inflight_files, 1),
           "b_open_rate_needed": img_cl, "b_max_img_per_s_node": max_img_node,
           "c_images_per_shard": round(img_per_shard), "c_opens_per_s_node": round(opens_node, 2),
           "c_pfs_share_pct": round(share * 100, 1), "c_requests_per_s_node": round(req_rate, 1),
           "c_inflight_per_node": round(inflight_shard, 2), "d_dataset_TB": round(dataset / 1e12, 2),
           "d_stage_all_nodes_s": round(stage_s, 1), "classification": cls,
           "e_recommendation": "repack into shards (optionally plus local staging)"}
    result = {"inputs": {"img_per_gpu": IMG_PER_GPU, "gpus_per_node": GPUS_PER_NODE, "nodes": NODES,
                         "image_B": IMG_B, "n_images": N_IMAGES, "mds_open_per_s": MDS_OPEN_PER_S,
                         "pfs_read_Bps": PFS_READ_BPS, "shard_B": SHARD_B, "request_B": REQ_B, "request_s": REQ_S},
              "steps": {"per_sample_latency_s": round(per_sample, 4)},
              "answer": ans, "units": {"rates": "1/s", "bandwidth": "GB/s (1e9 B/s)", "time": "s"},
              "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = "\n".join([
        "# 14.9 result `[MODELED]`", "",
        f"(a) {img_node:,} img/s and {bps_node/1e9:.2f} GB/s per node; {img_cl:,} img/s and {bps_cl/1e9:.1f} GB/s cluster",
        f"(b) in flight {inflight_files:.1f}/node; opens needed {img_cl:,}/s vs {MDS_OPEN_PER_S:,}/s -> "
        f"max {max_img_node:,.0f} img/s/node -> metadata-bound",
        f"(c) {img_per_shard:,.0f} img/shard; {opens_node:.1f} opens/s/node; PFS share {share*100:.0f} %; "
        f"{req_rate:.0f} req/s, {inflight_shard:.1f} in flight -> bandwidth-bound, far from limit",
        f"(d) dataset {dataset/1e12:.1f} TB fits in {NVME_PER_NODE_B/1e12:.1f} TB; staging {stage_total/1e12:.1f} TB "
        f"at 160 GB/s = {stage_s:.0f} s",
        "(e) repack into shards; confirm with meta_time_share >= 0.5 and mean_read_bytes < 1 MiB", ""])
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
