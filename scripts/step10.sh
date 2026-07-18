#!/bin/bash
# Step 10 — Machine Learning: build features + train models
#
# Runs inside a dedicated virtual environment (.venv-ml) to avoid a protobuf
# version conflict between mlflow and dbt-core/dbt-adapters. This script
# creates that venv on first run and reuses it afterwards.
#
# Usage: bash scripts/step10.sh

set -e

VENV_DIR=".venv-ml"

if [ ! -d "$VENV_DIR" ]; then
    echo "=== Step 10: Creating isolated ML virtual environment ($VENV_DIR) ==="
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r ml/requirements-ml.txt
else
    source "$VENV_DIR/bin/activate"
fi

echo ""
echo "=== Step 10: Building feature dataset from Gold layer exports ==="
python -m ml.features.build_features

echo ""
echo "=== Step 10: Training models (top10_finish) ==="
python -m ml.train.train_model --target top10_finish

echo ""
echo "=== Step 10: Training models (podium_finish) ==="
python -m ml.train.train_model --target podium_finish

deactivate

echo ""
echo "=== Done. View results with: source .venv-ml/bin/activate && mlflow ui ==="