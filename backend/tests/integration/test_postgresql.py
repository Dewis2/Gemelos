"""Opt-in tests against a dedicated, migrated PostgreSQL/PostGIS database."""

import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from adapters.inbound.api import create_app
from adapters.outbound.datasets import HuancayoHistoricalAdapter
from adapters.outbound.persistence import (
    SqlAlchemyPredictionRepository,
    SqlAlchemyTrafficAggregateRepository,
)
from domain.entities import TrafficPrediction
from infrastructure.config import Settings
from infrastructure.database.models import (
    IntersectionModel,
    SimulationScenarioModel,
    TrafficMeasurementModel,
    TrafficPredictionModel,
)
from infrastructure.database.seed import TEST_SOURCE_ID, seed_reference_data

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def pg():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "Set TEST_DATABASE_URL to a dedicated migrated database ending in _test"
        )
    if not (make_url(url).database or "").endswith("_test"):
        pytest.fail("Refusing to test against a database without the _test suffix")
    engine = create_engine(url, pool_pre_ping=True)
    factory = sessionmaker(engine, expire_on_commit=False)
    # Only test-owned application tables, never production or PostGIS catalogs.
    with engine.begin() as connection:
        connection.execute(text("SET LOCAL lock_timeout = '5s'"))
        connection.execute(
            text(
                "TRUNCATE simulation_results, traffic_predictions, traffic_measurements, "
                "traffic_signal_plans, simulation_scenarios, road_segments, intersections, "
                "data_sources, traffic_aggregates, traffic_locations, dataset_ingestion_runs"
            )
        )
    settings = Settings(
        _env_file=None,
        database_url=url,
        core_repository="sqlalchemy",
        demo_repository="sqlalchemy",
        mqtt_enabled=False,
        data_root=str(ROOT / "data"),
        ml_model_path="nonexistent-test-model.joblib",
    )
    try:
        yield settings, factory
    finally:
        engine.dispose()


def test_migrations_and_seed_preserve_existing_catalog(pg):
    _, factory = pg
    seed_reference_data(factory)
    with factory.begin() as session:
        first = session.scalar(select(IntersectionModel))
        first.name = "Nombre revisado"
        identifier = first.id
    seed_reference_data(factory)
    with factory() as session:
        assert session.scalar(text("SELECT version_num FROM alembic_version")) == "0002"
        assert session.scalar(text("SELECT count(*) FROM intersections")) == 4
        assert session.get(IntersectionModel, identifier).name == "Nombre revisado"
        assert session.scalar(text("SELECT count(*) FROM road_segments")) == 3
        assert session.scalar(text("SELECT postgis_version()"))


def test_http_measurement_survives_restart_and_failed_fk(pg):
    settings, factory = pg
    with TestClient(create_app(settings)) as client:
        segment = client.get("/api/v1/road-segments").json()[0]["id"]
        payload = dict(
            source_id=str(uuid4()),
            road_segment_id=segment,
            timestamp=datetime.now(UTC).isoformat(),
            traffic_volume=17,
        )
        assert (
            client.post("/api/v1/traffic-measurements", json=payload).status_code == 409
        )
        payload["source_id"] = str(TEST_SOURCE_ID)
        response = client.post("/api/v1/traffic-measurements", json=payload)
        assert response.status_code == 201
        identifier = response.json()["id"]
    with TestClient(create_app(settings)) as restarted:
        rows = restarted.get("/api/v1/digital-twin/state").json()["latest_measurements"]
        assert rows[0]["id"] == identifier
    # UPDATE and DELETE are verified in SQL; no unsupported HTTP CRUD is claimed.
    with factory.begin() as session:
        session.get(TrafficMeasurementModel, UUID(identifier)).traffic_volume = 23
    with factory.begin() as session:
        row = session.get(TrafficMeasurementModel, UUID(identifier))
        assert row.traffic_volume == 23
        session.delete(row)
    with factory() as session:
        assert session.get(TrafficMeasurementModel, UUID(identifier)) is None


def test_http_scenario_results_survive_restart(pg):
    settings, factory = pg
    with TestClient(create_app(settings)) as client:
        created = client.post(
            "/api/v1/scenarios",
            json={
                "name": "Prueba técnica PostgreSQL",
                "description": "No representa datos de campo",
                "configuration": {"steps": 2, "demand": {}},
            },
        )
        assert created.status_code == 201
        identifier = created.json()["id"]
        result = client.post(f"/api/v1/scenarios/{identifier}/run")
        assert result.status_code == 200
        assert len(result.json()) == 3
        ids = {row["id"] for row in result.json()}
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get("/api/v1/scenarios").json()[0]["id"] == identifier
        rows = restarted.get(f"/api/v1/scenarios/{identifier}/results").json()
        assert {row["id"] for row in rows} == ids
    with factory() as session:
        assert (
            session.get(SimulationScenarioModel, UUID(identifier)).configuration[
                "steps"
            ]
            == 2
        )


def test_historical_query_uses_database_and_ingestion_is_idempotent(pg, monkeypatch):
    settings, factory = pg
    adapter = HuancayoHistoricalAdapter(
        ROOT / "data/reference/huancayo_historical_counts.csv"
    )
    repository = SqlAlchemyTrafficAggregateRepository(factory)
    rows = list(adapter.stream_measurements())
    assert len(rows) == 9
    assert all(repository.upsert(row) == "inserted" for row in rows)
    assert all(repository.upsert(row) == "duplicate" for row in rows)

    def forbid_file_read(*args, **kwargs):
        raise AssertionError("The persistent query must not read the CSV")

    monkeypatch.setattr(
        HuancayoHistoricalAdapter, "stream_measurements", forbid_file_read
    )
    with TestClient(create_app(settings)) as client:
        response = client.get(
            "/api/v1/demo/peru/traffic",
            params={
                "dataset_id": "huancayo_historical_counts_2013",
            },
        )
        assert response.status_code == 200
        assert response.json()["record_count"] == 9
        filtered = client.get(
            "/api/v1/demo/peru/traffic",
            params={
                "dataset_id": "huancayo_historical_counts_2013",
                "location_id": rows[0].source_location_id,
                "vehicle_type": rows[0].vehicle_category,
            },
        ).json()
        assert all(
            r["source_location_id"] == rows[0].source_location_id
            for r in filtered["records"]
        )


def test_prediction_repository_commits_and_recovers_after_failure(pg):
    _, factory = pg
    seed_reference_data(factory)
    repository = SqlAlchemyPredictionRepository(factory)
    with factory() as session:
        segment = session.scalar(text("SELECT id FROM road_segments LIMIT 1"))
    prediction = TrafficPrediction(
        road_segment_id=uuid4(),
        target_timestamp=datetime.now(UTC),
        prediction_timestamp=datetime.now(UTC),
        predicted_volume=10,
        model_version="test-double-not-empirical",
    )
    with pytest.raises(IntegrityError):
        repository.add(prediction)
    prediction = TrafficPrediction(
        road_segment_id=segment,
        target_timestamp=datetime.now(UTC),
        prediction_timestamp=datetime.now(UTC),
        predicted_volume=10,
        model_version="test-double-not-empirical",
    )
    repository.add(prediction)
    with factory() as session:
        assert session.get(TrafficPredictionModel, prediction.id).predicted_volume == 10


def test_postgis_round_trip(pg):
    _, factory = pg
    seed_reference_data(factory)
    # A synthetic coordinate in the isolated test DB, never a claimed corridor point.
    with factory.begin() as session:
        session.execute(
            text("UPDATE intersections SET geometry=ST_SetSRID(ST_MakePoint(0,0),4326)")
        )
    with factory() as session:
        assert (
            session.scalar(text("SELECT ST_SRID(geometry) FROM intersections LIMIT 1"))
            == 4326
        )
        assert (
            session.scalar(
                text("SELECT ST_AsText(geometry) FROM intersections LIMIT 1")
            )
            == "POINT(0 0)"
        )
