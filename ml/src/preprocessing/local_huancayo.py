"""Quality gate for supplied 2026 Huancayo counts; never creates observations."""

import csv
import hashlib
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

REQUIRED = {
    "timestamp",
    "road_segment_id",
    "traffic_volume",
    "source_name",
    "source_reference",
    "measurement_method",
    "license",
}


def validate_local_counts(path: Path, now: datetime) -> dict[str, Any]:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    errors: list[str] = []
    records: list[tuple[UUID, datetime, int]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            errors.append("Missing columns: " + ", ".join(sorted(missing)))
        else:
            for number, row in enumerate(reader, start=2):
                try:
                    segment = UUID(row["road_segment_id"].strip())
                    moment = datetime.fromisoformat(row["timestamp"].strip())
                    volume = int(row["traffic_volume"].strip())
                    if moment.tzinfo is None or moment.utcoffset() is None:
                        raise ValueError("timestamp requires a timezone offset")
                    if moment.year != 2026 or moment > now:
                        raise ValueError("timestamp must be an observed date in 2026")
                    if volume < 0:
                        raise ValueError("traffic_volume must be non-negative")
                    if any(
                        not row[name].strip()
                        for name in REQUIRED
                        - {"timestamp", "road_segment_id", "traffic_volume"}
                    ):
                        raise ValueError("provenance fields cannot be empty")
                    records.append((segment, moment, volume))
                except (TypeError, ValueError, KeyError) as exc:
                    errors.append(f"Row {number}: {exc}")
    duplicates = [
        key
        for key, count in Counter((x[0], x[1]) for x in records).items()
        if count > 1
    ]
    if duplicates:
        errors.append(f"Duplicate segment/timestamp pairs: {len(duplicates)}")
    periods = sorted({moment.date() for _, moment, _ in records})
    segments = {segment for segment, _, _ in records}
    return {
        "dataset_sha256": digest,
        "rows_valid": len(records),
        "segment_count": len(segments),
        "distinct_days": len(periods),
        "first_date": periods[0].isoformat() if periods else None,
        "last_date": periods[-1].isoformat() if periods else None,
        "schema_quality_passed": not errors and bool(records),
        "temporal_evaluation_ready": not errors
        and len(records) >= 100
        and len(periods) >= 14,
        "field_provenance_verified": False,
        "errors": errors,
    }
