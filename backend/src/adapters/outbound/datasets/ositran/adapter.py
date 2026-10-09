from __future__ import annotations

import calendar
import hashlib
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
)
from application.dto.peru_demo import DatasetMetadata, DatasetScope, TrafficAggregate

DATASET_ID = "ositran_peru_road_traffic"
PROVIDER = "OSITRAN"
SOURCE_PAGE = (
    "https://www.datosabiertos.gob.pe/dataset/tr%C3%A1fico-vehicular-carreteras-"
    "organismo-supervisor-de-la-inversi%C3%B3n-en-infraestructura-de"
)


class OsitranRoadTrafficAdapter:
    _required = {
        "ANIO",
        "MES",
        "ENTIDAD_PRESTADORA",
        "CONCESION",
        "PEAJE",
        "CLASE_VEHICULO",
        "TIPO_VEHICULO",
        "CANTIDAD VEHICULOS",
    }

    def __init__(self, path: Path) -> None:
        self.path = path

    @cached_property
    def _cached_rows(self) -> list[dict[str, str]]:
        return list(read_rows(self.path)) if self.path.exists() else []

    def _rows(self) -> list[dict[str, str]]:
        return self._cached_rows

    @staticmethod
    def _period(row: dict[str, str]) -> str:
        return f"{int(row['ANIO']):04d}-{int(row['MES']):02d}"

    def get_metadata(self) -> DatasetMetadata:
        periods = self.get_available_periods()
        return DatasetMetadata(
            dataset_id=DATASET_ID,
            title="Tráfico Vehicular - CARRETERAS",
            provider=PROVIDER,
            country="Peru",
            source_type="official_open_government_data",
            temporal_granularity="monthly",
            spatial_granularity="toll_unit",
            period_min=periods[0] if periods else None,
            period_max=periods[-1] if periods else None,
            license="Open Data Commons Attribution License",
            source_page=SOURCE_PAGE,
            local_validation=False,
            allowed_uses={
                "demo": True,
                "ingestion_validation": True,
                "dashboard": True,
                "ml_experiment": True,
                "huancayo_local_validation": False,
            },
            limitations=[
                "No incluye un campo de región; cualquier filtro regional exige "
                "una unión verificable con el GeoJSON MTC.",
                "Los conteos de peaje no representan tráfico urbano de la Av. Ferrocarril.",
            ],
        )

    def get_available_periods(self) -> list[str]:
        periods: set[str] = set()
        for row in self._rows():
            try:
                periods.add(self._period(row))
            except (KeyError, ValueError):
                continue
        return sorted(periods)

    def get_locations(self) -> list[dict[str, Any]]:
        unique: dict[str, dict[str, Any]] = {}
        for row in self._rows():
            location_id = normalize_text(row.get("PEAJE", "")).replace(" ", "-")
            unique[location_id] = {
                "dataset_id": DATASET_ID,
                "source_location_id": location_id,
                "name": row.get("PEAJE"),
                "operator": row.get("ENTIDAD_PRESTADORA"),
                "concession": row.get("CONCESION"),
                "region": None,
            }
        return sorted(unique.values(), key=lambda item: str(item["name"]))

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
        if region:
            return
        emitted = 0
        for row in self._rows():
            try:
                period = self._period(row)
                count = parse_integer(row.get("CANTIDAD VEHICULOS", ""))
            except (KeyError, ValueError):
                continue
            row_location_id = normalize_text(row.get("PEAJE", "")).replace(" ", "-")
            category = normalize_text(row.get("TIPO_VEHICULO", "")) or "sin_especificar"
            if start_period and period < start_period:
                continue
            if end_period and period > end_period:
                continue
            if location_id and row_location_id != location_id:
                continue
            if vehicle_category and category != normalize_text(vehicle_category):
                continue
            year, month = (int(part) for part in period.split("-"))
            last_day = calendar.monthrange(year, month)[1]
            source_payload = json.dumps(row, sort_keys=True, ensure_ascii=False)
            source_record_id = hashlib.sha256(
                source_payload.encode("utf-8")
            ).hexdigest()
            yield TrafficAggregate(
                dataset_id=DATASET_ID,
                source_record_id=source_record_id,
                source_provider=PROVIDER,
                source_country="Peru",
                source_region=None,
                source_location_id=row_location_id,
                source_location_name=row.get("PEAJE", ""),
                period_start=date(year, month, 1).isoformat(),
                period_end=date(year, month, last_day).isoformat(),
                temporal_granularity="monthly",
                vehicle_category=category,
                vehicle_count=count,
                dataset_scope=DatasetScope.PERU_OFFICIAL_DEMO,
                metadata={
                    "source_columns": row,
                    "column_mapping": {
                        "PEAJE": "source_location_name",
                        "ANIO+MES": "period_start/period_end",
                        "TIPO_VEHICULO": "vehicle_category",
                        "CANTIDAD VEHICULOS": "vehicle_count",
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
                self._period(row)
                parse_integer(row.get("CANTIDAD VEHICULOS", ""))
            except (KeyError, ValueError):
                invalid += 1
        profile.update(
            {
                "dataset_id": DATASET_ID,
                "valid": not missing_columns and invalid == 0,
                "missing_required_columns": missing_columns,
                "rows_valid": len(rows) - invalid,
                "rows_invalid": invalid,
                "period_min": min(self.get_available_periods(), default=None),
                "period_max": max(self.get_available_periods(), default=None),
                "regions": [],
                "region_field_available": False,
                "locations": len({row["PEAJE"] for row in rows}),
                "vehicle_categories": sorted({row["TIPO_VEHICULO"] for row in rows}),
                "vehicle_classes": sorted({row["CLASE_VEHICULO"] for row in rows}),
                "column_mapping": {
                    "PEAJE": "source_location_name",
                    "ANIO+MES": "period_start/period_end",
                    "TIPO_VEHICULO": "vehicle_category",
                    "CANTIDAD VEHICULOS": "vehicle_count",
                },
            }
        )
        return profile

    def get_source_name(self) -> str:
        return PROVIDER
