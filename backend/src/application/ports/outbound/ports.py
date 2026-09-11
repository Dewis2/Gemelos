from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from domain.entities import (
    Intersection,
    RoadSegment,
    SimulationResult,
    SimulationScenario,
    TrafficMeasurement,
    TrafficPrediction,
)


class TrafficRepository(Protocol):
    def add(self, measurement: TrafficMeasurement) -> TrafficMeasurement: ...

    def latest(self) -> list[TrafficMeasurement]: ...


class RoadNetworkRepository(Protocol):
    def list_segments(self) -> list[RoadSegment]: ...

    def list_intersections(self) -> list[Intersection]: ...


class PredictionRepository(Protocol):
    def add(self, prediction: TrafficPrediction) -> TrafficPrediction: ...


class ScenarioRepository(Protocol):
    def add(self, scenario: SimulationScenario) -> SimulationScenario: ...

    def get(self, scenario_id: UUID) -> SimulationScenario | None: ...

    def list_scenarios(self) -> list[SimulationScenario]: ...


class SimulationRepository(Protocol):
    def add_all(self, results: list[SimulationResult]) -> list[SimulationResult]: ...

    def by_scenario(self, scenario_id: UUID) -> list[SimulationResult]: ...


class MachineLearningPort(Protocol):
    def predict_traffic(self, features: dict[str, float]) -> tuple[float, str]: ...


class TrafficSimulatorPort(Protocol):
    def start_simulation(self) -> None: ...

    def stop_simulation(self) -> None: ...

    def load_scenario(self, scenario: SimulationScenario) -> None: ...

    def set_traffic_demand(self, demand: dict[str, Any]) -> None: ...

    def get_vehicle_count(self) -> int: ...

    def get_average_speed(self) -> float: ...

    def get_queue_length(self) -> float: ...

    def run_steps(self, steps: int) -> None: ...


class EventPublisherPort(Protocol):
    def publish(self, topic: str, payload: dict[str, Any]) -> None: ...


class ClockPort(Protocol):
    def now(self) -> datetime: ...
