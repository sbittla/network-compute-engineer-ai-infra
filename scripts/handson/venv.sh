# Shared Python environment for the hands-on labs: source it, then use "$HANDSON_PY".
#   . scripts/handson/venv.sh            # creates ~/.venvs/ai-infra-handson on first use
# PyTorch is pinned to the CUDA 12.4 build (works on driver >= 550 and in WSL2); other packages are pinned too.
HANDSON_VENV="${HANDSON_VENV:-$HOME/.venvs/ai-infra-handson}"
if [ ! -x "$HANDSON_VENV/bin/python" ]; then
  command -v python3 >/dev/null || { echo "python3 missing" >&2; exit 1; }
  python3 -m venv "$HANDSON_VENV" 2>/dev/null || { apt-get install -y -qq python3-venv >/dev/null && python3 -m venv "$HANDSON_VENV"; }
  "$HANDSON_VENV/bin/pip" install -q --upgrade pip
  "$HANDSON_VENV/bin/pip" install -q "torch==2.5.1" --index-url https://download.pytorch.org/whl/cu124
  "$HANDSON_VENV/bin/pip" install -q "numpy==2.1.3" "pandas==2.2.3" "pyyaml==6.0.2" "requests==2.32.3"
fi
HANDSON_PY="$HANDSON_VENV/bin/python"
export HANDSON_VENV HANDSON_PY
