"""Pruebas de casos de uso de la capa Application con Fakes de los puertos de salida.

Ninguna de estas pruebas abre conexion a PostgreSQL, MQTT ni a ningun servicio externo:
todos los puertos de salida se satisfacen con dobles en memoria, por lo que se ejecutan
en milisegundos y aíslan la regla de negocio de la infraestructura.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from adapters.outbound.persistence import InMemoryStore
from adapters.outbound.sumo import FakeTrafficSimulator
from application.dto import PredictionRequest
from application.use_cases import (
    CreateSimulationScenario,
    PredictTrafficFlow,
    RegisterTrafficMeasurement,
    RunSimulationScenario,
)
from domain.entities import RoadSegment, SimulationScenario, TrafficMeasurement
from domain.exceptions import DomainValidationError, EntityNotFoundError
from tests.factories import make_network

VALID_FEATURES = {"day_of_week": 3, "hour": 8, "is_weekend": 0, "month": 10}


class FakeMachineLearningModel:
    """Stub del puerto `MachineLearningPort`. No carga joblib ni sklearn."""

    def __init__(self, volume: float = 1234.0, version: str = "fake-model") -> None:
        self.volume = volume
        self.version = version
        self.calls: list[dict[str, float]] = []

    def predict_traffic(self, features: dict[str, float]) -> tuple[float, str]:
        self.calls.append(features)
        return self.volume, self.version


class FailingMachineLearningModel:
    """Simula el adaptador real cuando el artefacto del modelo no esta disponible."""

    def predict_traffic(self, features: dict[str, float]) -> tuple[float, str]:
        raise RuntimeError("No trained model at /app/models/traffic_model.joblib")


class FakeEventPublisher:
    """Stub del puerto `EventPublisherPort`. No abre conexion MQTT."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.events.append((topic, payload))


def build_prediction_use_case(model: Any) -> tuple[PredictTrafficFlow, InMemoryStore, RoadSegment]:
    store = InMemoryStore()
    intersections, segment = make_network()
    store.intersections.extend(intersections)
    store.segments.append(segment)
    return PredictTrafficFlow(model, store, store), store, segment


def request_for(segment_id: UUID, features: dict[str, float]) -> PredictionRequest:
    return PredictionRequest(segment_id, datetime.now(UTC) + timedelta(hours=1), features)


# --- Caso de uso de prediccion: camino feliz con fakes -------------------------


def test_prediction_delegates_to_the_port_and_persists() -> None:
    model = FakeMachineLearningModel()
    use_case, store, segment = build_prediction_use_case(model)

    prediction = use_case.execute(request_for(segment.id, VALID_FEATURES))

    assert prediction.predicted_volume == 1234.0
    assert prediction.model_version == "fake-model"
    assert prediction.road_segment_id == segment.id
    assert store.predictions == [prediction]
    # El caso de uso entrega al puerto el vector ya normalizado.
    assert model.calls == [
        {"day_of_week": 3.0, "hour": 8.0, "is_weekend": 0.0, "month": 10.0}
    ]


def test_prediction_clamps_negative_volume_to_zero() -> None:
    use_case, _store, segment = build_prediction_use_case(FakeMachineLearningModel(volume=-50.0))
    prediction = use_case.execute(request_for(segment.id, VALID_FEATURES))
    assert prediction.predicted_volume == 0.0


# --- Reglas de negocio sobre el contrato del modelo ----------------------------


@pytest.mark.parametrize(
    ("features", "expected"),
    [
        ({}, "Faltan variables de entrada del modelo"),
        ({"hour": 8}, "Faltan variables de entrada del modelo"),
        ({**VALID_FEATURES, "traffic_volume": 900}, "Variables no esperadas por el modelo"),
        ({**VALID_FEATURES, "hour": 99}, "hour debe estar entre 0 y 23"),
        ({**VALID_FEATURES, "day_of_week": 9}, "day_of_week debe estar entre 0 y 6"),
        ({**VALID_FEATURES, "month": 13}, "month debe estar entre 1 y 12"),
        ({**VALID_FEATURES, "is_weekend": 1}, "is_weekend no coincide con day_of_week"),
        ({**VALID_FEATURES, "hour": 8.5}, "hour debe ser un numero entero"),
        ({**VALID_FEATURES, "month": "octubre"}, "month debe ser numerica"),
    ],
)
def test_invalid_features_are_rejected_before_calling_the_model(
    features: dict[str, float], expected: str
) -> None:
    model = FakeMachineLearningModel()
    use_case, store, segment = build_prediction_use_case(model)

    with pytest.raises(DomainValidationError) as error:
        use_case.execute(request_for(segment.id, features))

    assert expected in str(error.value)
    # La regla se aplica ANTES de la inferencia: no se persiste nada.
    assert model.calls == []
    assert store.predictions == []


def test_prediction_rejects_unknown_road_segment() -> None:
    use_case, store, _segment = build_prediction_use_case(FakeMachineLearningModel())

    with pytest.raises(EntityNotFoundError) as error:
        use_case.execute(request_for(uuid4(), VALID_FEATURES))

    assert "no está registrado en la red del corredor" in str(error.value)
    assert store.predictions == []


def test_prediction_failure_does_not_persist_a_partial_result() -> None:
    use_case, store, segment = build_prediction_use_case(FailingMachineLearningModel())

    with pytest.raises(RuntimeError):
        use_case.execute(request_for(segment.id, VALID_FEATURES))

    assert store.predictions == []


# --- Persistencia / Repository --------------------------------------------------


def test_register_measurement_persists_through_the_repository_port() -> None:
    store = InMemoryStore()
    publisher = FakeEventPublisher()
    segment_id = uuid4()
    measurement = TrafficMeasurement(
        source_id=uuid4(),
        road_segment_id=segment_id,
        timestamp=datetime.now(UTC),
        traffic_volume=812,
        average_speed=21.5,
    )

    saved = RegisterTrafficMeasurement(store, publisher).execute(measurement)

    assert saved.id == measurement.id
    assert store.latest() == [saved]
    assert store.latest()[0].road_segment_id == segment_id
    assert store.latest()[0].traffic_volume == 812
    assert publisher.events and publisher.events[0][1]["measurement_id"] == str(measurement.id)


def test_repository_returns_latest_measurements_in_reverse_chronology() -> None:
    store = InMemoryStore()
    base = datetime.now(UTC)
    older = TrafficMeasurement(
        source_id=uuid4(), road_segment_id=uuid4(), timestamp=base, traffic_volume=10
    )
    newer = TrafficMeasurement(
        source_id=uuid4(), road_segment_id=uuid4(), timestamp=base + timedelta(hours=1),
        traffic_volume=20,
    )
    RegisterTrafficMeasurement(store, FakeEventPublisher()).execute(older)
    RegisterTrafficMeasurement(store, FakeEventPublisher()).execute(newer)

    assert [item.traffic_volume for item in store.latest()] == [20, 10]


def test_repository_returns_none_for_unknown_scenario() -> None:
    assert InMemoryStore().get(UUID(int=0)) is None


# --- Regla de negocio del dominio ------------------------------------------------


def test_domain_rejects_invalid_measurement_state() -> None:
    with pytest.raises(DomainValidationError):
        TrafficMeasurement(
            source_id=uuid4(),
            road_segment_id=uuid4(),
            timestamp=datetime.now(UTC),
            traffic_volume=-1,
        )
    with pytest.raises(DomainValidationError):
        TrafficMeasurement(
            source_id=uuid4(),
            road_segment_id=uuid4(),
            timestamp=datetime.now(UTC).replace(tzinfo=None),
            traffic_volume=10,
        )


# --- Simulacion con el adaptador de prueba, sin SUMO ni servicios ----------------


def test_scenario_run_persists_one_row_per_segment() -> None:
    store = InMemoryStore()
    intersections, segment = make_network()
    store.intersections.extend(intersections)
    store.segments.append(segment)
    scenario = CreateSimulationScenario(store).execute(
        SimulationScenario("unit", "sin metricas fisicas", {"steps": 5})
    )

    use_case = RunSimulationScenario(store, store, store, FakeTrafficSimulator())
    results = use_case.execute(scenario.id)

    assert len(results) == 1
    assert results[0].road_segment_id == segment.id
    assert store.by_scenario(scenario.id) == results


# --- Factory Method ---------------------------------------------------------------


def test_factory_returns_memory_repository_by_default() -> None:
    from adapters.outbound.persistence import build_traffic_aggregate_repository

    repository = build_traffic_aggregate_repository()
    assert repository.__class__.__name__ == "InMemoryTrafficAggregateRepository"
    assert build_traffic_aggregate_repository("memory").__class__.__name__ == (
        "InMemoryTrafficAggregateRepository"
    )


def test_factory_rejects_unknown_persistence() -> None:
    from adapters.outbound.persistence import build_traffic_aggregate_repository

    with pytest.raises(ValueError, match="Persistencia no soportada"):
        build_traffic_aggregate_repository("mongodb")