from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IntersectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    geometry: str | None


class RoadSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    start_intersection_id: UUID
    end_intersection_id: UUID
    lane_count: int
    reference_speed: float
    geometry: str | None


class TrafficMeasurementCreate(BaseModel):
    source_id: UUID
    road_segment_id: UUID
    timestamp: datetime
    traffic_volume: int = Field(ge=0)
    average_speed: float | None = Field(default=None, ge=0)
    occupancy: float | None = Field(default=None, ge=0, le=1)


class TrafficMeasurementResponse(TrafficMeasurementCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class PredictionCreate(BaseModel):
    road_segment_id: UUID
    target_timestamp: datetime
    features: dict[str, float]


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    road_segment_id: UUID
    prediction_timestamp: datetime
    target_timestamp: datetime
    predicted_volume: float
    model_version: str


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=1000)
    configuration: dict[str, Any] = Field(default_factory=dict)


class ScenarioResponse(ScenarioCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime


class SimulationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    scenario_id: UUID
    road_segment_id: UUID
    travel_time: float
    average_speed: float
    delay: float
    queue_length: float
    emissions: dict[str, float]
    created_at: datetime


class DigitalTwinStateResponse(BaseModel):
    status: str
    corridor: str
    road_segment_count: int
    intersection_count: int
    latest_measurements: list[TrafficMeasurementResponse]
    geometry_status: str
