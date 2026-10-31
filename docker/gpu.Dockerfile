# syntax=docker/dockerfile:1
#
# L2 lab image: one package + PyTorch. With the default CUDA base it measures on a GPU when started
# with --gpus all and falls back to the CPU automatically when no GPU is visible. CI (no GPU) builds
# the small CPU-only variant: --build-arg BASE=python:3.11.11-slim-bookworm --build-arg TORCH_CPU=1
#
#   docker build -f docker/gpu.Dockerfile --build-arg PKG=book/part-4-distributed-ai/ch13-gpu-data-movement -t ai-infra-gpu:ch13 .
#   docker run --rm --gpus all ai-infra-gpu:ch13                 # measure on the GPU
#   docker run --rm ai-infra-gpu:ch13                            # CPU fallback
#
# Normally driven by scripts/hw_labs.py (build, run, test, evidence).

ARG BASE=pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime
FROM ${BASE}
ARG TORCH_CPU=0
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY docker/requirements-gpu.lock /tmp/requirements-gpu.lock
# Read-only host-inspection tools the Ch 3 collector and other L2 probes call (lspci, iostat, numactl, ip, ethtool, lstopo)
RUN apt-get update \
 && apt-get install -y --no-install-recommends pciutils sysstat numactl iproute2 ethtool hwloc-nox \
 && rm -rf /var/lib/apt/lists/*
RUN if [ "$TORCH_CPU" = "1" ]; then pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu; fi \
 && pip install --no-cache-dir -r /tmp/requirements-gpu.lock \
 && useradd --create-home --uid 1000 learner
COPY docker/hwlab/ /opt/hwlab/
ARG PKG
COPY --chown=learner ${PKG}/ /work/pkg/
USER learner
WORKDIR /work/pkg
CMD ["python", "/opt/hwlab/run.py", "--pkg", "/work/pkg", "--out", "/results"]
