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
    ReplayStartRequest,
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
from domain.exceptions import DomainValidationError, EntityNotFoundError

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


@router.get("/api/v1/datasets", tags=["demo-peru"])
def datasets(container: Container) -> list[dict[str, Any]]:
    return container.demo_query.list_datasets()


@router.get("/api/v1/datasets/{dataset_id}", tags=["demo-peru"])
def dataset_detail(dataset_id: str, container: Container) -> dict[str, Any]:
    dataset = container.demo_query.get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.get("/api/v1/demo/peru/locations", tags=["demo-peru"])
def peru_locations(
    container: Container,
    region: str | None = None,
) -> list[dict[str, Any]]:
    return container.demo_query.locations(region)


@router.get("/api/v1/demo/peru/traffic", tags=["demo-peru"])
def peru_traffic(
    container: Container,
    dataset_id: str = "mtc_peru_toll_flow",
    provider: str | None = None,
    region: str | None = None,
    location_id: str | None = None,
    start_period: str | None = None,
    end_period: str | None = None,
    vehicle_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> dict[str, Any]:
    dataset = container.demo_query.get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    if provider and provider.casefold() not in str(dataset["provider"]).casefold():
        return {"record_count": 0, "records": [], "message": "Provider filter did not match"}
    return container.demo_query.traffic(
        dataset_id,
        region=region,
        location_id=location_id,
        start_period=start_period,
        end_period=end_period,
        vehicle_category=vehicle_type,
        limit=limit,
    )


@router.get("/api/v1/demo/peru/junin", tags=["demo-peru"])
def peru_junin(container: Container) -> dict[str, Any]:
    return container.demo_query.junin()


@router.get("/api/v1/demo/peru/comparison", tags=["demo-peru"])
def peru_comparison(container: Container) -> dict[str, Any]:
    return container.demo_query.comparison()


@router.get("/api/v1/demo/peru/ml", tags=["demo-peru"])
def peru_ml_experiment(container: Container) -> dict[str, Any]:
    if container.demo_ml_metadata is None:
        raise HTTPException(status_code=404, detail="El experimento ML aún no fue ejecutado")
    return container.demo_ml_metadata


@router.post("/api/v1/demo/peru/replay/start", tags=["demo-peru"])
def start_peru_replay(payload: ReplayStartRequest, container: Container) -> dict[str, Any]:
    try:
        return container.demo_replay.start(
            payload.dataset_id,
            start_period=payload.start_period,
            end_period=payload.end_period,
            location_id=payload.location_id,
            speed_factor=payload.speed_factor,
            limit=payload.limit,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/api/v1/demo/peru/replay/pause", tags=["demo-peru"])
def pause_peru_replay(container: Container) -> dict[str, Any]:
    return container.demo_replay.pause()


@router.post("/api/v1/demo/peru/replay/continue", tags=["demo-peru"])
def continue_peru_replay(container: Container) -> dict[str, Any]:
    return container.demo_replay.resume()


@router.post("/api/v1/demo/peru/replay/stop", tags=["demo-peru"])
def stop_peru_replay(container: Container) -> dict[str, Any]:
    return container.demo_replay.stop()


@router.post("/api/v1/demo/peru/replay/reset", tags=["demo-peru"])
def reset_peru_replay(container: Container) -> dict[str, Any]:
    return container.demo_replay.reset()


@router.get("/api/v1/demo/peru/replay/status", tags=["demo-peru"])
def peru_replay_status(container: Container) -> dict[str, Any]:
    container.demo_replay.mark_api_served()
    return container.demo_replay.status()


@router.get("/api/v1/demo/peru/state", tags=["demo-peru"])
def peru_demo_state(container: Container) -> dict[str, Any]:
    container.demo_replay.mark_api_served()
    return container.demo_replay.status()


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
    except DomainValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


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


@router.get("/api/v1/scenarios", response_model=list[ScenarioResponse], tags=["scenarios"])
def list_scenarios(container: Container) -> list[Any]:
    return container.scenario_repository.list_scenarios()


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
