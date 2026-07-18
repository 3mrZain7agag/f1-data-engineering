#!/bin/bash
# Predict top10_finish or podium_finish for any race, with any saved model.
# Activates the ML venv automatically, then passes all arguments straight
# through to predict_race.py.
#
# Usage examples:
#   bash scripts/predict_race.sh                                   # latest race, top10_finish, xgboost, top 3
#   bash scripts/predict_race.sh --target podium_finish             # latest race, podium
#   bash scripts/predict_race.sh --race-id 2026_05 --target podium_finish --top 5
#   bash scripts/predict_race.sh --model logreg

set -e

VENV_DIR=".venv-ml"

if [ ! -d "$VENV_DIR" ]; then
    echo "No $VENV_DIR found. Run 'bash scripts/step10.sh' first to set up the ML environment and train models."
    exit 1
fi

source "$VENV_DIR/bin/activate"
python -m ml.predict.predict_race "$@"
deactivate