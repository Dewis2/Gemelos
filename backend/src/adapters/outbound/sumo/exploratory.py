"""Run the three versioned OSM/SUMO experiments without accepting user paths."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from statistics import mean
from threading import Lock
from typing import Any

PERIODS = {"baja": 8, "normal": 4, "alta": 2}


class ExploratorySumoError(RuntimeError):
    pass


class ExploratorySumoBusyError(ExploratorySumoError):
    pass


class ExploratorySumoRunner:
    def __init__(
        self, assets_root: Path, report_path: Path, binary: str = "sumo"
    ) -> None:
        self.assets_root = assets_root
        self.report_path = report_path
        self.binary = binary
        self._run_lock = Lock()

    def report(self) -> dict[str, Any]:
        return json.loads(self.report_path.read_text(encoding="utf-8"))

    def _binary_path(self) -> str:
        found = shutil.which(self.binary)
        if found:
            return found
        try:
            import sumo  # type: ignore[import-not-found,import-untyped]

            candidate = (
                Path(sumo.SUMO_HOME)
                / "bin"
                / ("sumo.exe" if os.name == "nt" else "sumo")
            )
            if candidate.is_file():
                return str(candidate)
        except ImportError:
            pass
        raise ExploratorySumoError("SUMO no está instalado en el servidor")

    def run(self, level: str) -> dict[str, Any]:
        if level not in PERIODS:
            raise ValueError("Solo se admiten los escenarios baja, normal y alta")
        if not self._run_lock.acquire(blocking=False):
            raise ExploratorySumoBusyError("Ya hay una ejecución SUMO en curso")
        try:
            return self._run_once(level)
        finally:
            self._run_lock.release()

    def _run_once(self, level: str) -> dict[str, Any]:
        report = self.report()
        period = PERIODS[level]
        config = self.assets_root / "configuration" / f"osm-{level}.sumocfg"
        network = self.assets_root / "networks" / "huancayo-exploratory.net.xml"
        routes = self.assets_root / "routes" / f"osm-{period}.rou.xml"
        for file, expected_hash in (
            (network, report["network"]["network_sha256"]),
            (routes, report["scenarios"][level]["route_sha256"]),
        ):
            if (
                not file.is_file()
                or hashlib.sha256(file.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                != expected_hash
            ):
                raise ExploratorySumoError(
                    f"Activo SUMO ausente o modificado: {file.name}"
                )
        if not config.is_file():
            raise ExploratorySumoError(f"Configuración SUMO ausente: {config.name}")
        with tempfile.TemporaryDirectory(prefix="gemelos-sumo-") as temporary:
            output = Path(temporary)
            trip_file = output / "tripinfo.xml"
            summary_file = output / "summary.xml"
            command = [
                self._binary_path(),
                "-c",
                str(config),
                "--seed",
                str(report["software"]["seed"]),
                "--tripinfo-output",
                str(trip_file),
                "--summary-output",
                str(summary_file),
                "--no-step-log",
                "true",
            ]
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=90,
                    check=False,
                    cwd=self.assets_root,
                )
            except subprocess.TimeoutExpired as exc:
                raise ExploratorySumoError(
                    "SUMO superó el límite de 90 segundos"
                ) from exc
            if completed.returncode:
                raise ExploratorySumoError(
                    f"SUMO terminó con código {completed.returncode}: {completed.stderr[-500:]}"
                )
            trips = ET.parse(trip_file).getroot().findall("tripinfo")
            steps = ET.parse(summary_file).getroot().findall("step")
            if not steps:
                raise ExploratorySumoError("SUMO no produjo resumen de pasos")
            last = steps[-1]
            durations = [float(trip.get("duration", "0")) for trip in trips]
            waits = [float(trip.get("waitingTime", "0")) for trip in trips]
            losses = [float(trip.get("timeLoss", "0")) for trip in trips]
            speeds = [
                3.6 * float(trip.get("routeLength", "0")) / duration
                for trip, duration in zip(trips, durations, strict=True)
                if duration > 0
            ]
            return {
                "study_type": "exploratory_uncalibrated",
                "level": level,
                "source": "OpenStreetMap contributors (ODbL 1.0)",
                "network_sha256": report["network"]["network_sha256"],
                "route_sha256": report["scenarios"][level]["route_sha256"],
                "seed": report["software"]["seed"],
                "synthetic_departure_interval_seconds": period,
                "routes_generated": len(ET.parse(routes).getroot().findall("vehicle")),
                "vehicles_inserted": int(last.get("inserted", "0")),
                "vehicles_arrived": int(last.get("arrived", "0")),
                "vehicles_remaining": int(last.get("running", "0"))
                + int(last.get("waiting", "0")),
                "mean_trip_duration_seconds": (
                    round(mean(durations), 2) if durations else None
                ),
                "mean_waiting_seconds": round(mean(waits), 2) if waits else None,
                "mean_time_loss_seconds": round(mean(losses), 2) if losses else None,
                "mean_trip_speed_kmh": round(mean(speeds), 2) if speeds else None,
            }
