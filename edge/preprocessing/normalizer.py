from datetime import datetime, timezone
from typing import Any
from uuid import UUID


def normalize_measurement(payload: dict[str, Any]) -> dict[str, Any]:
    source_id = str(UUID(str(payload["source_id"])))
    segment_id = str(UUID(str(payload["road_segment_id"])))
    volume = int(payload["traffic_volume"])
    if volume < 0:
        raise ValueError("traffic_volume cannot be negative")
    timestamp_value = payload.get("timestamp")
    timestamp = (
        datetime.fromisoformat(str(timestamp_value))
        if timestamp_value
        else datetime.now(timezone.utc)
    )
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return {
        "source_id": source_id,
        "road_segment_id": segment_id,
        "timestamp": timestamp.astimezone(timezone.utc).isoformat(),
        "traffic_volume": volume,
        "average_speed": payload.get("average_speed"),
        "occupancy": payload.get("occupancy"),
    }
