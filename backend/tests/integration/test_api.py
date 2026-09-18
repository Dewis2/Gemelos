from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient


def test_health_exposes_prototype_stage(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "stage": "prototype"}


def test_register_measurement_changes_twin_state(client: TestClient) -> None:
    payload = {
        "source_id": str(uuid4()),
        "road_segment_id": str(uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "traffic_volume": 15,
        "average_speed": 18.5,
        "occupancy": 0.25,
    }
    created = client.post("/api/v1/traffic-measurements", json=payload)
    state = client.get("/api/v1/digital-twin/state")
    assert created.status_code == 201
    assert created.json()["traffic_volume"] == 15
    assert state.status_code == 200
    assert state.json()["latest_measurements"][0]["id"] == created.json()["id"]


def test_prediction_fails_clearly_without_trained_model(client: TestClient) -> None:
    response = client.post(
        "/api/v1/predictions/traffic-flow",
        json={
            "road_segment_id": str(uuid4()),
            "target_timestamp": datetime.now(UTC).isoformat(),
            "features": {"hour": 8},
        },
    )
    assert response.status_code == 503
    assert "No trained model" in response.json()["detail"]


def test_scenario_lifecycle(client: TestClient) -> None:
    created = client.post(
        "/api/v1/scenarios",
        json={
            "name": "PoC",
            "description": "No empirical results",
            "configuration": {},
        },
    )
    scenario_id = created.json()["id"]
    run = client.post(f"/api/v1/scenarios/{scenario_id}/run")
    results = client.get(f"/api/v1/scenarios/{scenario_id}/results")
    assert created.status_code == 201
    assert run.status_code == 200
    assert run.json() == []
    assert results.json() == []


def test_compare_route_is_not_shadowed_by_scenario_id(client: TestClient) -> None:
    first, second = uuid4(), uuid4()
    response = client.get(f"/api/v1/scenarios/compare?scenario_ids={first}&scenario_ids={second}")
    assert response.status_code == 200
    assert response.json()[str(first)]["result_count"] == 0


def test_demo_peru_exposes_catalog_and_huancayo_reference(client: TestClient) -> None:
    datasets = client.get("/api/v1/datasets")
    traffic = client.get(
        "/api/v1/demo/peru/traffic",
        params={"dataset_id": "huancayo_historical_counts_2013"},
    )
    comparison = client.get("/api/v1/demo/peru/comparison")
    assert datasets.status_code == 200
    assert {item["dataset_id"] for item in datasets.json()} >= {
        "mtc_peru_toll_flow",
        "ositran_peru_road_traffic",
        "huancayo_historical_counts_2013",
    }
    assert traffic.status_code == 200
    assert traffic.json()["record_count"] == 9
    assert "No representan tráfico actual de 2026" in traffic.json()["warning"]
    assert comparison.json()["comparable_as_same_dataset"] is False
