from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from adapters.inbound.api import create_app
from infrastructure.config import Settings


@pytest.fixture
def app() -> FastAPI:
    return create_app(
        Settings(
            environment="test",
            ml_model_path="nonexistent-test-model.joblib",
            cors_origins=["http://testserver"],
        )
    )


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
