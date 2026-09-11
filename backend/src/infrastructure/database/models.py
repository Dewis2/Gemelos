from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

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
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    geometry: Mapped[Any | None] = mapped_column(Geometry("POINT", srid=4326), nullable=True)

    def to_domain(self) -> Intersection:
        return Intersection(
            id=self.id,
            name=self.name,
            geometry=str(self.geometry) if self.geometry is not None else None,
        )


class RoadSegmentModel(Base):
    __tablename__ = "road_segments"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    start_intersection_id: Mapped[UUID] = mapped_column(ForeignKey("intersections.id"))
    end_intersection_id: Mapped[UUID] = mapped_column(ForeignKey("intersections.id"))
    lane_count: Mapped[int] = mapped_column(Integer)
    reference_speed: Mapped[float] = mapped_column(Float)
    geometry: Mapped[Any | None] = mapped_column(Geometry("LINESTRING", srid=4326), nullable=True)

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
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
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
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    intersection_id: Mapped[UUID] = mapped_column(ForeignKey("intersections.id"), index=True)
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
        Index("ix_simulation_results_scenario_segment", "scenario_id", "road_segment_id"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
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
