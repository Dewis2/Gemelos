from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from application.dto.peru_demo import DatasetScope, TrafficAggregate
from domain.entities import (
    Intersection,
    RoadSegment,
    SimulationResult,
    SimulationScenario,
    TrafficMeasurement,
    TrafficPrediction,
)
from infrastructure.database.base import Base


class IntersectionModel(Base):
    __tablename__ = "intersections"
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    geometry: Mapped[Any | None] = mapped_column(
        Geometry("POINT", srid=4326), nullable=True
    )

    def to_domain(self) -> Intersection:
        return Intersection(
            id=self.id,
            name=self.name,
            geometry=str(self.geometry) if self.geometry is not None else None,
        )


class RoadSegmentModel(Base):
    __tablename__ = "road_segments"
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    start_intersection_id: Mapped[UUID] = mapped_column(ForeignKey("intersections.id"))
    end_intersection_id: Mapped[UUID] = mapped_column(ForeignKey("intersections.id"))
    lane_count: Mapped[int] = mapped_column(Integer)
    reference_speed: Mapped[float] = mapped_column(Float)
    geometry: Mapped[Any | None] = mapped_column(
        Geometry("LINESTRING", srid=4326), nullable=True
    )

    def to_domain(self) -> RoadSegment:
        return RoadSegment(
            id=self.id,
            name=self.name,
            start_intersection_id=self.start_intersection_id,
            end_intersection_id=self.end_intersection_id,
            lane_count=self.lane_count,
            reference_speed=self.reference_speed,
            geometry=str(self.geometry) if self.geometry is not None else None,
        )


class DataSourceModel(Base):
    __tablename__ = "data_sources"
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TrafficMeasurementModel(Base):
    __tablename__ = "traffic_measurements"
    __table_args__ = (
        Index("ix_traffic_measurements_timestamp", "timestamp"),
        Index("ix_traffic_measurements_road_segment_id", "road_segment_id"),
        Index("ix_traffic_measurements_source_id", "source_id"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("data_sources.id"))
    road_segment_id: Mapped[UUID] = mapped_column(ForeignKey("road_segments.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    traffic_volume: Mapped[int] = mapped_column(Integer)
    average_speed: Mapped[float | None] = mapped_column(Float)
    occupancy: Mapped[float | None] = mapped_column(Float)

    @classmethod
    def from_domain(cls, item: TrafficMeasurement) -> "TrafficMeasurementModel":
        return cls(**{name: getattr(item, name) for name in item.__dataclass_fields__})

    def to_domain(self) -> TrafficMeasurement:
        return TrafficMeasurement(
            id=self.id,
            source_id=self.source_id,
            road_segment_id=self.road_segment_id,
            timestamp=self.timestamp,
            traffic_volume=self.traffic_volume,
            average_speed=self.average_speed,
            occupancy=self.occupancy,
        )


class TrafficSignalPlanModel(Base):
    __tablename__ = "traffic_signal_plans"
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    intersection_id: Mapped[UUID] = mapped_column(
        ForeignKey("intersections.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    phases: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)


class TrafficPredictionModel(Base):
    __tablename__ = "traffic_predictions"
    __table_args__ = (
        Index("ix_traffic_predictions_target_timestamp", "target_timestamp"),
        Index("ix_traffic_predictions_road_segment_id", "road_segment_id"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    road_segment_id: Mapped[UUID] = mapped_column(ForeignKey("road_segments.id"))
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    target_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    predicted_volume: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(100))

    @classmethod
    def from_domain(cls, item: TrafficPrediction) -> "TrafficPredictionModel":
        return cls(**{name: getattr(item, name) for name in item.__dataclass_fields__})


class SimulationScenarioModel(Base):
    __tablename__ = "simulation_scenarios"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(String(1000))
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    @classmethod
    def from_domain(cls, item: SimulationScenario) -> "SimulationScenarioModel":
        return cls(**{name: getattr(item, name) for name in item.__dataclass_fields__})

    def to_domain(self) -> SimulationScenario:
        return SimulationScenario(
            id=self.id,
            name=self.name,
            description=self.description,
            configuration=self.configuration,
            created_at=self.created_at,
        )


class SimulationResultModel(Base):
    __tablename__ = "simulation_results"
    __table_args__ = (
        Index(
            "ix_simulation_results_scenario_segment", "scenario_id", "road_segment_id"
        ),
    )
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("simulation_scenarios.id"))
    road_segment_id: Mapped[UUID] = mapped_column(ForeignKey("road_segments.id"))
    travel_time: Mapped[float] = mapped_column(Float)
    average_speed: Mapped[float] = mapped_column(Float)
    delay: Mapped[float] = mapped_column(Float)
    queue_length: Mapped[float] = mapped_column(Float)
    emissions: Mapped[dict[str, float]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    @classmethod
    def from_domain(cls, item: SimulationResult) -> "SimulationResultModel":
        return cls(**{name: getattr(item, name) for name in item.__dataclass_fields__})

    def to_domain(self) -> SimulationResult:
        return SimulationResult(
            id=self.id,
            scenario_id=self.scenario_id,
            road_segment_id=self.road_segment_id,
            travel_time=self.travel_time,
            average_speed=self.average_speed,
            delay=self.delay,
            queue_length=self.queue_length,
            emissions=self.emissions,
            created_at=self.created_at,
        )


class TrafficAggregateModel(Base):
    __tablename__ = "traffic_aggregates"
    __table_args__ = (
        Index("ix_traffic_aggregates_dataset_period", "dataset_id", "period_start"),
        Index("ix_traffic_aggregates_location", "source_location_id"),
    )
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    natural_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_provider: Mapped[str] = mapped_column(String(200), nullable=False)
    source_country: Mapped[str] = mapped_column(String(80), nullable=False)
    source_region: Mapped[str | None] = mapped_column(String(100))
    source_location_id: Mapped[str] = mapped_column(String(120), nullable=False)
    source_location_name: Mapped[str] = mapped_column(String(200), nullable=False)
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    temporal_granularity: Mapped[str] = mapped_column(String(40), nullable=False)
    vehicle_category: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dataset_scope: Mapped[str] = mapped_column(String(80), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    ingestion_run_id: Mapped[str | None] = mapped_column(String(80))

    @classmethod
    def from_dto(cls, item: TrafficAggregate) -> "TrafficAggregateModel":
        return cls(
            natural_key=item.natural_key,
            dataset_id=item.dataset_id,
            source_record_id=item.source_record_id,
            source_provider=item.source_provider,
            source_country=item.source_country,
            source_region=item.source_region,
            source_location_id=item.source_location_id,
            source_location_name=item.source_location_name,
            period_start=datetime.fromisoformat(item.period_start),
            period_end=datetime.fromisoformat(item.period_end),
            temporal_granularity=item.temporal_granularity,
            vehicle_category=item.vehicle_category,
            vehicle_count=item.vehicle_count,
            dataset_scope=item.dataset_scope.value,
            metadata_json=item.metadata,
            ingestion_run_id=item.ingestion_run_id,
        )

    def to_dto(self) -> TrafficAggregate:
        return TrafficAggregate(
            dataset_id=self.dataset_id,
            source_record_id=self.source_record_id,
            source_provider=self.source_provider,
            source_country=self.source_country,
            source_region=self.source_region,
            source_location_id=self.source_location_id,
            source_location_name=self.source_location_name,
            period_start=self.period_start.isoformat(),
            period_end=self.period_end.isoformat(),
            temporal_granularity=self.temporal_granularity,
            vehicle_category=self.vehicle_category,
            vehicle_count=self.vehicle_count,
            dataset_scope=DatasetScope(self.dataset_scope),
            metadata=self.metadata_json,
            ingestion_run_id=self.ingestion_run_id,
        )


class TrafficLocationModel(Base):
    __tablename__ = "traffic_locations"
    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "source_location_id",
            name="uq_traffic_locations_dataset_source",
        ),
    )
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    dataset_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_location_id: Mapped[str] = mapped_column(
        String(120), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    operator: Mapped[str | None] = mapped_column(String(250))
    status: Mapped[str | None] = mapped_column(String(100))
    geometry: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    properties_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class DatasetIngestionRunModel(Base):
    __tablename__ = "dataset_ingestion_runs"
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    dataset_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    files_processed: Mapped[int] = mapped_column(Integer, default=0)
    rows_read: Mapped[int] = mapped_column(Integer, default=0)
    rows_valid: Mapped[int] = mapped_column(Integer, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)
    rows_inserted: Mapped[int] = mapped_column(Integer, default=0)
    rows_updated: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
