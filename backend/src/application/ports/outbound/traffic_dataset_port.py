from collections.abc import Iterable, Sequence
from typing import Any, Protocol

from application.dto.peru_demo import DatasetMetadata, TrafficAggregate, TrafficLocation


class TrafficDatasetPort(Protocol):
    def get_metadata(self) -> DatasetMetadata: ...

    def get_available_periods(self) -> list[str]: ...

    def get_locations(self) -> Sequence[TrafficLocation | dict[str, Any]]: ...

    def stream_measurements(
        self,
        *,
        start_period: str | None = None,
        end_period: str | None = None,
        location_id: str | None = None,
        region: str | None = None,
        vehicle_category: str | None = None,
        limit: int | None = None,
    ) -> Iterable[TrafficAggregate]: ...

    def validate(self) -> dict[str, Any]: ...

    def get_source_name(self) -> str: ...


class TrafficAggregateRepositoryPort(Protocol):
    def upsert(self, measurement: TrafficAggregate) -> str: ...

    def list_by_scope(self, dataset_scope: str) -> list[TrafficAggregate]: ...

    def list_by_dataset(self, dataset_id: str) -> list[TrafficAggregate]: ...
