import json
from datetime import UTC, datetime
from uuid import uuid4

from adapters.inbound.mqtt import TrafficMqttConsumer
from domain.entities import TrafficMeasurement


class RegistrationSpy:
    def __init__(self) -> None:
        self.received: TrafficMeasurement | None = None

    def execute(self, measurement: TrafficMeasurement) -> TrafficMeasurement:
        self.received = measurement
        return measurement


def test_consumer_validates_and_maps_payload() -> None:
    spy = RegistrationSpy()
    consumer = TrafficMqttConsumer(spy)
    payload = {
        "source_id": str(uuid4()),
        "road_segment_id": str(uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "traffic_volume": 7,
    }
    result = consumer.process_payload(json.dumps(payload).encode())
    assert result.traffic_volume == 7
    assert spy.received is result
