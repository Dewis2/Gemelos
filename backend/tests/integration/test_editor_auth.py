from fastapi.testclient import TestClient

from adapters.inbound.api import create_app
from infrastructure.auth import password_hash
from infrastructure.config import Settings


def test_staging_editor_controls_writes_and_keeps_reads_public() -> None:
    settings = Settings(
        _env_file=None,
        environment="test",
        core_repository="memory",
        demo_repository="memory",
        auth_required=True,
        auth_username="editor",
        auth_password_hash=password_hash("test-password", b"0123456789abcdef"),
        auth_secret="test-secret-with-at-least-32-characters",
        cors_origins=["https://frontend.example.org"],
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/health").status_code == 200
        body = {"name": "Prueba", "configuration": {}}
        unauthenticated = client.post("/api/v1/scenarios", json=body)
        assert unauthenticated.status_code == 401
        assert unauthenticated.headers["x-content-type-options"] == "nosniff"
        assert unauthenticated.headers["x-frame-options"] == "DENY"
        assert (
            client.post(
                "/api/v1/auth/login",
                json={"username": "editor", "password": "incorrecta"},
            ).status_code
            == 401
        )
        logged_in = client.post(
            "/api/v1/auth/login",
            json={"username": "editor", "password": "test-password"},
        )
        assert logged_in.status_code == 200
        token = logged_in.json()["access_token"]
        assert (
            client.post(
                "/api/v1/scenarios",
                json=body,
                headers={"Authorization": f"Bearer {token}"},
            ).status_code
            == 201
        )
        assert (
            client.post(
                "/api/v1/scenarios",
                json=body,
                headers={"Authorization": f"Bearer {token}altered"},
            ).status_code
            == 401
        )
        preflight = client.options(
            "/api/v1/scenarios",
            headers={
                "Origin": "https://frontend.example.org",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert preflight.status_code == 200
        assert (
            preflight.headers["access-control-allow-origin"]
            == "https://frontend.example.org"
        )
