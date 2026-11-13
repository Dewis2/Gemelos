"""Export traffic records with pseudonymous IDs and SHA-256 manifests.

This is an offline, read-only administrative operation. It intentionally has no
public API route because the prototype does not yet have user authentication.
"""

import argparse
import csv
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import create_engine, text

QUERIES = {
    "measurements": """
        SELECT m.id, m.source_id, s.name AS source_name, m.road_segment_id,
               m.timestamp, m.traffic_volume, m.average_speed, m.occupancy
        FROM public.traffic_measurements AS m
        JOIN public.data_sources AS s ON s.id = m.source_id
        ORDER BY m.timestamp, m.id
    """,
    "predictions": """
        SELECT id, road_segment_id, prediction_timestamp, target_timestamp,
               predicted_volume, model_version
        FROM public.traffic_predictions
        ORDER BY prediction_timestamp, id
    """,
}
FIELDS = {
    "measurements": (
        "record_token",
        "source_token",
        "source_name",
        "road_segment_token",
        "timestamp_utc",
        "traffic_volume",
        "average_speed",
        "occupancy",
    ),
    "predictions": (
        "record_token",
        "road_segment_token",
        "prediction_timestamp_utc",
        "target_timestamp_utc",
        "predicted_volume",
        "model_version",
    ),
}


def token(key: bytes, identifier: UUID) -> str:
    return hmac.new(key, str(identifier).encode("ascii"), hashlib.sha256).hexdigest()[
        :24
    ]


def timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Database timestamp has no time zone")
    return value.astimezone(UTC).isoformat()


def sanitize(kind: str, row: dict[str, object], key: bytes) -> dict[str, object]:
    if kind == "measurements":
        return {
            "record_token": token(key, row["id"]),
            "source_token": token(key, row["source_id"]),
            "source_name": row["source_name"],
            "road_segment_token": token(key, row["road_segment_id"]),
            "timestamp_utc": timestamp(row["timestamp"]),
            "traffic_volume": row["traffic_volume"],
            "average_speed": row["average_speed"],
            "occupancy": row["occupancy"],
        }
    return {
        "record_token": token(key, row["id"]),
        "road_segment_token": token(key, row["road_segment_id"]),
        "prediction_timestamp_utc": timestamp(row["prediction_timestamp"]),
        "target_timestamp_utc": timestamp(row["target_timestamp"]),
        "predicted_volume": row["predicted_volume"],
        "model_version": row["model_version"],
    }


def export(database_url: str, key: bytes, output_dir: Path) -> dict[str, object]:
    if len(key) < 32:
        raise ValueError("EXPORT_PSEUDONYM_KEY must be at least 32 bytes")
    if output_dir.exists():
        raise ValueError("Output directory already exists")
    output_dir.mkdir(parents=True)
    engine = create_engine(database_url, pool_pre_ping=True)
    manifest: dict[str, object] = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": "read-only snapshot of traffic_measurements and traffic_predictions",
        "identifiers": "HMAC-SHA256 pseudonyms; key omitted from export",
        "files": {},
    }
    try:
        with engine.connect().execution_options(
            isolation_level="REPEATABLE READ"
        ) as connection:
            for kind, query in QUERIES.items():
                path = output_dir / f"{kind}.csv"
                rows = connection.execute(text(query)).mappings()
                count = 0
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=FIELDS[kind])
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(sanitize(kind, dict(row), key))
                        count += 1
                with path.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                manifest["files"][path.name] = {"rows": count, "sha256": digest}
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return manifest
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only pseudonymous traffic export"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    database_url = os.environ.get("EXPORT_DATABASE_URL")
    secret = os.environ.get("EXPORT_PSEUDONYM_KEY")
    if not database_url or not secret:
        parser.error(
            "Set EXPORT_DATABASE_URL and EXPORT_PSEUDONYM_KEY in the process environment"
        )
    print(json.dumps(export(database_url, secret.encode(), args.output_dir), indent=2))


if __name__ == "__main__":
    main()
