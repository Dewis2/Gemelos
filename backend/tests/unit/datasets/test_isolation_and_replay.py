import time
from pathlib import Path
from typing import Any

from adapters.outbound.datasets.huancayo_reference import HuancayoHistoricalAdapter
from adapters.outbound.persistence import InMemoryTrafficAggregateRepository
from application.dto.peru_demo import DatasetScope, TrafficAggregate
from application.services import HistoricalReplayService, PeruDemoQueryService


class CapturingPublisher:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any]]] = []

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.messages.append((topic, payload))


def sample(scope: DatasetScope = DatasetScope.PERU_OFFICIAL_DEMO) -> TrafficAggregate:
    return TrafficAggregate(
        dataset_id="mtc_peru_toll_flow",
        source_record_id="one",
        source_provider="MTC",
        source_country="Peru",
        source_region="Junín",
        source_location_id="12TEST",
        source_location_name="Prueba",
        period_start="2025-01-01",
        period_end="2025-01-31",
        temporal_granularity="monthly",
        vehicle_category="total",
        vehicle_count=10,
        dataset_scope=scope,
    )


def test_peru_toll_data_never_becomes_huancayo_urban_data() -> None:
    repository = InMemoryTrafficAggregateRepository()
    repository.upsert(sample())
    assert repository.list_by_scope("huancayo_local_current") == []
    assert len(repository.list_by_scope("peru_official_demo")) == 1


def test_ingestion_is_idempotent_and_detects_duplicates() -> None:
    repository = InMemoryTrafficAggregateRepository()
    assert repository.upsert(sample()) == "inserted"
    assert repository.upsert(sample()) == "duplicate"


def test_historical_replay_payload_keeps_original_period() -> None:
    adapter = HuancayoHistoricalAdapter(
        Path("data/reference/huancayo_historical_counts.csv")
    )
    query = PeruDemoQueryService({adapter.get_metadata().dataset_id: adapter}, adapter)
    publisher = CapturingPublisher()
    service = HistoricalReplayService(
        query, InMemoryTrafficAggregateRepository(), publisher, mqtt_enabled=True
    )
    service.start(
        adapter.get_metadata().dataset_id,
        start_period=None,
        end_period=None,
        location_id="P03",
        speed_factor=60,
        limit=1,
    )
    time.sleep(0.15)
    assert publisher.messages[0][0] == "huancayo/ferrocarril/traffic"
    payload = publisher.messages[0][1]
    assert payload["original_period"]["granularity"] == "day_period"
    assert payload["historical_period"] == "2013-01"
    assert payload["replay_emitted_at"]
