"""Integration tests for versioned PostgreSQL routines (opt-in database)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from adapters.outbound.persistence import SqlAlchemyRoadNetworkRepository
from infrastructure.database.seed import TEST_SOURCE_ID, seed_reference_data

from tests.integration.test_postgresql import pg  # noqa: F401


def test_stored_procedure_and_summary(pg):
    settings, factory = pg
    seed_reference_data(factory)
    segment_id = SqlAlchemyRoadNetworkRepository(factory).list_segments()[0].id
    measurement_id = uuid4()
    moment = datetime(2026, 10, 23, 12, tzinfo=UTC)
    with factory.begin() as session:
        session.execute(
            text(
                "CALL public.sp_register_traffic_measurement("
                ":id, :source_id, :segment_id, :timestamp, :volume, :speed, :occupancy)"
            ),
            {
                "id": measurement_id,
                "source_id": TEST_SOURCE_ID,
                "segment_id": segment_id,
                "timestamp": moment,
                "volume": 12,
                "speed": 23.0,
                "occupancy": 0.4,
            },
        )
        row = session.execute(
            text(
                "SELECT * FROM public.fn_traffic_summary("
                ":segment_id, :start_time, :end_time)"
            ),
            {
                "segment_id": segment_id,
                "start_time": moment - timedelta(minutes=1),
                "end_time": moment + timedelta(minutes=1),
            },
        ).one()
        assert row.measurement_count == 1
        assert row.volume_total == 12
        assert row.average_speed == pytest.approx(23.0)


def test_procedure_rejects_negative_volume(pg):
    _, factory = pg
    seed_reference_data(factory)
    segment_id = SqlAlchemyRoadNetworkRepository(factory).list_segments()[0].id
    with pytest.raises(DBAPIError):
        with factory.begin() as session:
            session.execute(
                text(
                    "CALL public.sp_register_traffic_measurement("
                    ":id, :source_id, :segment_id, :timestamp, :volume, :speed, :occupancy)"
                ),
                {
                    "id": uuid4(),
                    "source_id": TEST_SOURCE_ID,
                    "segment_id": segment_id,
                    "timestamp": datetime.now(UTC),
                    "volume": -1,
                    "speed": None,
                    "occupancy": None,
                },
            )
