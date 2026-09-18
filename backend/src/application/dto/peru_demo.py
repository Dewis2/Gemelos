from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class DemoMode(StrEnum):
    PERU_OFFICIAL_DATA = "peru_official_data"


class DatasetScope(StrEnum):
    PERU_OFFICIAL_DEMO = "peru_official_demo"
    HUANCAYO_LOCAL_HISTORICAL = "huancayo_local_historical"
    HUANCAYO_LOCAL_CURRENT = "huancayo_local_current"


@dataclass(frozen=True, slots=True)
class DatasetMetadata:
    dataset_id: str
    title: str
    provider: str
    country: str
    source_type: str
    temporal_granularity: str
    spatial_granularity: str
    period_min: str | None
    period_max: str | None
    license: str
    source_page: str
    local_validation: bool
    allowed_uses: dict[str, bool]
    limitations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TrafficAggregate:
    dataset_id: str
    source_record_id: str
    source_provider: str
    source_country: str
    source_region: str | None
    source_location_id: str
    source_location_name: str
    period_start: str
    period_end: str
    temporal_granularity: str
    vehicle_category: str
    vehicle_count: int
    dataset_scope: DatasetScope
    metadata: dict[str, Any] = field(default_factory=dict)
    ingestion_run_id: str | None = None

    @property
    def natural_key(self) -> str:
        return "|".join(
            (
                self.dataset_id,
                self.source_record_id,
                self.source_location_id,
                self.period_start,
                self.vehicle_category,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["dataset_scope"] = self.dataset_scope.value
        return result


@dataclass(frozen=True, slots=True)
class TrafficLocation:
    dataset_id: str
    source_location_id: str
    name: str
    location_type: str
    operator: str | None
    status: str | None
    region: str | None
    province: str | None
    district: str | None
    longitude: float
    latitude: float
    crs: str
    properties: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DigitalTwinDemoState:
    mode: DemoMode = DemoMode.PERU_OFFICIAL_DATA
    status: str = "idle"
    current_dataset: str | None = None
    current_location: str | None = None
    current_historical_period: str | None = None
    vehicle_count: int | None = None
    vehicle_categories: dict[str, int] = field(default_factory=dict)
    last_update: str | None = None
    source_provider: str | None = None
    replay_speed: int | None = None
    replay_position: int = 0
    replay_total: int = 0
    technical_status: dict[str, str] = field(default_factory=dict)
    events: list[dict[str, str]] = field(default_factory=list)

    def add_event(self, stage: str, message: str) -> None:
        self.events.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "stage": stage,
                "message": message,
            }
        )
        self.events = self.events[-50:]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["mode"] = self.mode.value
        return result
