from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float | None]:
    result: dict[str, float | None] = {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": float(r2_score(y_true, y_pred)),
        "mape": None,
    }
    if bool((y_true != 0).all()):
        result["mape"] = float(
            np.mean(np.abs((y_true.to_numpy() - y_pred) / y_true)) * 100
        )
    return result


def prepare(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";", encoding="cp1252", dtype=str)
    frame = frame.loc[:, ~frame.columns.str.startswith("Unnamed")]
    frame["period"] = pd.to_datetime(frame["PERIODO"], format="%Y%m")
    frame["traffic_volume"] = (
        frame["VEH_TOTAL"].str.replace(r"\s+", "", regex=True).astype(float)
    )
    frame = frame.sort_values(["CODIGO_PEAJE", "period"])
    groups = frame.groupby("CODIGO_PEAJE", sort=False)["traffic_volume"]
    frame["lag_1"] = frame["traffic_volume"]
    frame["lag_2"] = groups.shift(1)
    frame["lag_3"] = groups.shift(2)
    frame["rolling_mean_3"] = groups.transform(
        lambda series: series.rolling(3, min_periods=3).mean()
    )
    frame["target_next_period"] = groups.shift(-1)
    frame["month"] = frame["period"].dt.month
    frame["year"] = frame["period"].dt.year
    return frame.dropna(
        subset=["lag_2", "lag_3", "rolling_mean_3", "target_next_period"]
    )


def run(data_path: Path, output_dir: Path) -> dict[str, object]:
    frame = prepare(data_path)
    periods = sorted(frame["period"].unique())
    split_index = max(1, int(len(periods) * 0.8))
    test_periods = periods[split_index:]
    if not test_periods:
        raise ValueError("No hay periodos suficientes para una división temporal")
    first_test = test_periods[0]
    train = frame[frame["period"] < first_test]
    test = frame[frame["period"] >= first_test]
    features = [
        "month",
        "year",
        "CODIGO_PEAJE",
        "lag_1",
        "lag_2",
        "lag_3",
        "rolling_mean_3",
    ]
    numeric = ["month", "year", "lag_1", "lag_2", "lag_3", "rolling_mean_3"]
    categorical = ["CODIGO_PEAJE"]
    preprocessor = ColumnTransformer(
        [
            ("numeric", "passthrough", numeric),
            ("location", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )
    models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=100,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
    }
    scores: dict[str, dict[str, float | None]] = {
        "naive_y_t_plus_1_equals_y_t": metrics(
            test["target_next_period"], test["lag_1"].to_numpy()
        )
    }
    fitted: dict[str, Pipeline] = {}
    predictions: dict[str, np.ndarray] = {}
    for name, estimator in models.items():
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", estimator)])
        pipeline.fit(train[features], train["target_next_period"])
        prediction = pipeline.predict(test[features])
        predictions[name] = prediction
        scores[name] = metrics(test["target_next_period"], prediction)
        fitted[name] = pipeline
    best_name = min(models, key=lambda name: float(scores[name]["mae"] or float("inf")))
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"{best_name}.joblib"
    joblib.dump(fitted[best_name], model_path)
    prediction_frame = pd.DataFrame(
        {
            "period": test["period"].dt.strftime("%Y-%m"),
            "actual": test["target_next_period"].to_numpy(),
            "predicted": predictions[best_name],
        }
    )
    prediction_series = (
        prediction_frame.groupby("period", as_index=False)[["actual", "predicted"]]
        .sum()
        .tail(24)
        .round(2)
        .to_dict(orient="records")
    )
    metadata: dict[str, object] = {
        "experiment": "peru_toll_traffic_next_period",
        "scope": "national_toll_demo_only",
        "warning": "Modelo experimental entrenado con datos nacionales de peaje; no es un modelo predictivo de la Av. Ferrocarril.",
        "training_dataset": "mtc_peru_toll_flow",
        "provider": "Ministerio de Transportes y Comunicaciones - MTC",
        "created_at": datetime.now(UTC).isoformat(),
        "training_period": {
            "min": train["period"].min().strftime("%Y-%m"),
            "max": train["period"].max().strftime("%Y-%m"),
        },
        "test_period": {
            "min": test["period"].min().strftime("%Y-%m"),
            "max": test["period"].max().strftime("%Y-%m"),
        },
        "temporal_split": True,
        "train_rows": len(train),
        "test_rows": len(test),
        "features": features,
        "target": "traffic_volume_next_month",
        "metrics": scores,
        "selected_model": best_name,
        "prediction_series": prediction_series,
        "model_artifact": str(model_path),
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/external/mtc/toll_flow/raw/mtc_toll_flow.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/models/demo_peru"),
    )
    args = parser.parse_args()
    print(json.dumps(run(args.data, args.output), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
