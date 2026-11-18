"""Run the bundled experiment with the real SUMO binary when installed."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from adapters.inbound.api import create_app
from adapters.outbound.sumo.exploratory import ExploratorySumoRunner
from infrastructure.auth import password_hash
from infrastructure.config import Settings

pytest.importorskip("sumo")

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("level", ["baja", "normal", "alta"])
def test_versioned_sumo_run_reproduces_published_aggregate(level: str) -> None:
    runner = ExploratorySumoRunner(
        ROOT / "simulation" / "sumo",
        ROOT / "frontend" / "src" / "data" / "osm-exploratory-report.json",
    )
    observed = runner.run(level)
    published = runner.report()["scenarios"][level]
    for key in (
        "routes_generated",
        "vehicles_inserted",
        "vehicles_arrived",
        "vehicles_remaining",
        "mean_trip_duration_seconds",
        "mean_waiting_seconds",
        "mean_time_loss_seconds",
        "mean_trip_speed_kmh",
    ):
        assert observed[key] == published[key]


def test_http_sumo_execution_requires_editor_and_returns_aggregate() -> None:
    settings = Settings(
        _env_file=None,
        environment="test",
        core_repository="memory",
        demo_repository="memory",
        auth_required=True,
        auth_username="editor",
        auth_password_hash=password_hash("test-password", b"0123456789abcdef"),
        auth_secret="test-secret-with-at-least-32-characters",
        sumo_assets_root=str(ROOT / "simulation" / "sumo"),
        sumo_report_path=str(
            ROOT / "frontend" / "src" / "data" / "osm-exploratory-report.json"
        ),
    )
    with TestClient(create_app(settings)) as client:
        route = "/api/v1/simulations/exploratory/normal/run"
        assert client.post(route).status_code == 401
        token = client.post(
            "/api/v1/auth/login",
            json={"username": "editor", "password": "test-password"},
        ).json()["access_token"]
        invalid = client.post(
            "/api/v1/simulations/exploratory/custom/run",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert invalid.status_code == 422
        response = client.post(route, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["vehicles_arrived"] == 225
        assert response.json()["study_type"] == "exploratory_uncalibrated"
