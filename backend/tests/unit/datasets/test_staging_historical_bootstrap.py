"""Historical staging import is complete and repeatable without a live database."""

from pathlib import Path

import pytest

from adapters.outbound.persistence import InMemoryTrafficAggregateRepository
from infrastructure.bootstrap_historical import load_historical_reference

DATA = Path(__file__).resolve().parents[4] / "data"


def test_historical_import_is_complete_and_idempotent():
    repository = InMemoryTrafficAggregateRepository()

    first = load_historical_reference(DATA, repository)
    assert first["records_verified"] == 9
    assert first["inserted"] == 9
    assert first["unchanged"] == 0
    assert first["current_local_2026"] is False

    second = load_historical_reference(DATA, repository)
    assert second["records_verified"] == 9
    assert second["inserted"] == 0
    assert second["unchanged"] == 9


def test_missing_reference_fails_loudly(tmp_path: Path):
    with pytest.raises(RuntimeError, match="did not pass validation"):
        load_historical_reference(tmp_path, InMemoryTrafficAggregateRepository())
