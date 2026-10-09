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
    segment = client.get("/api/v1/road-segments").json()[0]
    response = client.post(
        "/api/v1/predictions/traffic-flow",
        json={
            "road_segment_id": segment["id"],
            "target_timestamp": datetime.now(UTC).isoformat(),
            "features": {"day_of_week": 3, "hour": 8, "is_weekend": 0, "month": 10},
        },
    )
    assert response.status_code == 503
    assert "No trained model" in response.json()["detail"]


def test_prediction_rejects_incomplete_features(client: TestClient) -> None:
    segment = client.get("/api/v1/road-segments").json()[0]
    response = client.post(
        "/api/v1/predictions/traffic-flow",
        json={
            "road_segment_id": segment["id"],
            "target_timestamp": datetime.now(UTC).isoformat(),
            "features": {"hour": 8},
        },
    )
    assert response.status_code == 422
    assert "Faltan variables de entrada del modelo" in response.json()["detail"]


def test_prediction_rejects_out_of_range_feature(client: TestClient) -> None:
    segment = client.get("/api/v1/road-segments").json()[0]
    response = client.post(
        "/api/v1/predictions/traffic-flow",
        json={
            "road_segment_id": segment["id"],
            "target_timestamp": datetime.now(UTC).isoformat(),
            "features": {"day_of_week": 3, "hour": 99, "is_weekend": 0, "month": 10},
        },
    )
    assert response.status_code == 422
    assert "hour" in response.json()["detail"]


def test_prediction_rejects_unknown_road_segment(client: TestClient) -> None:
    response = client.post(
        "/api/v1/predictions/traffic-flow",
        json={
            "road_segment_id": str(uuid4()),
            "target_timestamp": datetime.now(UTC).isoformat(),
            "features": {"day_of_week": 3, "hour": 8, "is_weekend": 0, "month": 10},
        },
    )
    assert response.status_code == 404
    assert "no está registrado en la red del corredor" in response.json()["detail"]


def test_road_segments_expose_the_corridor(client: TestClient) -> None:
    segments = client.get("/api/v1/road-segments")
    nodes = client.get("/api/v1/intersections")
    assert segments.status_code == 200
    assert len(segments.json()) == 3
    assert len(nodes.json()) == 4
    names = [segment["name"] for segment in segments.json()]
    assert all("Av. Ferrocarril" in name for name in names)
    # La geometria sigue pendiente de validacion cartografica.
    assert all(segment["geometry"] is None for segment in segments.json())


def test_twin_state_counts_the_corridor(client: TestClient) -> None:
    state = client.get("/api/v1/digital-twin/state").json()
    assert state["road_segment_count"] == 3
    assert state["intersection_count"] == 4
    assert state["geometry_status"] == "pending_validation"


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

    # El corredor ahora aporta segmentos, asi que la simulacion emite una fila por
    # tramo. Los indicadores siguen en cero porque el adaptador de simulacion no
    # calcula magnitudes fisicas; el frontend lo presenta como marcador de posicion.
    segments = client.get("/api/v1/road-segments").json()
    assert len(segments) == 3
    assert len(run.json()) == len(segments)
    assert results.json() == run.json()
    for row, segment in zip(run.json(), segments, strict=True):
        assert row["road_segment_id"] == segment["id"]
        assert row["travel_time"] == 0.0
        assert row["average_speed"] == 0.0
        assert row["delay"] == 0.0
        assert row["queue_length"] == 0.0
        assert row["emissions"] == {}


def test_compare_route_is_not_shadowed_by_scenario_id(client: TestClient) -> None:
    first, second = uuid4(), uuid4()
    response = client.get(
        f"/api/v1/scenarios/compare?scenario_ids={first}&scenario_ids={second}"
    )
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
