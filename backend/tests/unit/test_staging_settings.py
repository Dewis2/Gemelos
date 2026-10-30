"""Cloud configuration rules and provider-issued Postgres URLs."""

import pytest
from pydantic import ValidationError

from infrastructure.config import Settings


def test_render_postgres_dsn_uses_installed_psycopg_driver():
    settings = Settings(
        _env_file=None,
        database_url="postgresql://user:pass@remote.example:5432/digital_twin",
    )
    assert settings.database_url == (
        "postgresql+psycopg://user:pass@remote.example:5432/digital_twin"
    )


def test_staging_requires_sql_and_https_frontend():
    settings = Settings(
        _env_file=None,
        environment="staging",
        database_url="postgres://user:pass@remote.example:5432/digital_twin",
        core_repository="sqlalchemy",
        demo_repository="sqlalchemy",
        cors_origins=["https://gemelos-staging-frontend.onrender.com"],
    )
    assert settings.database_url.startswith("postgresql+psycopg://")


@pytest.mark.parametrize(
    "changes",
    [
        {"core_repository": "memory"},
        {"demo_repository": "memory"},
        {"cors_origins": ["http://localhost:5173"]},
        {"database_url": "postgresql://user:pass@localhost:5432/digital_twin"},
    ],
)
def test_staging_rejects_local_services(changes):
    arguments = dict(
        _env_file=None,
        environment="staging",
        database_url="postgresql://user:pass@remote.example:5432/digital_twin",
        core_repository="sqlalchemy",
        demo_repository="sqlalchemy",
        cors_origins=["https://gemelos-staging-frontend.onrender.com"],
    )
    arguments.update(changes)
    with pytest.raises(ValidationError):
        Settings(**arguments)
