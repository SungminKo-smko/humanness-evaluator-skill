#!/usr/bin/env bash
# =============================================================================
# Humanness Evaluator Skill — Installer
#
# Usage (from the skill directory):
#   bash install.sh
#
# This script sets up the 'biophi' conda environment with all dependencies
# needed to run OASis humanness evaluation. BioPhiSkill is bundled inside
# this skill — no separate clone required.
# =============================================================================
set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="biophi"

echo "================================================"
echo "  Humanness Evaluator Skill — Installer"
echo "================================================"
echo "  Skill directory: $SKILL_DIR"

# 1. Check conda
if ! command -v conda &> /dev/null; then
    echo "ERROR: conda not found. Please install Miniconda or Anaconda first."
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# 2. Check / install HMMER
if ! command -v hmmscan &> /dev/null; then
    echo "[INFO] hmmer not found — will install via conda"
    INSTALL_HMMER="yes"
else
    echo "[INFO] hmmer already available"
    INSTALL_HMMER="no"
fi

# 3. Create / reuse conda environment
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "[INFO] Conda environment '${ENV_NAME}' already exists. Skipping creation."
else
    echo "[INFO] Creating conda environment '${ENV_NAME}' (Python 3.9)..."
    conda create -y -n "${ENV_NAME}" python=3.9
fi

# 4. Install HMMER + abnumber via conda
if [ "$INSTALL_HMMER" = "yes" ]; then
    echo "[INFO] Installing hmmer and abnumber via conda..."
    conda install -y -n "${ENV_NAME}" -c bioconda -c conda-forge abnumber hmmer
else
    echo "[INFO] Installing abnumber via conda..."
    conda install -y -n "${ENV_NAME}" -c bioconda -c conda-forge abnumber
fi

# 5. Install the bundled biophi package and all pip dependencies
echo "[INFO] Installing bundled biophi package..."
conda run -n "${ENV_NAME}" pip install -e "${SKILL_DIR}[viz]" --quiet

echo ""
echo "================================================"
echo "  Installation complete!"
echo ""
echo "  Activate with:"
echo "    conda activate ${ENV_NAME}"
echo ""
echo "  Quick test:"
echo "    python -c \"from agent_api import evaluate_humanness; print('Humanness Evaluator ready!')\""
echo "================================================"
