from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from domain.exceptions import DomainValidationError


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Intersection:
    name: str
    id: UUID = field(default_factory=uuid4)
    geometry: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainValidationError("Intersection name cannot be empty")


@dataclass(slots=True)
class RoadSegment:
    name: str
    start_intersection_id: UUID
    end_intersection_id: UUID
    lane_count: int
    reference_speed: float
    id: UUID = field(default_factory=uuid4)
    geometry: str | None = None

    def __post_init__(self) -> None:
        if self.start_intersection_id == self.end_intersection_id:
            raise DomainValidationError(
                "A road segment needs two different intersections"
            )
        if self.lane_count < 1:
            raise DomainValidationError("lane_count must be at least 1")
        if self.reference_speed <= 0:
            raise DomainValidationError("reference_speed must be positive")


@dataclass(slots=True)
class DataSource:
    name: str
    source_type: str
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    active: bool = True


@dataclass(slots=True)
class TrafficMeasurement:
    source_id: UUID
    road_segment_id: UUID
    timestamp: datetime
    traffic_volume: int
    average_speed: float | None = None
    occupancy: float | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise DomainValidationError("timestamp must include timezone information")
        if self.traffic_volume < 0:
            raise DomainValidationError("traffic_volume cannot be negative")
        if self.average_speed is not None and self.average_speed < 0:
            raise DomainValidationError("average_speed cannot be negative")
        if self.occupancy is not None and not 0 <= self.occupancy <= 1:
            raise DomainValidationError("occupancy must be between 0 and 1")


@dataclass(slots=True)
class TrafficSignalPlan:
    intersection_id: UUID
    name: str
    phases: list[dict[str, Any]]
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class TrafficPrediction:
    road_segment_id: UUID
    prediction_timestamp: datetime
    target_timestamp: datetime
    predicted_volume: float
    model_version: str
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class SimulationScenario:
    name: str
    description: str
    configuration: dict[str, Any]
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class SimulationResult:
    scenario_id: UUID
    road_segment_id: UUID
    travel_time: float
    average_speed: float
    delay: float
    queue_length: float
    emissions: dict[str, float]
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
