#!/bin/bash
# Predict the podium (top 3) for the newest race in the Gold layer data.
# If that race already has results, compares prediction to actual outcome.
# Usage: bash scripts/predict_latest_podium.sh

set -e

VENV_DIR=".venv-ml"

if [ ! -d "$VENV_DIR" ]; then
    echo "No $VENV_DIR found. Run 'bash scripts/step10.sh' first to set up the ML environment and train models."
    exit 1
fi

source "$VENV_DIR/bin/activate"
python -m ml.predict.predict_latest_podium
deactivate