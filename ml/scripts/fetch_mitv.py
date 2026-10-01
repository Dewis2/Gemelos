"""Descarga el dataset académico externo Metro Interstate Traffic Volume (MITV-UCI).

El archivo se conserva sin modificar en la capa `raw`, siguiendo la misma convención
que el resto de fuentes externas del proyecto. La descarga es idempotente: si el archivo
ya existe y su perfil coincide con lo esperado, no se vuelve a bajar.

Uso:
    python -m ml.scripts.fetch_mitv [--force]
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

DATASET_URL = (
    "https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip"
)
#: El zip distribuido por UCI trae el CSV comprimido y con nombre underscored.
ARCHIVE_MEMBER = "Metro_Interstate_Traffic_Volume.csv.gz"
CSV_NAME = "Metro_Interstate_Traffic_Volume.csv"
REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_TARGET = REPO_ROOT / "data" / "external" / "mitv" / "traffic_volume" / "raw"
CSV_PATH = RAW_TARGET / CSV_NAME
PROFILE_PATH = RAW_TARGET / "download_report.json"

EXPECTED_ROWS = 48204
EXPECTED_COLUMNS = [
    "holiday",
    "temp",
    "rain_1h",
    "snow_1h",
    "clouds_all",
    "weather_main",
    "weather_description",
    "date_time",
    "traffic_volume",
]
TIMESTAMP_COLUMN = "date_time"
TARGET_COLUMN = "traffic_volume"


def download(force: bool) -> dict[str, object]:
    RAW_TARGET.mkdir(parents=True, exist_ok=True)

    if CSV_PATH.exists() and not force:
        report = verify()
        report["action"] = "reused_existing"
        return report

    with TemporaryDirectory() as temporary:
        archive = Path(temporary) / "mitv.zip"
        request = urllib.request.Request(DATASET_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=180) as response:
            archive.write_bytes(response.read())

        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            if ARCHIVE_MEMBER not in names:
                raise RuntimeError(
                    f"El archivo {ARCHIVE_MEMBER} no está en el zip. Contenido: {names}"
                )
            with (
                bundle.open(ARCHIVE_MEMBER) as source,
                gzip.open(source, "rb") as decompressed,
                CSV_PATH.open("wb") as target,
            ):
                shutil.copyfileobj(decompressed, target)

    report = verify()
    report["action"] = "downloaded"
    return report


def verify() -> dict[str, object]:
    """Comprueba el archivo descargado contra el perfil publicado del dataset."""
    import pandas as pd

    frame = pd.read_csv(CSV_PATH)
    header = list(frame.columns)
    missing = [column for column in EXPECTED_COLUMNS if column not in header]
    if missing:
        raise RuntimeError(f"Faltan columnas esperadas en el dataset: {missing}")
    if len(frame) != EXPECTED_ROWS:
        raise RuntimeError(
            f"Se esperaban {EXPECTED_ROWS} registros y se obtuvieron {len(frame)}."
        )

    timestamps = pd.to_datetime(frame[TIMESTAMP_COLUMN], utc=True)
    report: dict[str, object] = {
        "path": str(CSV_PATH),
        "url": DATASET_URL,
        "rows": len(frame),
        "columns": header,
        "timestamp_column": TIMESTAMP_COLUMN,
        "target_column": TARGET_COLUMN,
        "period_min": str(timestamps.min()),
        "period_max": str(timestamps.max()),
        "hours": int(timestamps.dt.hour.nunique()),
        "target_min": int(frame[TARGET_COLUMN].min()),
        "target_max": int(frame[TARGET_COLUMN].max()),
        "license": "CC BY 4.0 (UCI)",
        "scope": "external_academic_benchmark",
        "notice": (
            "Observaciones de Minnesota, EE. UU. Solo sirven para experimentación técnica "
            "del pipeline. No constituyen evidencia sobre Huancayo."
        ),
    }
    PROFILE_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the MITV-UCI benchmark dataset")
    parser.add_argument("--force", action="store_true", help="Volver a descargar el archivo")
    arguments = parser.parse_args()
    print(json.dumps(download(arguments.force), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()