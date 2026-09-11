from typing import Any, Protocol
from uuid import UUID

from application.dto.models import PredictionRequest
from domain.entities import SimulationScenario, TrafficMeasurement, TrafficPrediction


class MeasurementRegistration(Protocol):
    def execute(self, measurement: TrafficMeasurement) -> TrafficMeasurement: ...


class DigitalTwinQuery(Protocol):
    def execute(self) -> dict[str, Any]: ...


class PredictionCommand(Protocol):
    def execute(self, request: PredictionRequest) -> TrafficPrediction: ...


class ScenarioCommand(Protocol):
    def create(self, scenario: SimulationScenario) -> SimulationScenario: ...

    def run(self, scenario_id: UUID) -> list[Any]: ...
