"""Pruebas del patron Strategy para la politica de ambito de los datos de trafico.

Demuestran los cuatro elementos exigidos: abstraccion, dos estrategias concretas, un
contexto que selecciona y un intercambio verificable. No usan PostgreSQL ni MQTT.
"""

from __future__ import annotations

import pytest

from adapters.outbound.datasets import HuancayoHistoricalAdapter
from application.dto.peru_demo import (
    DatasetMetadata,
    DatasetScope,
    TrafficAggregate,
    TrafficLocation,
)
from application.services import PeruDemoQueryService
from application.services.traffic_scope import (
    LocalHistoricalScope,
    NationalDemoScope,
    TrafficScopeResolver,
    TrafficScopeStrategy,
    default_scope_strategies,
)

LOCAL_DATASET = "huancayo_historical_counts_2013"
LOCAL_WARNING = "Aforos históricos municipales. No representan tráfico actual de 2026."
NATIONAL_WARNING = (
    "Demostración con datos históricos oficiales. No representa "
    "tiempo real ni tráfico urbano de la Av. Ferrocarril."
)


class FakeDataset:
    """Doble del puerto de salida: no lee archivos ni toca el disco."""

    def __init__(self, dataset_id: str, provider: str) -> None:
        self.dataset_id = dataset_id
        self.provider = provider
        self.regions: list[str | None] = []

    def get_metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            dataset_id=self.dataset_id,
            title=f"conjunto {self.dataset_id}",
            provider=self.provider,
            country="Peru",
            source_type="fake",
            temporal_granularity="day_period",
            spatial_granularity="count_point",
            period_min="2013",
            period_max="2013",
            license="NO DETERMINADO",
            source_page="",
            local_validation=False,
            allowed_uses={},
            limitations=[],
        )

    def get_source_name(self) -> str:
        return self.provider

    def stream_measurements(self, **kwargs):  # noqa: ANN003, ANN201 - stub minimo
        self.regions.append(kwargs.get("region"))
        yield TrafficAggregate(
            dataset_id=self.dataset_id,
            source_record_id="r1",
            source_provider=self.provider,
            source_country="Peru",
            source_region="Junín",
            source_location_id="P04",
            source_location_name="P04",
            period_start="2013-01-01",
            period_end="2013-12-31",
            temporal_granularity="day_period",
            vehicle_category="all_vehicles",
            vehicle_count=1593,
            dataset_scope=DatasetScope.HUANCAYO_LOCAL_HISTORICAL,
        )

    def get_locations(self) -> list[TrafficLocation]:  # noqa: ANN201
        return []


def build_service(scopes: TrafficScopeResolver | None = None) -> PeruDemoQueryService:
    local = FakeDataset(LOCAL_DATASET, "Municipalidad Provincial de Huancayo")
    national = FakeDataset("mtc_peru_toll_flow", "MTC")
    datasets = {local.dataset_id: local, national.dataset_id: national}
    return PeruDemoQueryService(datasets, national, scopes=scopes)  # type: ignore[arg-type]


# --- 1. Abstraccion -------------------------------------------------------------


def test_concrete_strategies_satisfy_the_strategy_protocol() -> None:
    for strategy in default_scope_strategies():
        assert isinstance(strategy, TrafficScopeStrategy)


# --- 2. Dos estrategias concretas ------------------------------------------------


def test_default_resolver_selects_the_local_strategy_for_huancayo() -> None:
    resolved = TrafficScopeResolver().resolve(LOCAL_DATASET)
    assert resolved.key == "local_historical"
    assert resolved.warning() == LOCAL_WARNING


def test_default_resolver_selects_the_national_strategy_for_peajes() -> None:
    resolved = TrafficScopeResolver().resolve("mtc_peru_toll_flow")
    assert resolved.key == "national_demo"
    assert resolved.warning() == NATIONAL_WARNING


# --- 3. El contexto selecciona y la estrategia se intercambia --------------------


def test_registering_a_new_strategy_changes_the_selection_at_runtime() -> None:
    resolver = TrafficScopeResolver()

    class CorredorUnicoScope:
        key = "corredor_unico"

        def admits(self, dataset_id: str) -> bool:
            return True

        def warning(self) -> str:
            return "Aviso de la estrategia de corredor."

    assert resolver.resolve(LOCAL_DATASET).key == "local_historical"
    resolver.register(CorredorUnicoScope(), first=True)
    # Misma peticion, distinta estrategia seleccionada.
    assert resolver.resolve(LOCAL_DATASET).key == "corredor_unico"
    assert resolver.resolve(LOCAL_DATASET).warning() == "Aviso de la estrategia de corredor."


def test_resolver_without_local_strategy_falls_back_to_the_national_one() -> None:
    resolver = TrafficScopeResolver([NationalDemoScope()])
    assert resolver.resolve(LOCAL_DATASET).key == "national_demo"


def test_strategy_order_is_first_match_wins() -> None:
    resolver = TrafficScopeResolver([LocalHistoricalScope(), NationalDemoScope()])
    assert [strategy.key for strategy in resolver.strategies] == [
        "local_historical",
        "national_demo",
    ]
    assert resolver.resolve(LOCAL_DATASET).key == "local_historical"


def test_resolver_without_matching_strategy_fails_explicitly() -> None:
    class RechazaTodo:
        key = "rechaza"

        def admits(self, dataset_id: str) -> bool:
            return False

        def warning(self) -> str:
            return ""

    with pytest.raises(LookupError, match="No hay ninguna estrategia"):
        TrafficScopeResolver([RechazaTodo()]).resolve(LOCAL_DATASET)


# --- 4. El intercambio se propaga al servicio real ------------------------------


def test_service_uses_the_local_strategy_warning() -> None:
    service = build_service()
    payload = service.traffic(LOCAL_DATASET)
    assert payload["warning"] == LOCAL_WARNING
    assert payload["total_vehicles"] == 1593


def test_service_warning_changes_when_the_strategy_is_swapped() -> None:
    swapped = TrafficScopeResolver()

    class AvisoAlternativo:
        key = "alternativo"

        def admits(self, dataset_id: str) -> bool:
            return True

        def warning(self) -> str:
            return "Aviso inyectado para la demostracion."

    swapped.register(AvisoAlternativo(), first=True)
    payload = build_service(swapped).traffic(LOCAL_DATASET)

    assert payload["warning"] == "Aviso inyectado para la demostracion."
    # El resto del comportamiento no cambia.
    assert payload["total_vehicles"] == 1593
    assert payload["dataset"]["dataset_id"] == LOCAL_DATASET


def test_service_keeps_national_warning_for_peajes() -> None:
    payload = build_service().traffic("mtc_peru_toll_flow")
    assert payload["warning"] == NATIONAL_WARNING


# --- El Strategy no altera el adaptador real ------------------------------------


def test_real_huancayo_adapter_still_works_through_the_service() -> None:
    adapter = HuancayoHistoricalAdapter(
        path=None  # type: ignore[arg-type] - el adaptador no toca disco sin measurements
    )
    assert adapter.get_source_name() == "Municipalidad Provincial de Huancayo"
    resolved = TrafficScopeResolver().resolve(adapter.get_metadata().dataset_id)
    assert resolved.key == "local_historical"