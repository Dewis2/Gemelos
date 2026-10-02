from __future__ import annotations

import threading
import time
from collections import defaultdict
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from application.dto.peru_demo import (
    DatasetScope,
    DigitalTwinDemoState,
    TrafficAggregate,
    TrafficLocation,
)
from application.ports.outbound import (
    EventPublisherPort,
    TrafficAggregateRepositoryPort,
    TrafficDatasetPort,
)
from application.services.traffic_scope import TrafficScopeResolver


class PeruDemoQueryService:
    def __init__(
        self,
        datasets: Mapping[str, TrafficDatasetPort],
        location_dataset: TrafficDatasetPort,
        scopes: TrafficScopeResolver | None = None,
    ) -> None:
        self._datasets = dict(datasets)
        self._location_dataset = location_dataset
        # Contexto Strategy. Puede inyectarse otro resolver para cambiar la politica.
        self._scopes = TrafficScopeResolver() if scopes is None else scopes
        self._repository: TrafficAggregateRepositoryPort | None = None

    def set_repository(self, repository: TrafficAggregateRepositoryPort) -> None:
        self._repository = repository

    def list_datasets(self) -> list[dict[str, Any]]:
        return [adapter.get_metadata().to_dict() for adapter in self._datasets.values()]

    def get_dataset(self, dataset_id: str) -> dict[str, Any] | None:
        adapter = self._datasets.get(dataset_id)
        return adapter.get_metadata().to_dict() if adapter else None

    def get_adapter(self, dataset_id: str) -> TrafficDatasetPort | None:
        return self._datasets.get(dataset_id)

    def locations(self, region: str | None = None) -> list[dict[str, Any]]:
        latest: dict[str, TrafficLocation] = {}
        for item in self._location_dataset.get_locations():
            if not isinstance(item, TrafficLocation):
                continue
            if region and (item.region or "").casefold() != region.casefold():
                continue
            previous = latest.get(item.source_location_id)
            previous_cut = str(previous.properties.get("FECCORTE", "")) if previous else ""
            current_cut = str(item.properties.get("FECCORTE", ""))
            if previous is None or current_cut >= previous_cut:
                latest[item.source_location_id] = item
        return [item.to_dict() for item in sorted(latest.values(), key=lambda value: value.name)]

    def traffic(
        self,
        dataset_id: str,
        *,
        region: str | None = None,
        location_id: str | None = None,
        start_period: str | None = None,
        end_period: str | None = None,
        vehicle_category: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        adapter = self._datasets[dataset_id]
        if self._repository is None:
            measurements = list(
                adapter.stream_measurements(
                    region=region,
                    location_id=location_id,
                    start_period=start_period,
                    end_period=end_period,
                    vehicle_category=vehicle_category,
                )
            )
        else:
            measurements = [
                item
                for item in self._repository.list_by_dataset(dataset_id)
                if (not region or (item.source_region or "").casefold() == region.casefold())
                and (not location_id or item.source_location_id == location_id)
                and (not start_period or item.period_start[: len(start_period)] >= start_period)
                and (not end_period or item.period_start[: len(end_period)] <= end_period)
                and (not vehicle_category or item.vehicle_category == vehicle_category)
            ]
            measurements.sort(key=lambda item: (item.period_start, item.natural_key))
        category_totals: dict[str, int] = defaultdict(int)
        series: dict[str, int] = defaultdict(int)
        contains_total = any(item.vehicle_category == "total" for item in measurements)
        for item in measurements:
            category_totals[item.vehicle_category] += item.vehicle_count
            if not contains_total or item.vehicle_category == "total":
                series[item.period_start[:7]] += item.vehicle_count
        total = category_totals.get("total", sum(category_totals.values()))
        return {
            "dataset": adapter.get_metadata().to_dict(),
            "filters": {
                "region": region,
                "location_id": location_id,
                "start_period": start_period,
                "end_period": end_period,
                "vehicle_category": vehicle_category,
            },
            "record_count": len(measurements),
            "records_returned": min(len(measurements), limit),
            "total_vehicles": total,
            "category_totals": dict(sorted(category_totals.items())),
            "series": [
                {"period": period, "vehicle_count": value}
                for period, value in sorted(series.items())
            ],
            "records": [item.to_dict() for item in measurements[:limit]],
            "source_label": f"Fuente: {adapter.get_source_name()}",
            # Strategy: la politica de aviso la decide la estrategia aplicable al
            # conjunto de datos, no un condicional dentro de este servicio.
            "warning": self._scopes.resolve(dataset_id).warning(),
        }

    def junin(self) -> dict[str, Any]:
        flow = self._datasets.get("mtc_peru_toll_flow")
        flow_locations = flow.get_locations() if flow else []
        matched_flow = [
            item
            for item in flow_locations
            if isinstance(item, dict) and str(item.get("region", "")).casefold() == "junín"
        ]
        geo_locations = self.locations("JUNIN")
        flow_by_code = {str(item["source_location_id"]): item for item in matched_flow}
        geo_by_code = {str(item["source_location_id"]): item for item in geo_locations}
        matched_units = [
            {
                "source_location_id": code,
                "flow_name": flow_by_code.get(code, {}).get("name"),
                "geojson_name": geo_by_code.get(code, {}).get("name"),
            }
            for code in sorted(set(flow_by_code) | set(geo_by_code))
        ]
        return {
            "junin_filter_available": bool(matched_flow or geo_locations),
            "matched_records": (
                len(list(flow.stream_measurements(region="JUNIN", vehicle_category="total")))
                if flow
                else 0
            ),
            "matched_toll_units": matched_units,
            "flow_locations": matched_flow,
            "geojson_locations": geo_locations,
            "method": (
                "Filtro explícito DEPARTAMENTO/DEPARTAMEN, normalizado sin distinguir mayúsculas."
            ),
            "limitations": [
                "OSITRAN no contiene región; sus registros solo pueden asociarse "
                "mediante un join verificable con el GeoJSON.",
                "La presencia en Junín no implica pertenencia al corredor urbano "
                "de la Av. Ferrocarril.",
            ],
        }

    def comparison(self) -> dict[str, Any]:
        return {
            "comparable_as_same_dataset": False,
            "national_demo": [
                item
                for item in self.list_datasets()
                if item["dataset_id"] != "huancayo_historical_counts_2013"
            ],
            "local_historical_reference": self.get_dataset("huancayo_historical_counts_2013"),
            "local_current_2026": {
                "available": False,
                "message": (
                    "No existen datos locales actuales de la Av. Ferrocarril en el repositorio."
                ),
            },
            "warning": (
                "Los datos nacionales de peaje, los aforos de Huancayo 2013 y "
                "los datos locales actuales son ámbitos separados."
            ),
        }


class HistoricalReplayService:
    _topics = {
        "mtc_peru_toll_flow": "demo/peru/mtc/traffic",
        "ositran_peru_road_traffic": "demo/peru/ositran/traffic",
        "huancayo_historical_counts_2013": "huancayo/ferrocarril/traffic",
    }

    def __init__(
        self,
        query: PeruDemoQueryService,
        repository: TrafficAggregateRepositoryPort,
        publisher: EventPublisherPort,
        *,
        mqtt_enabled: bool,
    ) -> None:
        self._query = query
        self._repository = repository
        self._publisher = publisher
        self._mqtt_enabled = mqtt_enabled
        self._state = DigitalTwinDemoState()
        self._records: list[TrafficAggregate] = []
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None

    def start(
        self,
        dataset_id: str,
        *,
        start_period: str | None,
        end_period: str | None,
        location_id: str | None,
        speed_factor: int,
        limit: int,
    ) -> dict[str, Any]:
        if speed_factor not in {1, 5, 10, 60}:
            raise ValueError("speed_factor must be one of 1, 5, 10 or 60")
        adapter = self._query.get_adapter(dataset_id)
        if adapter is None:
            raise KeyError(dataset_id)
        report = adapter.validate()
        if not report.get("valid"):
            raise ValueError(f"Dataset validation failed: {report}")
        records = list(
            adapter.stream_measurements(
                start_period=start_period,
                end_period=end_period,
                location_id=location_id,
                limit=limit,
            )
        )
        if not records:
            raise ValueError("No records match the replay filters")
        self.stop()
        with self._lock:
            self._records = records
            self._stop.clear()
            self._pause.clear()
            self._state = DigitalTwinDemoState(
                status="running",
                current_dataset=dataset_id,
                source_provider=adapter.get_source_name(),
                replay_speed=speed_factor,
                replay_total=len(records),
                technical_status={
                    "dataset": "loaded",
                    "parser": "validated",
                    "repository": "pending",
                    "mqtt": "pending" if self._mqtt_enabled else "disabled",
                    "digital_twin_core": "pending",
                    "api": "ready",
                },
            )
            self._state.add_event("dataset", f"{len(records)} registros cargados para replay")
            self._state.add_event("parser", "Validación del esquema completada")
        self._thread = threading.Thread(target=self._run, daemon=True, name="peru-demo-replay")
        self._thread.start()
        return self.status()

    def _run(self) -> None:
        for index, item in enumerate(self._records, start=1):
            if self._stop.is_set():
                break
            while self._pause.is_set() and not self._stop.is_set():
                time.sleep(0.05)
            with self._lock:
                result = self._repository.upsert(item)
                self._state.technical_status["repository"] = result
                self._state.add_event("repository", f"Registro {result}: {item.natural_key}")
                emitted_at = datetime.now(UTC).isoformat()
                payload = {
                    "dataset_id": item.dataset_id,
                    "provider": item.source_provider,
                    "country": item.source_country,
                    "location_id": item.source_location_id,
                    "historical_period": item.period_start[:7],
                    "original_period": {
                        "start": item.period_start,
                        "end": item.period_end,
                        "granularity": item.temporal_granularity,
                    },
                    "replay_emitted_at": emitted_at,
                    "replay_speed": self._state.replay_speed,
                    "event_type": "historical_traffic_replay",
                    "data": {
                        "vehicle_category": item.vehicle_category,
                        "vehicle_count": item.vehicle_count,
                    },
                }
                try:
                    self._publisher.publish(self._topics[item.dataset_id], payload)
                    if self._mqtt_enabled:
                        self._state.technical_status["mqtt"] = "published"
                        self._state.add_event(
                            "mqtt", f"Evento publicado en {self._topics[item.dataset_id]}"
                        )
                    else:
                        self._state.add_event(
                            "mqtt", "MQTT deshabilitado; evento registrado localmente"
                        )
                except Exception as exc:  # pragma: no cover - depends on broker
                    self._state.technical_status["mqtt"] = "error"
                    self._state.add_event("mqtt", f"Error de publicación: {exc}")
                if self._state.current_historical_period != item.period_start[:7]:
                    self._state.vehicle_categories = {}
                self._state.current_location = item.source_location_name
                self._state.current_historical_period = item.period_start[:7]
                self._state.vehicle_count = item.vehicle_count
                self._state.vehicle_categories[item.vehicle_category] = item.vehicle_count
                self._state.last_update = emitted_at
                self._state.replay_position = index
                self._state.technical_status["digital_twin_core"] = "updated"
                self._state.add_event("digital_twin_core", "Estado de demostración actualizado")
                if item.dataset_scope == DatasetScope.PERU_OFFICIAL_DEMO:
                    try:
                        self._publisher.publish(
                            "demo/peru/digital-twin/state",
                            {
                                "dataset_id": item.dataset_id,
                                "provider": item.source_provider,
                                "country": item.source_country,
                                "location_id": item.source_location_id,
                                "historical_period": item.period_start[:7],
                                "replay_emitted_at": emitted_at,
                                "event_type": "digital_twin_demo_state_updated",
                                "data": {
                                    "vehicle_count": item.vehicle_count,
                                    "vehicle_categories": dict(self._state.vehicle_categories),
                                },
                            },
                        )
                    except Exception as exc:  # pragma: no cover - depends on broker
                        self._state.technical_status["mqtt"] = "error"
                        self._state.add_event("mqtt", f"Error de estado: {exc}")
            time.sleep(max(0.05, 1 / (self._state.replay_speed or 1)))
        with self._lock:
            if not self._stop.is_set():
                self._state.status = "completed"
                self._state.add_event("replay", "Reproducción histórica completada")

    def pause(self) -> dict[str, Any]:
        with self._lock:
            if self._state.status == "running":
                self._pause.set()
                self._state.status = "paused"
                self._state.add_event("replay", "Reproducción pausada")
            return self._state.to_dict()

    def resume(self) -> dict[str, Any]:
        with self._lock:
            if self._state.status == "paused":
                self._pause.clear()
                self._state.status = "running"
                self._state.add_event("replay", "Reproducción reanudada")
            return self._state.to_dict()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join()
        with self._lock:
            if self._state.status in {"running", "paused"}:
                self._state.status = "stopped"
                self._state.add_event("replay", "Reproducción detenida")
            return self._state.to_dict()

    def reset(self) -> dict[str, Any]:
        self.stop()
        with self._lock:
            self._records = []
            self._state = DigitalTwinDemoState()
            return self._state.to_dict()

    def mark_api_served(self) -> None:
        with self._lock:
            self._state.technical_status["api"] = "served"

    def status(self) -> dict[str, Any]:
        with self._lock:
            return self._state.to_dict()
