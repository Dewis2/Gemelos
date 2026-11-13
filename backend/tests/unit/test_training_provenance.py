"""The model registry records the exact input and artifact bytes."""

import hashlib
from pathlib import Path
from uuid import UUID

from ml.src.training.provenance import register_run


def test_registered_run_contains_reproducible_hashes(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.csv"
    model = tmp_path / "model.joblib"
    dataset.write_bytes(b"timestamp,volume\n2026-01-01,12\n")
    model.write_bytes(b"example-model")

    result = register_run({"mae": 2.5}, dataset, model)

    UUID(result["run_id"])
    assert result["mae"] == 2.5
    assert result["dataset_sha256"] == hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert result["model_sha256"] == hashlib.sha256(model.read_bytes()).hexdigest()
    assert result["registry_schema_version"] == 1
