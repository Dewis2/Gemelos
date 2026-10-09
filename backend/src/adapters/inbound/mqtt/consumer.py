import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from application.ports.inbound import MeasurementRegistration
from domain.entities import TrafficMeasurement


class TrafficMqttConsumer:
    topic = "huancayo/ferrocarril/traffic/measurements"

    def __init__(self, register_measurement: MeasurementRegistration) -> None:
        self._register = register_measurement
        self._logger = logging.getLogger(__name__)

    def process_payload(self, raw_payload: bytes) -> TrafficMeasurement:
        try:
            payload: dict[str, Any] = json.loads(raw_payload.decode("utf-8"))
            measurement = TrafficMeasurement(
                source_id=UUID(payload["source_id"]),
                road_segment_id=UUID(payload["road_segment_id"]),
                timestamp=datetime.fromisoformat(payload["timestamp"]),
                traffic_volume=int(payload["traffic_volume"]),
                average_speed=(
                    float(payload["average_speed"])
                    if payload.get("average_speed") is not None
                    else None
                ),
                occupancy=(
                    float(payload["occupancy"])
                    if payload.get("occupancy") is not None
                    else None
                ),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._logger.warning("Rejected invalid MQTT traffic payload: %s", exc)
            raise ValueError("Invalid traffic measurement payload") from exc
        return self._register.execute(measurement)
