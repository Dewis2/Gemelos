from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from adapters.outbound.datasets import (
    HuancayoHistoricalAdapter,
    MtcTollFlowAdapter,
    MtcTollLocationAdapter,
    OsitranRoadTrafficAdapter,
)
from adapters.outbound.datasets.common import normalize_text, sha256
from adapters.outbound.persistence import (
    InMemoryTrafficAggregateRepository,
    SqlAlchemyIngestionRunRecorder,
    SqlAlchemyTrafficAggregateRepository,
    SqlAlchemyTrafficLocationRepository,
)
from application.ports.outbound import TrafficDatasetPort
from application.services import PeruDemoQueryService

DOWNLOADS: dict[str, list[tuple[str, str]]] = {
    "mtc-toll-flow": [
        (
            "https://www.datosabiertos.gob.pe/sites/default/files/Flujo%20vehicular%20registrado%20en%20peajes_2014-2026_I.csv",
            "mtc_toll_flow.csv",
        ),
        (
            "https://www.datosabiertos.gob.pe/sites/default/files/Diccionario_Datos_Flujo%20vehicular_2014-2026_I.xlsx",
            "data_dictionary.xlsx",
        ),
        (
            "https://www.datosabiertos.gob.pe/sites/default/files/Metadatos_Flujo%20vehicular_2014-2026_I.docx",
            "metadata.docx",
        ),
    ],
    "mtc-toll-locations": [
        (
            "https://www.datosabiertos.gob.pe/sites/default/files/unidades_peaje_2024-2025_ii.geojson",
            "mtc_toll_locations.geojson",
        ),
        (
            "https://www.datosabiertos.gob.pe/sites/default/files/Diccionario_Datos_Peaje_2024-2025_ii.pdf",
            "data_dictionary.pdf",
        ),
        (
            "https://www.datosabiertos.gob.pe/sites/default/files/Metadatos_peajes_2024-2025_ii.pdf",
            "metadata.pdf",
        ),
    ],
    "ositran-road-traffic": [
        (
            "https://www.datosabiertos.gob.pe/sites/default/files/202603-PDE-REP-00201.csv",
            "ositran_road_traffic.csv",
        ),
        (
            "https://www.datosabiertos.gob.pe/sites/default/files/Diccionario%20PDE-REP-00201.xlsx",
            "data_dictionary.xlsx",
        ),
        (
            "https://www.datosabiertos.gob.pe/sites/default/files/Metadatos%20PDE-REP-00201.xlsx",
            "metadata.xlsx",
        ),
    ],
}


def data_root() -> Path:
    return Path(os.getenv("DATA_ROOT", "data"))


def adapters(
    root: Path,
) -> tuple[dict[str, TrafficDatasetPort], MtcTollLocationAdapter]:
    flow = MtcTollFlowAdapter(root / "external/mtc/toll_flow/raw/mtc_toll_flow.csv")
    locations = MtcTollLocationAdapter(
        root / "external/mtc/toll_locations/raw/mtc_toll_locations.geojson"
    )
    ositran = OsitranRoadTrafficAdapter(
        root / "external/ositran/road_traffic/raw/ositran_road_traffic.csv"
    )
    huancayo = HuancayoHistoricalAdapter(
        root / "reference/huancayo_historical_counts.csv"
    )
    return (
        {
            "mtc-toll-flow": flow,
            "mtc-toll-locations": locations,
            "ositran-road-traffic": ositran,
            "huancayo-historical": huancayo,
        },
        locations,
    )


def download(dataset: str, *, force: bool, dry_run: bool) -> dict[str, Any]:
    root = data_root()
    destinations = {
        "mtc-toll-flow": root / "external/mtc/toll_flow/raw",
        "mtc-toll-locations": root / "external/mtc/toll_locations/raw",
        "ositran-road-traffic": root / "external/ositran/road_traffic/raw",
    }
    result: dict[str, Any] = {"dataset": dataset, "files": [], "dry_run": dry_run}
    for url, filename in DOWNLOADS[dataset]:
        target = destinations[dataset] / filename
        action = "skipped_existing" if target.exists() and not force else "download"
        if action == "download" and not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=120) as response:
                target.write_bytes(response.read())
            action = "downloaded"
        result["files"].append(
            {
                "url": url,
                "path": str(target),
                "action": action,
                "checksum": sha256(target) if target.exists() else None,
            }
        )
    return result


def _catalog_text(metadata: dict[str, Any], path: Path | None) -> str:
    downloaded_at = (
        datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
        if path and path.exists()
        else None
    )
    lines = [
        f"dataset_id: {metadata['dataset_id']}",
        f'title: "{metadata["title"]}"',
        f'provider: "{metadata["provider"]}"',
        f"country: {metadata['country']}",
        f"source_type: {metadata['source_type']}",
        f"temporal_granularity: {metadata['temporal_granularity']}",
        f"spatial_granularity: {metadata['spatial_granularity']}",
        f"period_min: {metadata['period_min'] or 'null'}",
        f"period_max: {metadata['period_max'] or 'null'}",
        f'license: "{metadata["license"]}"',
        f'source_page: "{metadata["source_page"]}"',
        f"downloaded_at: {downloaded_at or 'null'}",
        f"checksum: {sha256(path) if path and path.exists() else 'null'}",
        f"local_validation: {str(metadata['local_validation']).lower()}",
        "allowed_uses:",
    ]
    lines.extend(
        f"  {key}: {str(value).lower()}"
        for key, value in metadata["allowed_uses"].items()
    )
    lines.append("limitations:")
    lines.extend(f'  - "{item}"' for item in metadata["limitations"])
    return "\n".join(lines) + "\n"


def _join_report(
    flow: MtcTollFlowAdapter, locations: MtcTollLocationAdapter
) -> dict[str, Any]:
    flow_locations = {
        str(item["source_location_id"]): item
        for item in flow.get_locations()
        if isinstance(item, dict)
    }
    geo_locations = locations.get_locations()
    geo_codes = {item.source_location_id for item in geo_locations}
    exact = set(flow_locations).intersection(geo_codes)
    geo_by_name: dict[str, set[str]] = defaultdict(set)
    for geo_item in geo_locations:
        geo_by_name[normalize_text(geo_item.name)].add(geo_item.source_location_id)
    normalized: set[str] = set()
    ambiguous: set[str] = set()
    for code, flow_item in flow_locations.items():
        if code in exact:
            continue
        matches = geo_by_name.get(normalize_text(str(flow_item["name"])), set())
        if len(matches) == 1:
            normalized.add(code)
        elif len(matches) > 1:
            ambiguous.add(code)
    unmatched = set(flow_locations).difference(exact, normalized, ambiguous)
    matched = len(exact) + len(normalized)
    return {
        "join_priority": ["official_code", "normalized_name"],
        "flow_unique_locations": len(flow_locations),
        "geojson_unique_locations": len(geo_codes),
        "matched_exact": len(exact),
        "matched_normalized": len(normalized),
        "unmatched": len(unmatched),
        "ambiguous": len(ambiguous),
        "unmatched_location_ids": sorted(unmatched),
        "ambiguous_location_ids": sorted(ambiguous),
        "join_rate_percent": (
            round((matched / len(flow_locations) * 100), 4) if flow_locations else 0.0
        ),
    }


def generate_reports(root: Path) -> dict[str, Any]:
    available, location_adapter = adapters(root)
    flow = available["mtc-toll-flow"]
    ositran = available["ositran-road-traffic"]
    huancayo = available["huancayo-historical"]
    assert isinstance(flow, MtcTollFlowAdapter)
    assert isinstance(ositran, OsitranRoadTrafficAdapter)
    assert isinstance(huancayo, HuancayoHistoricalAdapter)
    reports_dir = root / "reports"
    catalog_dir = root / "catalog"
    reports_dir.mkdir(parents=True, exist_ok=True)
    catalog_dir.mkdir(parents=True, exist_ok=True)

    mtc_report = flow.validate()
    ositran_report = ositran.validate()
    spatial_validation = location_adapter.validate()
    spatial_report = {
        "features_read": spatial_validation.get("features_read", 0),
        "features_inserted": 0,
        "features_insertable": spatial_validation.get("features_insertable", 0),
        "invalid_geometries": spatial_validation.get("invalid_geometries", 0),
        "crs": spatial_validation.get("crs"),
        "bbox": spatial_validation.get("bbox"),
        "database_status": "not_executed",
        "limitations": [
            "La validación geométrica se ejecutó; la importación PostGIS requiere "
            "PostgreSQL disponible."
        ],
    }
    query = PeruDemoQueryService(
        {adapter.get_metadata().dataset_id: adapter for adapter in available.values()},
        location_adapter,
    )
    junin = query.junin()
    join = _join_report(flow, location_adapter)

    (reports_dir / "mtc_schema_report.json").write_text(
        json.dumps(mtc_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (reports_dir / "ositran_schema_report.json").write_text(
        json.dumps(ositran_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (reports_dir / "spatial_import_report.json").write_text(
        json.dumps(spatial_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (reports_dir / "peru_junin_discovery.json").write_text(
        json.dumps(junin, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    natural_keys: Counter[str] = Counter()
    valid_measurements = 0
    for adapter in (flow, ositran, huancayo):
        for measurement in adapter.stream_measurements():
            natural_keys[measurement.natural_key] += 1
            valid_measurements += 1
    duplicates = sum(value - 1 for value in natural_keys.values() if value > 1)
    ingestion_report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "datasets_downloaded": [
            adapter.get_metadata().dataset_id
            for adapter in (flow, location_adapter, ositran)
            if adapter.path.exists()
        ],
        "files_processed": 4,
        "rows_read": {
            "mtc_toll_flow": mtc_report.get("row_count", 0),
            "ositran_road_traffic": ositran_report.get("row_count", 0),
            "mtc_toll_locations": spatial_validation.get("features_read", 0),
            "huancayo_historical": len(huancayo._rows()),
        },
        "rows_valid": {
            "mtc_toll_flow": mtc_report.get("rows_valid", 0),
            "ositran_road_traffic": ositran_report.get("rows_valid", 0),
            "mtc_toll_locations": spatial_validation.get("features_insertable", 0),
            "huancayo_historical": len(huancayo._rows()),
        },
        "rows_invalid": {
            "mtc_toll_flow": mtc_report.get("rows_invalid", 0),
            "ositran_road_traffic": ositran_report.get("rows_invalid", 0),
            "mtc_toll_locations": spatial_validation.get("invalid_geometries", 0),
            "huancayo_historical": 0,
        },
        "normalized_measurements": valid_measurements,
        "duplicates_within_sources": duplicates,
        "period_min": min(
            value
            for value in [
                mtc_report.get("period_min"),
                ositran_report.get("period_min"),
            ]
            if value
        ),
        "period_max": max(
            value
            for value in [
                mtc_report.get("period_max"),
                ositran_report.get("period_max"),
            ]
            if value
        ),
        "locations": {
            "mtc_flow_unique": mtc_report.get("locations"),
            "geojson_features": spatial_validation.get("features_read"),
            "geojson_unique_current": len(query.locations()),
            "ositran_unique": ositran_report.get("locations"),
        },
        "regions": mtc_report.get("regions", []),
        "vehicle_categories": {
            "mtc": mtc_report.get("vehicle_categories", []),
            "ositran": ositran_report.get("vehicle_categories", []),
        },
        "nulls": {
            "mtc": mtc_report.get("nulls", {}),
            "ositran": ositran_report.get("nulls", {}),
        },
        "join_rate_with_geojson": join,
        "persistence": "not_executed_by_report_generator",
    }
    (reports_dir / "peru_demo_ingestion_report.json").write_text(
        json.dumps(ingestion_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    catalog_paths = {
        "mtc-toll-flow": root / "external/mtc/toll_flow/raw/mtc_toll_flow.csv",
        "mtc-toll-locations": root
        / "external/mtc/toll_locations/raw/mtc_toll_locations.geojson",
        "ositran-road-traffic": root
        / "external/ositran/road_traffic/raw/ositran_road_traffic.csv",
        "huancayo-historical": root / "reference/huancayo_historical_counts.csv",
    }
    catalog_names = {
        "mtc-toll-flow": "mtc_toll_flow.yaml",
        "mtc-toll-locations": "mtc_toll_locations.yaml",
        "ositran-road-traffic": "ositran_road_traffic.yaml",
        "huancayo-historical": "huancayo_historical_counts.yaml",
    }
    for slug, catalog_adapter in available.items():
        (catalog_dir / catalog_names[slug]).write_text(
            _catalog_text(
                catalog_adapter.get_metadata().to_dict(), catalog_paths[slug]
            ),
            encoding="utf-8",
        )
    return {
        "reports": [str(path) for path in sorted(reports_dir.glob("*.json"))],
        "catalog": [str(path) for path in sorted(catalog_dir.glob("*.yaml"))],
        "join": join,
        "junin": junin,
    }


def ingest(
    adapter: TrafficDatasetPort,
    *,
    dry_run: bool,
    limit: int | None,
) -> dict[str, Any]:
    validation = adapter.validate()
    # Se anotan antes de cualquier rama porque las dos rutas de persistencia
    # comparten estas variables. No altera el flujo: solo fija el tipo declarado.
    run_recorder: SqlAlchemyIngestionRunRecorder | None = None
    run_id: UUID | None = None
    if isinstance(adapter, MtcTollLocationAdapter):
        locations = adapter.get_locations()
        if dry_run:
            return {
                "dataset_id": adapter.get_metadata().dataset_id,
                "dry_run": True,
                "validation": validation,
                "features_read": len(locations),
                "features_inserted": 0,
            }
        if os.getenv("DEMO_REPOSITORY") != "sqlalchemy":
            return {
                "dataset_id": adapter.get_metadata().dataset_id,
                "dry_run": False,
                "persistence": "not_executed_no_postgresql",
                "features_read": len(locations),
                "features_inserted": 0,
            }
        from infrastructure.database.session import SessionFactory

        run_recorder = SqlAlchemyIngestionRunRecorder(SessionFactory)
        run_id = run_recorder.start(adapter.get_metadata().dataset_id)
        location_repository = SqlAlchemyTrafficLocationRepository(SessionFactory)
        location_counts = Counter(
            location_repository.upsert(item) for item in locations
        )
        result = {
            "dataset_id": adapter.get_metadata().dataset_id,
            "dry_run": False,
            "persistence": "postgresql_postgis",
            "features_read": len(locations),
            "features_inserted": location_counts["inserted"],
            "features_updated": location_counts["updated"],
            "invalid_geometries": validation.get("invalid_geometries", 0),
            "crs": validation.get("crs"),
            "bbox": validation.get("bbox"),
        }
        run_recorder.finish(
            run_id,
            {
                "rows_read": len(locations),
                "rows_valid": len(locations),
                "rows_rejected": int(validation.get("invalid_geometries", 0)),
                "rows_inserted": location_counts["inserted"],
                "rows_updated": location_counts["updated"],
            },
        )
        result["ingestion_run_id"] = str(run_id)
        return result
    measurements = list(adapter.stream_measurements(limit=limit))
    if dry_run:
        return {
            "dataset_id": adapter.get_metadata().dataset_id,
            "dry_run": True,
            "validation": validation,
            "normalized_records": len(measurements),
            "rows_inserted": 0,
            "rows_updated": 0,
            "duplicates": 0,
        }
    repository: Any = InMemoryTrafficAggregateRepository()
    persistence = "memory"
    if os.getenv("DEMO_REPOSITORY") == "sqlalchemy":
        from infrastructure.database.session import SessionFactory

        repository = SqlAlchemyTrafficAggregateRepository(SessionFactory)
        persistence = "postgresql"
        run_recorder = SqlAlchemyIngestionRunRecorder(SessionFactory)
        run_id = run_recorder.start(adapter.get_metadata().dataset_id)
    counters: Counter[str] = Counter(repository.upsert(item) for item in measurements)
    result = {
        "dataset_id": adapter.get_metadata().dataset_id,
        "dry_run": False,
        "persistence": persistence,
        "rows_read": validation.get("row_count", len(measurements)),
        "rows_valid": validation.get("rows_valid", len(measurements)),
        "rows_rejected": validation.get("rows_invalid", 0),
        "rows_inserted": counters["inserted"],
        "rows_updated": counters["updated"],
        "duplicates": counters["duplicate"],
    }
    if run_recorder is not None and run_id is not None:
        run_recorder.finish(
            run_id,
            {
                "rows_read": int(result["rows_read"]),
                "rows_valid": int(result["rows_valid"]),
                "rows_rejected": int(result["rows_rejected"]),
                "rows_inserted": counters["inserted"],
                "rows_updated": counters["updated"],
                "duplicates": counters["duplicate"],
            },
        )
        result["ingestion_run_id"] = str(run_id)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI reproducible para Demo Perú")
    sub = parser.add_subparsers(dest="command", required=True)
    datasets_parser = sub.add_parser("datasets")
    actions = datasets_parser.add_subparsers(dest="action", required=True)
    actions.add_parser("discover")
    download_parser = actions.add_parser("download")
    download_parser.add_argument("dataset", choices=DOWNLOADS)
    inspect_parser = actions.add_parser("inspect")
    inspect_parser.add_argument("dataset")
    ingest_parser = actions.add_parser("ingest")
    ingest_parser.add_argument("dataset")
    region_parser = actions.add_parser("find-region")
    region_parser.add_argument("region")
    demo_parser = sub.add_parser("demo-peru")
    demo_parser.add_argument("action", choices=["prepare"])
    for item in (
        parser,
        datasets_parser,
        download_parser,
        inspect_parser,
        ingest_parser,
        demo_parser,
    ):
        item.add_argument("--dry-run", action="store_true")
        item.add_argument("--force", action="store_true")
        item.add_argument("--limit", type=int)
        item.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = data_root()
    available, location_adapter = adapters(root)
    if args.command == "demo-peru":
        for dataset in DOWNLOADS:
            download(dataset, force=args.force, dry_run=args.dry_run)
        result = generate_reports(root) if not args.dry_run else {"dry_run": True}
    elif args.action == "discover":
        result = generate_reports(root)
    elif args.action == "download":
        result = download(args.dataset, force=args.force, dry_run=args.dry_run)
    elif args.action == "inspect":
        if args.dataset not in available:
            raise SystemExit(f"Unknown dataset: {args.dataset}")
        result = available[args.dataset].validate()
    elif args.action == "ingest":
        if args.dataset not in available:
            raise SystemExit(f"Unknown dataset: {args.dataset}")
        result = ingest(available[args.dataset], dry_run=args.dry_run, limit=args.limit)
    elif args.action == "find-region":
        query = PeruDemoQueryService(
            {
                adapter.get_metadata().dataset_id: adapter
                for adapter in available.values()
            },
            location_adapter,
        )
        if normalize_text(args.region) == "junin":
            result = query.junin()
        else:
            result = {
                "region": args.region,
                "geojson_locations": query.locations(args.region),
                "method": "Filtro explícito del campo DEPARTAMEN del GeoJSON.",
            }
    else:  # pragma: no cover
        raise AssertionError("unreachable")
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
