import json
from pathlib import Path

from adapters.outbound.datasets.huancayo_reference import HuancayoHistoricalAdapter
from adapters.outbound.datasets.mtc import MtcTollFlowAdapter, MtcTollLocationAdapter
from adapters.outbound.datasets.ositran import OsitranRoadTrafficAdapter


def test_mtc_parser_detects_real_mapping_and_region(tmp_path: Path) -> None:
    path = tmp_path / "synthetic_test_fixture_mtc.csv"
    path.write_text(
        "ADMINIST;CODIGO_PEAJE;DEPARTAMENTO;NOMBRE_PEAJE;VEH_TOTAL;VEH_LIGEROS_TOTAL;VEH_PESADOS_TOTAL;ANIO;MES;PERIODO\n"
        "No concesionado;12TEST;Junín;Prueba;1 200;800;400;2025;01;202501\n",
        encoding="cp1252",
    )
    adapter = MtcTollFlowAdapter(path)
    report = adapter.validate()
    rows = list(adapter.stream_measurements(region="JUNIN"))
    assert report["delimiter"] == ";"
    assert report["period_min"] == "2025-01"
    assert [item.vehicle_count for item in rows] == [1200, 800, 400]
    assert all(item.dataset_scope.value == "peru_official_demo" for item in rows)


def test_ositran_parser_preserves_original_columns(tmp_path: Path) -> None:
    path = tmp_path / "synthetic_test_fixture_ositran.csv"
    path.write_text(
        '"ANIO";"MES";"ENTIDAD_PRESTADORA";"CONCESION";"SIGLAS";'
        '"PEAJE";"CLASE_VEHICULO";"TIPO_TARIFA";"TIPO_VEHICULO";'
        '"TIPO_EJE_VEH";"NRO_EJES";"CANTIDAD VEHICULOS"\n'
        '"2025";"2";"Entidad";"Concesión";"SIG";"Peaje Uno";'
        '"PAGANTES";"Normal";"PESADO";"EJE VEHICULO";"2 ejes";"42"\n',
        encoding="utf-8",
    )
    adapter = OsitranRoadTrafficAdapter(path)
    rows = list(adapter.stream_measurements())
    assert adapter.validate()["rows_valid"] == 1
    assert rows[0].vehicle_count == 42
    assert rows[0].metadata["source_columns"]["CLASE_VEHICULO"] == "PAGANTES"


def test_geojson_parser_uses_declared_crs_and_rejects_invalid_geometry(
    tmp_path: Path,
) -> None:
    path = tmp_path / "synthetic_test_fixture_locations.geojson"
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "crs": {
                    "type": "name",
                    "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
                },
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-75.2, -12.1]},
                        "properties": {
                            "IDPEAJE": 1,
                            "CODPEAJE": "12TEST",
                            "NOMBRE": "Prueba",
                            "DEPARTAMEN": "JUNIN",
                            "FECCORTE": "20250630",
                        },
                    },
                    {"type": "Feature", "geometry": None, "properties": {"IDPEAJE": 2}},
                ],
            }
        ),
        encoding="utf-8",
    )
    adapter = MtcTollLocationAdapter(path)
    report = adapter.validate()
    assert report["features_read"] == 2
    assert report["invalid_geometries"] == 1
    assert report["crs"] == "urn:ogc:def:crs:OGC:1.3:CRS84"


def test_huancayo_2013_is_never_labeled_current() -> None:
    adapter = HuancayoHistoricalAdapter(
        Path("data/reference/huancayo_historical_counts.csv")
    )
    rows = list(adapter.stream_measurements())
    assert len(rows) == 9
    assert all(row.dataset_scope.value == "huancayo_local_historical" for row in rows)
    assert all(row.metadata["historical"] is True for row in rows)
    assert all(row.metadata["year"] == 2013 for row in rows)
