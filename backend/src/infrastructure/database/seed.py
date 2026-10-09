"""Idempotent technical catalogs; these rows are not field observations."""

from dataclasses import asdict
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.corridor_reference import build_corridor
from infrastructure.database.models import (
    DataSourceModel,
    IntersectionModel,
    RoadSegmentModel,
)

TEST_SOURCE_ID = uuid5(
    NAMESPACE_URL, "https://gemelo-digital-huancayo.org/sources/technical-test"
)


def seed_reference_data(factory: sessionmaker[Session]) -> None:
    nodes, segments = build_corridor()
    with factory.begin() as session:
        for model, items in ((IntersectionModel, nodes), (RoadSegmentModel, segments)):
            for item in items:
                session.execute(
                    insert(model).values(**asdict(item)).on_conflict_do_nothing()
                )
        session.execute(
            insert(DataSourceModel)
            .values(
                id=TEST_SOURCE_ID,
                name="Pruebas técnicas locales",
                source_type="technical_test",
                description="Datos de prueba; no representan aforos presenciales del corredor.",
                active=True,
            )
            .on_conflict_do_nothing()
        )
