"""Immutable identifiers and file hashes for reproducible ML runs."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def register_run(
    metadata: dict[str, Any], dataset: Path, artifact: Path
) -> dict[str, Any]:
    return {
        **metadata,
        "run_id": str(uuid4()),
        "registered_at_utc": datetime.now(UTC).isoformat(),
        "dataset_sha256": sha256_file(dataset),
        "model_sha256": sha256_file(artifact),
        "registry_schema_version": 1,
    }
