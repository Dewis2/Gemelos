from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from adapters.outbound.persistence import InMemoryStore
from adapters.outbound.sumo import FakeTrafficSimulator
from application.dto import PredictionRequest
from application.use_cases import (
    CompareSimulationScenarios,
    CreateSimulationScenario,
    PredictTrafficFlow,
    RegisterTrafficMeasurement,
    RunSimulationScenario,
)
from domain.entities import SimulationScenario
from tests.factories import make_measurement, make_network


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.events.append((topic, payload))


class ConstantModel:
    def predict_traffic(self, features: dict[str, float]) -> tuple[float, str]:
        assert features["hour"] == 8.0
        assert set(features) == {"day_of_week", "hour", "is_weekend", "month"}
        return 42.0, "test-model"


VALID_FEATURES = {"day_of_week": 0, "hour": 8, "is_weekend": 0, "month": 10}


def test_register_measurement_persists_and_publishes() -> None:
    store = InMemoryStore()
    publisher = RecordingPublisher()
    measurement = make_measurement()
    saved = RegisterTrafficMeasurement(store, publisher).execute(measurement)
    assert store.latest() == [saved]
    assert publisher.events[0][1]["measurement_id"] == str(measurement.id)


def test_predict_traffic_uses_port_and_saves_prediction() -> None:
    store = InMemoryStore()
    intersections, segment = make_network()
    store.intersections.extend(intersections)
    store.segments.append(segment)
    target = datetime.now(UTC) + timedelta(hours=1)
    request = PredictionRequest(segment.id, target, VALID_FEATURES)
    prediction = PredictTrafficFlow(ConstantModel(), store, store).execute(request)
    assert prediction.predicted_volume == 42.0
    assert prediction.model_version == "test-model"
    assert store.predictions == [prediction]


def test_run_and_compare_scenario_uses_simulator_observations() -> None:
    store = InMemoryStore()
    intersections, segment = make_network()
    store.intersections.extend(intersections)
    store.segments.append(segment)
    scenario = CreateSimulationScenario(store).execute(
        SimulationScenario("test", "unit test", {"steps": 2})
    )
    simulator = FakeTrafficSimulator(average_speed=12.5, queue_length=3.0)
    results = RunSimulationScenario(store, store, store, simulator).execute(scenario.id)
    comparison = CompareSimulationScenarios(store).execute([scenario.id])
    assert len(results) == 1
    assert results[0].average_speed == 12.5
    assert comparison[str(scenario.id)]["average_queue_length"] == 3.0
    assert simulator.started is False


def test_repository_returns_none_for_unknown_scenario() -> None:
    assert InMemoryStore().get(UUID(int=0)) is None
