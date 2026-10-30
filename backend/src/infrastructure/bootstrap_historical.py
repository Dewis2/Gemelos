"""Seed the nine *historical 2013* Huancayo records into the staging database.

The online demo reads traffic aggregates from PostgreSQL, not directly from its CSV.
Run once per staging container start after Alembic migrations. The repository's
natural-key upsert makes repeat runs idempotent.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from adapters.outbound.datasets import HuancayoHistoricalAdapter
from application.ports.outbound import TrafficAggregateRepositoryPort
from infrastructure.config import get_settings

DATASET_ID = "huancayo_historical_counts_2013"
EXPECTED_ROWS = 9


def load_historical_reference(
    data_root: Path, repository: TrafficAggregateRepositoryPort
) -> dict[str, Any]:
    adapter = HuancayoHistoricalAdapter(
        data_root / "reference" / "huancayo_historical_counts.csv"
    )
    validation = adapter.validate()
    if not validation.get("valid"):
        raise RuntimeError("Historical reference CSV did not pass validation.")

    records = list(adapter.stream_measurements())
    if len(records) != EXPECTED_ROWS:
        raise RuntimeError("Expected exactly nine historical 2013 observations.")

    changes = Counter(repository.upsert(record) for record in records)
    persisted = repository.list_by_dataset(DATASET_ID)
    if len(persisted) != EXPECTED_ROWS:
        raise RuntimeError("Historical import did not persist all nine observations.")
    expected = {row.natural_key: row.vehicle_count for row in records}
    actual = {row.natural_key: row.vehicle_count for row in persisted}
    if actual != expected:
        raise RuntimeError("Historical database records differ from reference CSV.")

    return {
        "dataset_id": DATASET_ID,
        "scope": "huancayo_local_historical_2013",
        "records_verified": len(persisted),
        "inserted": changes["inserted"],
        "updated": changes["updated"],
        "unchanged": changes["duplicate"],
        "current_local_2026": False,
    }


def main() -> None:
    settings = get_settings()
    if settings.environment != "staging" or settings.demo_repository != "sqlalchemy":
        raise RuntimeError("Historical bootstrap requires PostgreSQL staging.")

    from adapters.outbound.persistence import SqlAlchemyTrafficAggregateRepository
    from infrastructure.database.session import SessionFactory

    report = load_historical_reference(
        Path(settings.data_root), SqlAlchemyTrafficAggregateRepository(SessionFactory)
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
