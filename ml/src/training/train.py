import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from ml.src.evaluation.evaluate import regression_metrics
from ml.src.features.features import build_time_features
from ml.src.preprocessing.temporal import temporal_split


def train(
    dataset: Path,
    output: Path,
    model_name: str,
    timestamp_column: str,
    target_column: str,
) -> dict[str, Any]:
    frame = build_time_features(pd.read_csv(dataset), timestamp_column)
    train_frame, test_frame = temporal_split(frame, timestamp_column)
    feature_columns = ["hour", "day_of_week", "month", "is_weekend"]
    estimator = (
        LinearRegression()
        if model_name == "linear"
        else RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    )
    estimator.fit(train_frame[feature_columns], train_frame[target_column])
    predicted = estimator.predict(test_frame[feature_columns])
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(estimator, output)
    return {
        "model": model_name,
        "features": feature_columns,
        "train_rows": len(train_frame),
        "test_rows": len(test_frame),
        "metrics": regression_metrics(
            test_frame[target_column].tolist(), predicted.tolist()
        ),
        "notice": "Technical experiment only; not a validation for Huancayo 2026.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a traffic-flow baseline with temporal split"
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("ml/models/traffic_model.joblib")
    )
    parser.add_argument(
        "--model", choices=["linear", "random-forest"], default="linear"
    )
    parser.add_argument("--timestamp-column", default="timestamp")
    parser.add_argument("--target-column", default="traffic_volume")
    args = parser.parse_args()
    print(
        json.dumps(
            train(
                args.dataset,
                args.output,
                args.model,
                args.timestamp_column,
                args.target_column,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
