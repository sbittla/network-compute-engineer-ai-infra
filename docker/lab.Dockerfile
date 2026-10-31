# syntax=docker/dockerfile:1
#
# One self-contained image per lab package (chapter or capstone). Build context is the repo root;
# the image contains only the one package named by PKG, plus the pinned runtime and test harness.
#
#   docker build -f docker/lab.Dockerfile --build-arg PKG=book/part-3-networking/ch09-congestion-control-lossless-fabrics -t ai-infra-lab:ch09 .
#   docker run --rm --network none ai-infra-lab:ch09                    # full package test suite
#   docker build ... --target learner -t ai-infra-lab:ch09-learner .
#   docker run --rm -it --network none ai-infra-lab:ch09-learner        # learner: run the checker on starter/
#
# Normally driven by scripts/docker_labs.py (build, test, outputs, ci).

FROM python:3.13.1-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
COPY docker/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir -r /tmp/requirements.lock \
 && useradd --create-home --uid 1000 learner \
 && mkdir -p /results && chown learner /results
COPY docker/harness/run_lab.py /opt/harness/run_lab.py

# --- learner image: solutions, reviews, instructor material and generators stripped -------------
FROM runtime AS staging
ARG PKG
COPY ${PKG}/ /src/pkg/
RUN rm -rf /src/pkg/solutions /src/pkg/review /src/pkg/instructor \
           /src/pkg/lab/tools /src/pkg/starter-kit/tools

FROM runtime AS learner
COPY --from=staging --chown=learner /src/pkg /work/pkg
USER learner
WORKDIR /work/pkg
CMD ["python", "/opt/harness/run_lab.py", "--impl", "starter"]

# --- instructor/CI image (default): full package + test harness ---------------------------------
FROM runtime AS instructor
ARG PKG
LABEL org.opencontainers.image.title="ai-infra-lab" \
      org.opencontainers.image.description="AI Infrastructure Engineering lab package ${PKG}"
COPY --chown=learner docker/harness/ /opt/harness/
COPY --chown=learner ${PKG}/ /work/pkg/
USER learner
WORKDIR /work/pkg
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "/opt/harness/test_package.py", \
     "--pkg", "/work/pkg", "--junitxml=/results/junit.xml"]
