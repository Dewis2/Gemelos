from datetime import UTC, datetime
from uuid import uuid4

from domain.entities import Intersection, RoadSegment, TrafficMeasurement


def make_measurement(traffic_volume: int = 10) -> TrafficMeasurement:
    return TrafficMeasurement(
        source_id=uuid4(),
        road_segment_id=uuid4(),
        timestamp=datetime.now(UTC),
        traffic_volume=traffic_volume,
        average_speed=20.0,
        occupancy=0.4,
    )


def make_network() -> tuple[list[Intersection], RoadSegment]:
    start = Intersection(name="Validated start")
    end = Intersection(name="Validated end")
    segment = RoadSegment(
        name="Test segment",
        start_intersection_id=start.id,
        end_intersection_id=end.id,
        lane_count=2,
        reference_speed=30.0,
    )
    return [start, end], segment
