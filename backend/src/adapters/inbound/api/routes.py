from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.inbound.api.container import ApplicationContainer
from adapters.inbound.api.dependencies import get_container
from adapters.inbound.api.schemas import (
    DigitalTwinStateResponse,
    IntersectionResponse,
    PredictionCreate,
    PredictionResponse,
    RoadSegmentResponse,
    ScenarioCreate,
    ScenarioResponse,
    SimulationResultResponse,
    TrafficMeasurementCreate,
    TrafficMeasurementResponse,
)
from adapters.outbound.ml.joblib_model import ModelNotReadyError
from application.dto import PredictionRequest
from domain.entities import SimulationScenario, TrafficMeasurement
from domain.exceptions import EntityNotFoundError

Container = Annotated[ApplicationContainer, Depends(get_container)]
router = APIRouter()


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "stage": "prototype"}


@router.get(
    "/api/v1/road-segments",
    response_model=list[RoadSegmentResponse],
    tags=["road-network"],
)
def road_segments(container: Container) -> list[Any]:
    return container.get_network.execute()["road_segments"]


@router.get(
    "/api/v1/intersections",
    response_model=list[IntersectionResponse],
    tags=["road-network"],
)
def intersections(container: Container) -> list[Any]:
    return container.get_network.execute()["intersections"]


@router.post(
    "/api/v1/traffic-measurements",
    response_model=TrafficMeasurementResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["traffic"],
)
def register_traffic(payload: TrafficMeasurementCreate, container: Container) -> Any:
    measurement = TrafficMeasurement(**payload.model_dump())
    return container.register_measurement.execute(measurement)


@router.get(
    "/api/v1/digital-twin/state",
    response_model=DigitalTwinStateResponse,
    tags=["digital-twin"],
)
def digital_twin_state(container: Container) -> dict[str, Any]:
    return container.get_twin_state.execute()


@router.post(
    "/api/v1/predictions/traffic-flow",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["predictions"],
)
def predict_traffic(payload: PredictionCreate, container: Container) -> Any:
    request = PredictionRequest(**payload.model_dump())
    try:
        return container.predict_traffic.execute(request)
    except ModelNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post(
    "/api/v1/scenarios",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["scenarios"],
)
def create_scenario(payload: ScenarioCreate, container: Container) -> Any:
    return container.create_scenario.execute(SimulationScenario(**payload.model_dump()))


@router.get("/api/v1/scenarios/compare", tags=["simulations"])
def compare_scenarios(
    container: Container,
    scenario_ids: Annotated[list[UUID], Query(min_length=2)],
) -> dict[str, dict[str, float | int]]:
    return container.compare_scenarios.execute(scenario_ids)


@router.post(
    "/api/v1/scenarios/{scenario_id}/run",
    response_model=list[SimulationResultResponse],
    tags=["simulations"],
)
def run_scenario(scenario_id: UUID, container: Container) -> list[Any]:
    try:
        return container.run_scenario.execute(scenario_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/api/v1/scenarios/{scenario_id}/results",
    response_model=list[SimulationResultResponse],
    tags=["simulations"],
)
def scenario_results(scenario_id: UUID, container: Container) -> list[Any]:
    return container.get_simulation_results.execute(scenario_id)
