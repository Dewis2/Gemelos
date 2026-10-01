"""Entrena el modelo de flujo vehicular y publica la metadata que consume la API.

Reutiliza el pipeline existente (`ml.src.training.train`) sobre el dataset académico
externo MITV-UCI y escribe `metadata.json` con resultados de la corrida. No se
introduce ninguna métrica que el entrenamiento no haya calculado.

Uso:
    python -m ml.scripts.train_and_publish
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib

from ml.src.training.train import train

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = (
    REPO_ROOT
    / "data"
    / "external"
    / "mitv"
    / "traffic_volume"
    / "raw"
    / "Metro_Interstate_Traffic_Volume.csv"
)
DOWNLOAD_REPORT = (
    REPO_ROOT
    / "data"
    / "external"
    / "mitv"
    / "traffic_volume"
    / "raw"
    / "download_report.json"
)
MODEL_PATH = REPO_ROOT / "ml" / "models" / "traffic_model.joblib"
METADATA_PATH = REPO_ROOT / "ml" / "models" / "demo_peru" / "metadata.json"

MODEL_NAMES = {"random-forest": "random_forest", "linear": "linear_regression"}


def month_range(period: dict[str, str]) -> dict[str, str]:
    return {"min": period["min"][:7], "max": period["max"][:7]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and publish the traffic-flow model")
    parser.add_argument(
        "--selected",
        choices=["random-forest", "linear"],
        default="random-forest",
        help="Modelo publicado. Random Forest es el baseline del proyecto.",
    )
    arguments = parser.parse_args()

    if not RAW_CSV.is_file():
        raise SystemExit(
            f"Falta el dataset en {RAW_CSV}. Ejecuta primero: python -m ml.scripts.fetch_mitv"
        )

    # Se entrenan ambos modelos del pipeline existente; las metricas se comparan y se
    # publica el baseline del proyecto. No se inventa ninguna cifra.
    results: dict[str, dict[str, object]] = {}
    for choice in ("random-forest", "linear"):
        artifact = (
            MODEL_PATH
            if choice == "random-forest"
            else MODEL_PATH.with_name(f"traffic_model_{MODEL_NAMES[choice]}.joblib")
        )
        results[MODEL_NAMES[choice]] = train(
            RAW_CSV,
            artifact,
            MODEL_NAMES[choice],
            timestamp_column="date_time",
            target_column="traffic_volume",
        )

    selected = MODEL_NAMES[arguments.selected]
    selected_run = results[selected]
    selected_artifact = (
        MODEL_PATH
        if arguments.selected == "random-forest"
        else MODEL_PATH.with_name(f"traffic_model_{MODEL_NAMES[arguments.selected]}.joblib")
    )

    model_version = f"{arguments.selected}-mitv-{datetime.now(UTC):%Y%m%d}"
    estimator = joblib.load(selected_artifact)
    estimator.model_version = model_version
    joblib.dump(estimator, selected_artifact)

    metrics = {
        name: {**dict(run["metrics"]), "mape": None} for name, run in results.items()
    }
    download = json.loads(DOWNLOAD_REPORT.read_text(encoding="utf-8"))

    metadata: dict[str, object] = {
        "experiment": "mitv_hourly_traffic_volume",
        "scope": "external_academic_benchmark",
        "warning": (
            "Modelo experimental de PoC entrenado con MITV-UCI (Metro Interstate Traffic Volume, "
            "Minnesota, EE. UU.). Corresponde a otro contexto geográfico: no ha sido validado con "
            "datos locales actuales de la Av. Ferrocarril y no representa tráfico de Huancayo."
        ),
        "training_dataset": "mitv_uci_metro_interstate",
        "provider": "UCI Machine Learning Repository",
        "source_url": download["url"],
        "license": download["license"],
        "created_at": datetime.now(UTC).isoformat(),
        "geography": "Minnesota, EE. UU.",
        "rows_total": download["rows"],
        "temporal_granularity": "hour",
        "timestamp_column": "date_time",
        "target": "traffic_volume (veh/h)",
        "target_min": download["target_min"],
        "target_max": download["target_max"],
        "training_period": month_range(dict(selected_run["train_period"])),
        "test_period": month_range(dict(selected_run["test_period"])),
        "temporal_split": True,
        "train_rows": selected_run["train_rows"],
        "test_rows": selected_run["test_rows"],
        "features": selected_run["features"],
        "selected_model": selected,
        "model_artifact": "ml/models/traffic_model.joblib",
        "model_version": model_version,
        "metrics": metrics,
        "prediction_series_aggregation": "monthly_mean",
        "prediction_series": selected_run["prediction_series"],
        "inference_contract": {
            "endpoint": "/api/v1/predictions/traffic-flow",
            "features": selected_run["features"],
            "note": (
                "El backend construye el vector con sorted(features), por lo que el orden "
                "alfabético de estas variables es parte del contrato."
            ),
        },
    }

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        json.dumps(
            {
                "model_path": str(selected_artifact),
                "metadata_path": str(METADATA_PATH),
                "model_version": model_version,
                "selected_model": selected,
                "metrics": metrics,
                "train_rows": selected_run["train_rows"],
                "test_rows": selected_run["test_rows"],
                "features": selected_run["features"],
                "prediction_series_points": len(selected_run["prediction_series"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()