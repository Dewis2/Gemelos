from fastapi.testclient import TestClient

from adapters.inbound.api import create_app
from infrastructure.config import Settings


def test_security_headers_and_bounded_scenarios() -> None:
    settings = Settings(
        _env_file=None, core_repository="memory", demo_repository="memory"
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "no-referrer"
        for configuration in ({"steps": 0}, {"steps": 10001}, {"steps": "many"}):
            response = client.post(
                "/api/v1/scenarios",
                json={"name": "invalid", "configuration": configuration},
            )
            assert response.status_code == 422
