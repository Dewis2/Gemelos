import csv
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ml.src.preprocessing.local_huancayo import validate_local_counts
from scripts.export_evidence import sanitize


def test_local_counts_reject_unobserved_and_duplicate_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "local.csv"
    segment = uuid4()
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "timestamp",
                "road_segment_id",
                "traffic_volume",
                "source_name",
                "source_reference",
                "measurement_method",
                "license",
            ],
        )
        writer.writeheader()
        row = {
            "timestamp": "2026-10-01T08:00:00-05:00",
            "road_segment_id": str(segment),
            "traffic_volume": "10",
            "source_name": "Prueba",
            "source_reference": "fixture",
            "measurement_method": "conteo",
            "license": "uso de prueba",
        }
        writer.writerow(row)
        writer.writerow(row)
        writer.writerow({**row, "timestamp": "2027-01-01T08:00:00-05:00"})
    report = validate_local_counts(csv_path, datetime(2026, 11, 13, tzinfo=UTC))
    assert not report["schema_quality_passed"]
    assert not report["temporal_evaluation_ready"]
    assert any("Duplicate" in error for error in report["errors"])
    assert any("2026" in error for error in report["errors"])
    assert report["field_provenance_verified"] is False


def test_export_pseudonymizes_identifiers() -> None:
    record = uuid4()
    source = uuid4()
    segment = uuid4()
    row = sanitize(
        "measurements",
        {
            "id": record,
            "source_id": source,
            "source_name": "Prueba",
            "road_segment_id": segment,
            "timestamp": datetime(2026, 10, 1, 13, tzinfo=UTC),
            "traffic_volume": 10,
            "average_speed": 20.0,
            "occupancy": 0.2,
        },
        b"a" * 32,
    )
    assert str(record) not in str(row)
    assert str(source) not in str(row)
    assert str(segment) not in str(row)
    assert row["timestamp_utc"] == "2026-10-01T13:00:00+00:00"
