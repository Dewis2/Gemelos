import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from ml.src.evaluation.evaluate import regression_metrics
from ml.src.features.features import CALENDAR_FEATURES, build_time_features
from ml.src.preprocessing.temporal import temporal_split


def monthly_series(
    frame: pd.DataFrame,
    timestamp_column: str,
    target_column: str,
    predicted: np.ndarray,
) -> list[dict[str, float | str]]:
    """Aggregate the test-set comparison by month so the UI can plot it legibly."""
    monthly = (
        pd.DataFrame(
            {
                "period": pd.to_datetime(
                    frame[timestamp_column], utc=True
                ).dt.strftime("%Y-%m"),
                "actual": frame[target_column].to_numpy(),
                "predicted": predicted,
            }
        )
        .groupby("period", as_index=False)
        .agg(actual=("actual", "mean"), predicted=("predicted", "mean"))
    )
    return [
        {
            "period": str(row.period),
            "actual": round(float(row.actual), 2),
            "predicted": round(float(row.predicted), 2),
        }
        for row in monthly.itertuples()
    ]


def train(
    dataset: Path,
    output: Path,
    model_name: str,
    timestamp_column: str,
    target_column: str,
) -> dict[str, Any]:
    frame = build_time_features(pd.read_csv(dataset), timestamp_column)
    train_frame, test_frame = temporal_split(frame, timestamp_column)
    feature_columns = list(CALENDAR_FEATURES)
    # Se aceptan tanto el nombre de la CLI ("linear") como el canonico
    # ("linear_regression"); comparar contra una sola cadena hacIA que un alias
    # cayera en la rama de Random Forest y produjera metricas duplicadas.
    estimator = (
        LinearRegression()
        if model_name.casefold() in {"linear", "linear_regression"}
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
        "train_period": {
            "min": str(train_frame[timestamp_column].min()),
            "max": str(train_frame[timestamp_column].max()),
        },
        "test_period": {
            "min": str(test_frame[timestamp_column].min()),
            "max": str(test_frame[timestamp_column].max()),
        },
        "metrics": regression_metrics(
            test_frame[target_column].tolist(), predicted.tolist()
        ),
        "prediction_series": monthly_series(
            test_frame, timestamp_column, target_column, predicted
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
