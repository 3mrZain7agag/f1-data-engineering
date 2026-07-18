"""
Step 10 — Model Training
Trains binary classifiers for top10_finish and podium_finish, logs runs to MLflow.

Split strategy: train on all seasons except the most recent, test on the most
recent season. This avoids random-shuffle leakage (e.g. training on a driver's
2024 races and testing on other 2024 races from the same season) and mirrors
a realistic "predict the upcoming season" use case.

Run:
    python -m ml.train.train_model --target top10_finish
    python -m ml.train.train_model --target podium_finish

Requires: scikit-learn, xgboost, mlflow (add to requirements.txt)
"""

import argparse
import os
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

from ml.features.build_features import FEATURE_COLS

DATASET_PATH = "ml/data/training_dataset.csv"
MODELS_DIR = "ml/models"


def split_by_season(df: pd.DataFrame):
    latest_season = df["season"].max()
    train = df[df["season"] < latest_season]
    test = df[df["season"] == latest_season]
    return train, test, latest_season


def baseline_grid_heuristic(test_df: pd.DataFrame, target: str) -> float:
    """Dumb baseline: 'started well enough' heuristic to beat.
    top10_finish -> grid <= 10 ; podium_finish -> grid <= 3
    """
    threshold = 10 if target == "top10_finish" else 3
    preds = (test_df["grid_position"] <= threshold).astype(int)
    return accuracy_score(test_df[target], preds)


def evaluate(model, X_test, y_test) -> dict:
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy": accuracy_score(y_test, preds),
        "precision": precision_score(y_test, preds, zero_division=0),
        "recall": recall_score(y_test, preds, zero_division=0),
        "roc_auc": roc_auc_score(y_test, probs),
    }


def main(target: str):
    df = pd.read_csv(DATASET_PATH)
    train_df, test_df, latest_season = split_by_season(df)

    X_train, y_train = train_df[FEATURE_COLS], train_df[target]
    X_test, y_test = test_df[FEATURE_COLS], test_df[target]

    baseline_acc = baseline_grid_heuristic(test_df, target)

    mlflow.set_experiment("f1-race-outcome-prediction")

    with mlflow.start_run(run_name=f"logreg_{target}"):
        mlflow.log_param("model_type", "LogisticRegression")
        mlflow.log_param("target", target)
        mlflow.log_param("test_season", int(latest_season))
        mlflow.log_metric("baseline_grid_heuristic_accuracy", baseline_acc)

        logreg = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        )
        logreg.fit(X_train, y_train)
        metrics = evaluate(logreg, X_test, y_test)
        for k, v in metrics.items():
            mlflow.log_metric(k, v)
        mlflow.sklearn.log_model(logreg, "model")
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib.dump(logreg, os.path.join(MODELS_DIR, f"{target}_logreg.joblib"))
        print(f"[LogisticRegression | {target}] {metrics} | baseline={baseline_acc:.3f}")

    with mlflow.start_run(run_name=f"xgboost_{target}"):
        mlflow.log_param("model_type", "XGBoost")
        mlflow.log_param("target", target)
        mlflow.log_param("test_season", int(latest_season))
        mlflow.log_metric("baseline_grid_heuristic_accuracy", baseline_acc)

        xgb = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            eval_metric="logloss",
            random_state=42,
        )
        xgb.fit(X_train, y_train)
        metrics = evaluate(xgb, X_test, y_test)
        for k, v in metrics.items():
            mlflow.log_metric(k, v)
        mlflow.xgboost.log_model(xgb, "model")
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib.dump(xgb, os.path.join(MODELS_DIR, f"{target}_xgboost.joblib"))
        print(f"[XGBoost | {target}] {metrics} | baseline={baseline_acc:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target", choices=["top10_finish", "podium_finish"], required=True
    )
    args = parser.parse_args()
    main(args.target)