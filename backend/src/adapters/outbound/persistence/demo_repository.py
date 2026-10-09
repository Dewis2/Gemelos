from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from application.dto.peru_demo import DatasetScope, TrafficAggregate, TrafficLocation


class InMemoryTrafficAggregateRepository:
    def __init__(self) -> None:
        self._items: dict[str, TrafficAggregate] = {}

    def upsert(self, measurement: TrafficAggregate) -> str:
        existing = self._items.get(measurement.natural_key)
        if existing is None:
            self._items[measurement.natural_key] = measurement
            return "inserted"
        if existing == measurement:
            return "duplicate"
        self._items[measurement.natural_key] = measurement
        return "updated"

    def list_by_scope(self, dataset_scope: str) -> list[TrafficAggregate]:
        return [
            item
            for item in self._items.values()
            if item.dataset_scope == DatasetScope(dataset_scope)
        ]

    def list_by_dataset(self, dataset_id: str) -> list[TrafficAggregate]:
        return [item for item in self._items.values() if item.dataset_id == dataset_id]


class SqlAlchemyTrafficAggregateRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def upsert(self, measurement: TrafficAggregate) -> str:
        from sqlalchemy import select

        from infrastructure.database.models import TrafficAggregateModel

        with self._session_factory() as session:
            existing = session.scalar(
                select(TrafficAggregateModel).where(
                    TrafficAggregateModel.natural_key == measurement.natural_key
                )
            )
            if existing is None:
                session.add(TrafficAggregateModel.from_dto(measurement))
                session.commit()
                return "inserted"
            if existing.vehicle_count == measurement.vehicle_count:
                return "duplicate"
            existing.vehicle_count = measurement.vehicle_count
            existing.metadata_json = measurement.metadata
            session.commit()
            return "updated"

    def list_by_scope(self, dataset_scope: str) -> list[TrafficAggregate]:
        from sqlalchemy import select

        from infrastructure.database.models import TrafficAggregateModel

        with self._session_factory() as session:
            rows = session.scalars(
                select(TrafficAggregateModel).where(
                    TrafficAggregateModel.dataset_scope == dataset_scope
                )
            )
            return [row.to_dto() for row in rows]

    def list_by_dataset(self, dataset_id: str) -> list[TrafficAggregate]:
        from sqlalchemy import select

        from infrastructure.database.models import TrafficAggregateModel

        with self._session_factory() as session:
            rows = session.scalars(
                select(TrafficAggregateModel)
                .where(TrafficAggregateModel.dataset_id == dataset_id)
                .order_by(
                    TrafficAggregateModel.period_start,
                    TrafficAggregateModel.natural_key,
                )
            )
            return [row.to_dto() for row in rows]


class SqlAlchemyTrafficLocationRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def upsert(self, location: TrafficLocation) -> str:
        from geoalchemy2.elements import WKTElement
        from sqlalchemy import select

        from infrastructure.database.models import TrafficLocationModel

        if "CRS84" not in location.crs:
            raise ValueError(f"Unsupported source CRS: {location.crs}")
        with self._session_factory() as session:
            existing = session.scalar(
                select(TrafficLocationModel).where(
                    TrafficLocationModel.dataset_id == location.dataset_id,
                    TrafficLocationModel.source_location_id
                    == location.source_location_id,
                )
            )
            geometry = WKTElement(
                f"POINT({location.longitude} {location.latitude})", srid=4326
            )
            properties = {**location.properties, "source_crs": location.crs}
            if existing is None:
                session.add(
                    TrafficLocationModel(
                        dataset_id=location.dataset_id,
                        source_location_id=location.source_location_id,
                        name=location.name,
                        type=location.location_type,
                        operator=location.operator,
                        status=location.status,
                        geometry=geometry,
                        properties_json=properties,
                    )
                )
                session.commit()
                return "inserted"
            existing.name = location.name
            existing.type = location.location_type
            existing.operator = location.operator
            existing.status = location.status
            existing.geometry = geometry
            existing.properties_json = properties
            session.commit()
            return "updated"


class SqlAlchemyIngestionRunRecorder:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def start(self, dataset_id: str) -> UUID:
        from infrastructure.database.models import DatasetIngestionRunModel

        run_id = uuid4()
        with self._session_factory() as session:
            session.add(
                DatasetIngestionRunModel(
                    id=run_id,
                    dataset_id=dataset_id,
                    started_at=datetime.now(UTC),
                    status="running",
                )
            )
            session.commit()
        return run_id

    def finish(
        self, run_id: UUID, counters: dict[str, int], *, status: str = "completed"
    ) -> None:
        from infrastructure.database.models import DatasetIngestionRunModel

        with self._session_factory() as session:
            row = session.get(DatasetIngestionRunModel, run_id)
            if row is None:
                raise RuntimeError(f"Ingestion run not found: {run_id}")
            row.finished_at = datetime.now(UTC)
            row.status = status
            row.files_processed = counters.get("files_processed", 1)
            row.rows_read = counters.get("rows_read", 0)
            row.rows_valid = counters.get("rows_valid", 0)
            row.rows_rejected = counters.get("rows_rejected", 0)
            row.rows_inserted = counters.get("rows_inserted", 0)
            row.rows_updated = counters.get("rows_updated", 0)
            row.duplicates = counters.get("duplicates", 0)
            session.commit()
