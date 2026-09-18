from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from functools import cached_property
from pathlib import Path
from typing import Any

from adapters.outbound.datasets.common import file_profile, normalize_text, parse_integer, read_rows
from application.dto.peru_demo import DatasetMetadata, DatasetScope, TrafficAggregate

DATASET_ID = "huancayo_historical_counts_2013"
PROVIDER = "Municipalidad Provincial de Huancayo"


class HuancayoHistoricalAdapter:
    def __init__(self, path: Path) -> None:
        self.path = path

    @cached_property
    def _cached_rows(self) -> list[dict[str, str]]:
        return list(read_rows(self.path)) if self.path.exists() else []

    def _rows(self) -> list[dict[str, str]]:
        return self._cached_rows

    def get_metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            dataset_id=DATASET_ID,
            title="Aforos históricos del Plan Regulador de Rutas de Transporte Urbano",
            provider=PROVIDER,
            country="Peru",
            source_type="historical_local_reference",
            temporal_granularity="day_period",
            spatial_granularity="count_point",
            period_min="2013",
            period_max="2013",
            license="NO DETERMINADO",
            source_page="https://documentos.munihuancayo.gob.pe/documentos/servicios_publica/transito_transporte/plan_regulador_rutas.pdf",
            local_validation=False,
            allowed_uses={
                "demo": True,
                "ingestion_validation": True,
                "dashboard": True,
                "ml_experiment": False,
                "huancayo_local_validation": False,
            },
            limitations=[
                "Los nueve registros son aforos históricos de 2013 y no representan "
                "tráfico actual de 2026.",
                "No se interpolan los periodos mañana, mediodía y noche.",
            ],
        )

    def get_available_periods(self) -> list[str]:
        order = {"morning": 0, "midday": 1, "night": 2}
        return sorted(
            {row.get("period", "") for row in self._rows()},
            key=lambda value: order.get(value, 99),
        )

    def get_locations(self) -> list[dict[str, Any]]:
        return [
            {
                "dataset_id": DATASET_ID,
                "source_location_id": point,
                "name": point,
                "region": "Junín",
                "year": 2013,
                "historical": True,
            }
            for point in sorted({row.get("point", "") for row in self._rows()})
        ]

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
        if region and normalize_text(region) != "junin":
            return
        emitted = 0
        for row in self._rows():
            if location_id and row.get("point") != location_id:
                continue
            yield TrafficAggregate(
                dataset_id=DATASET_ID,
                source_record_id=f"{row.get('point')}:{row.get('period')}:2013",
                source_provider=PROVIDER,
                source_country="Peru",
                source_region="Junín",
                source_location_id=row.get("point", ""),
                source_location_name=row.get("point", ""),
                period_start=date(2013, 1, 1).isoformat(),
                period_end=date(2013, 12, 31).isoformat(),
                temporal_granularity="day_period",
                vehicle_category="all_vehicles",
                vehicle_count=parse_integer(row.get("vehicles", "")),
                dataset_scope=DatasetScope.HUANCAYO_LOCAL_HISTORICAL,
                metadata={
                    "historical": True,
                    "year": 2013,
                    "day_period": row.get("period"),
                    "data_classification": row.get("data_classification"),
                    "source": row.get("source"),
                },
            )
            emitted += 1
            if limit is not None and emitted >= limit:
                return

    def validate(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"valid": False, "error": "reference file not found", "path": str(self.path)}
        profile = file_profile(self.path)
        rows = self._rows()
        valid_rows = [
            row
            for row in rows
            if row.get("dataset_id") == DATASET_ID
            and row.get("year") == "2013"
            and row.get("data_classification") == "historical_local_reference"
        ]
        profile.update(
            {
                "dataset_id": DATASET_ID,
                "valid": len(valid_rows) == len(rows) == 9,
                "rows_valid": len(valid_rows),
                "rows_invalid": len(rows) - len(valid_rows),
                "period_min": "2013",
                "period_max": "2013",
                "locations": sorted({row.get("point", "") for row in rows}),
                "historical": True,
            }
        )
        return profile

    def get_source_name(self) -> str:
        return PROVIDER
