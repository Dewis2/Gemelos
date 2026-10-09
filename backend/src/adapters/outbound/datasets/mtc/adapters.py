from __future__ import annotations

import calendar
import json
from collections.abc import Iterable
from datetime import date
from functools import cached_property
from pathlib import Path
from typing import Any

from adapters.outbound.datasets.common import (
    file_profile,
    normalize_text,
    parse_integer,
    read_rows,
    sha256,
)
from application.dto.peru_demo import (
    DatasetMetadata,
    DatasetScope,
    TrafficAggregate,
    TrafficLocation,
)

FLOW_DATASET_ID = "mtc_peru_toll_flow"
LOCATION_DATASET_ID = "mtc_peru_toll_locations"
MTC_PROVIDER = "Ministerio de Transportes y Comunicaciones - MTC"
FLOW_SOURCE_PAGE = (
    "https://www.datosabiertos.gob.pe/dataset/flujo-vehicular-registrado-en-las-"
    "unidades-de-peaje-de-la-red-vial-nacional-2014-%E2%80%93-2026-i"
)
LOCATION_SOURCE_PAGE = (
    "https://www.datosabiertos.gob.pe/dataset/unidades-de-peaje-de-la-red-vial-"
    "nacional-2024-%E2%80%93-2025-ii-trimestre-ministerio-de-transportes"
)


def _month_bounds(period: str) -> tuple[str, str]:
    year, month = int(period[:4]), int(period[4:6])
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1).isoformat(), date(year, month, last_day).isoformat()


class MtcTollFlowAdapter:
    _category_columns = {
        "total": "VEH_TOTAL",
        "ligeros": "VEH_LIGEROS_TOTAL",
        "pesados": "VEH_PESADOS_TOTAL",
    }
    _required = {
        "ADMINIST",
        "CODIGO_PEAJE",
        "DEPARTAMENTO",
        "NOMBRE_PEAJE",
        "VEH_TOTAL",
        "ANIO",
        "MES",
        "PERIODO",
    }

    def __init__(self, path: Path) -> None:
        self.path = path

    @cached_property
    def _cached_rows(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        return list(read_rows(self.path))

    def _rows(self) -> list[dict[str, str]]:
        return self._cached_rows

    def get_metadata(self) -> DatasetMetadata:
        periods = self.get_available_periods()
        return DatasetMetadata(
            dataset_id=FLOW_DATASET_ID,
            title="Flujo vehicular registrado en las unidades de peaje de la Red Vial Nacional",
            provider=MTC_PROVIDER,
            country="Peru",
            source_type="official_open_government_data",
            temporal_granularity="monthly",
            spatial_granularity="toll_unit",
            period_min=periods[0] if periods else None,
            period_max=periods[-1] if periods else None,
            license="License Not Specified",
            source_page=FLOW_SOURCE_PAGE,
            local_validation=False,
            allowed_uses={
                "demo": True,
                "ingestion_validation": True,
                "dashboard": True,
                "ml_experiment": True,
                "huancayo_local_validation": False,
            },
            limitations=[
                "Los conteos de peaje no representan tráfico urbano de la Av. Ferrocarril.",
                "La licencia no está especificada en la ficha del catálogo; "
                "el archivo raw no se redistribuye.",
            ],
        )

    def get_available_periods(self) -> list[str]:
        values = {row.get("PERIODO", "") for row in self._rows()}
        return sorted(f"{item[:4]}-{item[4:6]}" for item in values if len(item) == 6)

    def get_locations(self) -> list[dict[str, Any]]:
        unique: dict[str, dict[str, Any]] = {}
        for row in self._rows():
            code = row.get("CODIGO_PEAJE", "")
            unique[code] = {
                "dataset_id": FLOW_DATASET_ID,
                "source_location_id": code,
                "name": row.get("NOMBRE_PEAJE"),
                "region": row.get("DEPARTAMENTO"),
                "administration": row.get("ADMINIST"),
            }
        return sorted(
            unique.values(), key=lambda item: (str(item["region"]), str(item["name"]))
        )

    def stream_measurements(
        self,
        *,
        start_period: str | None = None,
        end_period: str | None = None,
        location_id: str | None = None,
        region: str | None = None,
        vehicle_category: str | None = None,
        limit: int | None = None,
    ) -> Iterable[TrafficAggregate]:
        normalized_region = normalize_text(region) if region else None
        categories = (
            {vehicle_category: self._category_columns[vehicle_category]}
            if vehicle_category in self._category_columns
            else self._category_columns
        )
        emitted = 0
        for row in self._rows():
            period = row.get("PERIODO", "")
            display_period = (
                f"{period[:4]}-{period[4:6]}" if len(period) == 6 else period
            )
            if start_period and display_period < start_period:
                continue
            if end_period and display_period > end_period:
                continue
            if location_id and row.get("CODIGO_PEAJE") != location_id:
                continue
            if (
                normalized_region
                and normalize_text(row.get("DEPARTAMENTO", "")) != normalized_region
            ):
                continue
            if len(period) != 6:
                continue
            period_start, period_end = _month_bounds(period)
            for category, column in categories.items():
                try:
                    count = parse_integer(row.get(column, ""))
                except ValueError:
                    continue
                yield TrafficAggregate(
                    dataset_id=FLOW_DATASET_ID,
                    source_record_id=f"{row.get('CODIGO_PEAJE')}:{period}",
                    source_provider=MTC_PROVIDER,
                    source_country="Peru",
                    source_region=row.get("DEPARTAMENTO") or None,
                    source_location_id=row.get("CODIGO_PEAJE", ""),
                    source_location_name=row.get("NOMBRE_PEAJE", ""),
                    period_start=period_start,
                    period_end=period_end,
                    temporal_granularity="monthly",
                    vehicle_category=category,
                    vehicle_count=count,
                    dataset_scope=DatasetScope.PERU_OFFICIAL_DEMO,
                    metadata={
                        "source_columns": row,
                        "column_mapping": {
                            "CODIGO_PEAJE": "source_location_id",
                            "NOMBRE_PEAJE": "source_location_name",
                            "DEPARTAMENTO": "source_region",
                            "PERIODO": "period_start/period_end",
                            column: "vehicle_count",
                        },
                    },
                )
                emitted += 1
                if limit is not None and emitted >= limit:
                    return

    def validate(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "valid": False,
                "error": "raw file not found",
                "path": str(self.path),
            }
        profile = file_profile(self.path)
        rows = self._rows()
        missing_columns = sorted(self._required.difference(profile["columns"]))
        invalid = 0
        for row in rows:
            try:
                parse_integer(row.get("VEH_TOTAL", ""))
                if len(row.get("PERIODO", "")) != 6:
                    raise ValueError("invalid period")
            except ValueError:
                invalid += 1
        profile.update(
            {
                "dataset_id": FLOW_DATASET_ID,
                "valid": not missing_columns and invalid == 0,
                "missing_required_columns": missing_columns,
                "rows_valid": len(rows) - invalid,
                "rows_invalid": invalid,
                "period_min": min(self.get_available_periods(), default=None),
                "period_max": max(self.get_available_periods(), default=None),
                "regions": sorted({row["DEPARTAMENTO"] for row in rows}),
                "locations": len({row["CODIGO_PEAJE"] for row in rows}),
                "vehicle_categories": list(self._category_columns),
                "column_mapping": {
                    "CODIGO_PEAJE": "source_location_id",
                    "NOMBRE_PEAJE": "source_location_name",
                    "DEPARTAMENTO": "source_region",
                    "PERIODO": "period_start/period_end",
                    "VEH_TOTAL": "vehicle_count (total)",
                    "VEH_LIGEROS_TOTAL": "vehicle_count (ligeros)",
                    "VEH_PESADOS_TOTAL": "vehicle_count (pesados)",
                },
            }
        )
        return profile

    def get_source_name(self) -> str:
        return MTC_PROVIDER


class MtcTollLocationAdapter:
    def __init__(self, path: Path) -> None:
        self.path = path

    @cached_property
    def _cached_document(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"type": "FeatureCollection", "features": []}
        raw = self.path.read_bytes()
        for encoding in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                return json.loads(raw.decode(encoding))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        raise ValueError(f"Cannot decode GeoJSON: {self.path}")

    def _document(self) -> dict[str, Any]:
        return self._cached_document

    def get_metadata(self) -> DatasetMetadata:
        periods = self.get_available_periods()
        return DatasetMetadata(
            dataset_id=LOCATION_DATASET_ID,
            title="Unidades de Peaje de la Red Vial Nacional 2024-2025",
            provider=MTC_PROVIDER,
            country="Peru",
            source_type="official_open_government_data",
            temporal_granularity="snapshot",
            spatial_granularity="point",
            period_min=periods[0] if periods else None,
            period_max=periods[-1] if periods else None,
            license="License Not Specified (catalog); ODC Attribution stated in metadata PDF",
            source_page=LOCATION_SOURCE_PAGE,
            local_validation=False,
            allowed_uses={
                "demo": True,
                "ingestion_validation": True,
                "dashboard": True,
                "ml_experiment": False,
                "huancayo_local_validation": False,
            },
            limitations=[
                "Existe una discrepancia de licencia entre la ficha del catálogo "
                "y el PDF de metadatos.",
                "No se redistribuye el archivo raw hasta aclarar sus condiciones.",
            ],
        )

    def get_available_periods(self) -> list[str]:
        values: set[str] = set()
        for feature in self._document().get("features", []):
            raw = str(feature.get("properties", {}).get("FECCORTE", ""))
            if len(raw) == 8 and raw.isdigit():
                values.add(f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}")
        return sorted(values)

    def get_locations(self) -> list[TrafficLocation]:
        document = self._document()
        crs = document.get("crs", {}).get("properties", {}).get("name", "CRS84")
        locations: list[TrafficLocation] = []
        for feature in document.get("features", []):
            properties = feature.get("properties", {})
            geometry = feature.get("geometry") or {}
            coordinates = geometry.get("coordinates", [])
            if geometry.get("type") != "Point" or len(coordinates) < 2:
                continue
            locations.append(
                TrafficLocation(
                    dataset_id=LOCATION_DATASET_ID,
                    source_location_id=str(
                        properties.get("CODPEAJE") or properties.get("IDPEAJE")
                    ),
                    name=str(properties.get("NOMBRE") or ""),
                    location_type="unidad_de_peaje",
                    operator=properties.get("ADMINIST"),
                    status=properties.get("ESTADO"),
                    region=properties.get("DEPARTAMEN"),
                    province=properties.get("PROVINCIA"),
                    district=properties.get("DISTRITO"),
                    longitude=float(coordinates[0]),
                    latitude=float(coordinates[1]),
                    crs=str(crs),
                    properties=properties,
                )
            )
        return locations

    def stream_measurements(
        self,
        *,
        start_period: str | None = None,
        end_period: str | None = None,
        location_id: str | None = None,
        region: str | None = None,
        vehicle_category: str | None = None,
        limit: int | None = None,
    ) -> Iterable[TrafficAggregate]:
        return ()

    def validate(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "valid": False,
                "error": "raw file not found",
                "path": str(self.path),
            }
        document = self._document()
        features = document.get("features", [])
        valid_locations = self.get_locations()
        coordinates = [(item.longitude, item.latitude) for item in valid_locations]
        crs = document.get("crs", {}).get("properties", {}).get("name", "CRS84")
        return {
            "dataset_id": LOCATION_DATASET_ID,
            "valid": document.get("type") == "FeatureCollection"
            and len(features) == len(valid_locations),
            "path": str(self.path),
            "checksum_sha256": sha256(self.path),
            "features_read": len(features),
            "features_insertable": len(valid_locations),
            "invalid_geometries": len(features) - len(valid_locations),
            "crs": crs,
            "bbox": (
                [
                    min(point[0] for point in coordinates),
                    min(point[1] for point in coordinates),
                    max(point[0] for point in coordinates),
                    max(point[1] for point in coordinates),
                ]
                if coordinates
                else None
            ),
            "columns": sorted(
                {
                    key
                    for feature in features
                    for key in feature.get("properties", {}).keys()
                }
            ),
            "period_min": min(self.get_available_periods(), default=None),
            "period_max": max(self.get_available_periods(), default=None),
            "regions": sorted({item.region for item in valid_locations if item.region}),
            "locations": len(valid_locations),
        }

    def get_source_name(self) -> str:
        return MTC_PROVIDER
