"""PostgreSQL/PostGIS fixture shared by opt-in integration tests.

It refuses to touch any database that does not end with _test.
"""

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from infrastructure.config import Settings

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
