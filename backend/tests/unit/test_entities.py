from datetime import datetime
from uuid import uuid4

import pytest

from domain.entities import RoadSegment, TrafficMeasurement
from domain.exceptions import DomainValidationError


def test_road_segment_rejects_same_endpoint() -> None:
    intersection_id = uuid4()
    with pytest.raises(DomainValidationError, match="different intersections"):
        RoadSegment("invalid", intersection_id, intersection_id, 1, 30.0)


def test_measurement_requires_timezone() -> None:
    with pytest.raises(DomainValidationError, match="timezone"):
        TrafficMeasurement(uuid4(), uuid4(), datetime(2026, 1, 1), 5)


def test_measurement_rejects_invalid_occupancy() -> None:
    with pytest.raises(DomainValidationError, match="between 0 and 1"):
        TrafficMeasurement(
            uuid4(), uuid4(), datetime.now().astimezone(), 5, occupancy=1.1
        )
