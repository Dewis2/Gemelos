"""Build and run a reproducible, uncalibrated SUMO study from an OSM snapshot.

This command never reads the municipal counts or writes to PostgreSQL. Its trips
are synthetic and its outputs must not be presented as observed Huancayo traffic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUMO_DIR = ROOT / "simulation" / "sumo"
OSM_FILE = SUMO_DIR / "networks" / "huancayo-ferrocarril-osm-20261113.osm.xml"
NET_FILE = SUMO_DIR / "networks" / "huancayo-exploratory.net.xml"
FRONTEND_DATA = ROOT / "frontend" / "src" / "data"
SEED = 30167
DEPARTURE_END = 900
SIMULATION_END = 1800
SCENARIOS = {"baja": 8, "normal": 4, "alta": 2}
SOURCE_URL = (
    "https://api.openstreetmap.org/api/0.6/map?bbox=-75.220,-12.073,-75.200,-12.060"
)


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def remove_generated_comments(path: Path) -> None:
    """Drop SUMO's timestamp and local-path comments from committed XML artifacts."""
    content = path.read_bytes()
    path.write_bytes(re.sub(rb"<!--.*?-->\s*", b"", content, flags=re.DOTALL))


def sumo_home() -> Path:
    configured = os.getenv("SUMO_HOME")
    if configured:
        return Path(configured)
    try:
        import sumo  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("Instale eclipse-sumo==1.28.0 o defina SUMO_HOME") from exc
    return Path(sumo.SUMO_HOME)


def execute(command: list[str], environment: dict[str, str], log: Path) -> None:
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    with log.open("a", encoding="utf-8") as stream:
        stream.write("\n$ " + " ".join(command) + "\n")
        stream.write(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(
            f"Falló {Path(command[0]).name} (código {result.returncode}); revise {log}"
        )


def write_config(scenario: str, route_file: Path) -> Path:
    config = SUMO_DIR / "configuration" / f"osm-{scenario}.sumocfg"
    root = ET.Element("configuration")
    inputs = ET.SubElement(root, "input")
    ET.SubElement(inputs, "net-file", value=os.path.relpath(NET_FILE, config.parent))
    ET.SubElement(
        inputs, "route-files", value=os.path.relpath(route_file, config.parent)
    )
    times = ET.SubElement(root, "time")
    ET.SubElement(times, "begin", value="0")
    ET.SubElement(times, "end", value=str(SIMULATION_END))
    config.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    return config


def network_features(home: Path) -> tuple[dict[str, Any], dict[str, int]]:
    sys.path.insert(0, str(home / "tools"))
    import sumolib  # type: ignore[import-not-found]

    network = sumolib.net.readNet(str(NET_FILE))
    features: list[dict[str, Any]] = []
    corridor_edges = 0
    for edge in network.getEdges():
        if not edge.allows("passenger"):
            continue
        shape = edge.getShape()
        if len(shape) < 2:
            continue
        name = edge.getName()
        corridor = "ferrocarril" in name.casefold()
        corridor_edges += int(corridor)
        coordinates = [list(network.convertXY2LonLat(x, y)) for x, y in shape]
        features.append(
            {
                "type": "Feature",
                "properties": {"name": name, "corridor": corridor},
                "geometry": {"type": "LineString", "coordinates": coordinates},
            }
        )
    if corridor_edges == 0:
        raise RuntimeError(
            "La red importada no contiene vías llamadas Avenida Ferrocarril"
        )
    return (
        {"type": "FeatureCollection", "features": features},
        {"passenger_edges": len(features), "ferrocarril_edges": corridor_edges},
    )


def parse_run(
    trip_file: Path, summary_file: Path, departure_period: int
) -> dict[str, Any]:
    trips = ET.parse(trip_file).getroot().findall("tripinfo")
    summary_steps = ET.parse(summary_file).getroot().findall("step")
    if not summary_steps:
        raise RuntimeError(f"SUMO no produjo pasos para {summary_file}")
    last = summary_steps[-1]
    durations = [float(trip.get("duration", "0")) for trip in trips]
    waits = [float(trip.get("waitingTime", "0")) for trip in trips]
    losses = [float(trip.get("timeLoss", "0")) for trip in trips]
    speeds = [
        3.6 * float(trip.get("routeLength", "0")) / duration
        for trip, duration in zip(trips, durations, strict=True)
        if duration > 0
    ]
    return {
        "synthetic_departure_interval_seconds": departure_period,
        "routes_generated": len(
            ET.parse(SUMO_DIR / "routes" / f"osm-{departure_period}.rou.xml")
            .getroot()
            .findall("vehicle")
        ),
        "vehicles_inserted": int(last.get("inserted", "0")),
        "vehicles_arrived": int(last.get("arrived", "0")),
        "vehicles_remaining": int(last.get("running", "0"))
        + int(last.get("waiting", "0")),
        "mean_trip_duration_seconds": round(mean(durations), 2) if durations else None,
        "mean_waiting_seconds": round(mean(waits), 2) if waits else None,
        "mean_time_loss_seconds": round(mean(losses), 2) if losses else None,
        "mean_trip_speed_kmh": round(mean(speeds), 2) if speeds else None,
    }


def build() -> dict[str, Any]:
    if not OSM_FILE.is_file():
        raise FileNotFoundError(f"Falta la extracción OSM: {OSM_FILE}")
    home = sumo_home()
    suffix = ".exe" if os.name == "nt" else ""
    bin_dir = home / "bin"
    netconvert = bin_dir / f"netconvert{suffix}"
    sumo_binary = bin_dir / f"sumo{suffix}"
    random_trips = home / "tools" / "randomTrips.py"
    for executable in (netconvert, sumo_binary, random_trips):
        if not executable.is_file():
            raise FileNotFoundError(f"No se encontró {executable}")
    environment = os.environ.copy()
    environment["SUMO_HOME"] = str(home)
    environment["PATH"] = str(bin_dir) + os.pathsep + environment.get("PATH", "")
    environment["PYTHONPATH"] = (
        str(home / "tools") + os.pathsep + environment.get("PYTHONPATH", "")
    )
    outputs = SUMO_DIR / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    log = outputs / "osm-exploration-build.log"
    log.write_text("", encoding="utf-8")

    execute(
        [
            str(netconvert),
            "--osm-files",
            str(OSM_FILE),
            "--output-file",
            str(NET_FILE),
            "--geometry.remove",
            "--roundabouts.guess",
            "--junctions.join",
            "--output.street-names",
            "true",
        ],
        environment,
        log,
    )
    remove_generated_comments(NET_FILE)
    geojson, network_stats = network_features(home)
    FRONTEND_DATA.mkdir(parents=True, exist_ok=True)
    map_path = FRONTEND_DATA / "osm-exploratory-network.json"
    map_path.write_text(
        json.dumps(geojson, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    results: dict[str, Any] = {}
    for scenario, period in SCENARIOS.items():
        route_file = SUMO_DIR / "routes" / f"osm-{period}.rou.xml"
        requested_trips = outputs / f"osm-{scenario}.trips.xml"
        trip_file = outputs / f"osm-{scenario}.tripinfo.xml"
        summary_file = outputs / f"osm-{scenario}.summary.xml"
        execute(
            [
                sys.executable,
                str(random_trips),
                "-n",
                str(NET_FILE),
                "-r",
                str(route_file),
                "-o",
                str(requested_trips),
                "-b",
                "0",
                "-e",
                str(DEPARTURE_END),
                "-p",
                str(period),
                "--seed",
                str(SEED),
                "--vehicle-class",
                "passenger",
                "--min-distance",
                "300",
            ],
            environment,
            log,
        )
        remove_generated_comments(route_file)
        config = write_config(scenario, route_file)
        execute(
            [
                str(sumo_binary),
                "-c",
                str(config),
                "--seed",
                str(SEED),
                "--tripinfo-output",
                str(trip_file),
                "--summary-output",
                str(summary_file),
                "--no-step-log",
                "true",
            ],
            environment,
            log,
        )
        results[scenario] = parse_run(trip_file, summary_file, period)
        results[scenario]["route_sha256"] = sha256(route_file)

    version = subprocess.run(
        [str(sumo_binary), "--version"], capture_output=True, text=True, check=True
    ).stdout.splitlines()[0]
    report = {
        "study_type": "exploratory_uncalibrated",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "name": "OpenStreetMap contributors",
            "url": SOURCE_URL,
            "license": "ODbL 1.0",
            "attribution_url": "https://www.openstreetmap.org/copyright",
            "snapshot_sha256": sha256(OSM_FILE),
            "bbox_west_south_east_north": [-75.220, -12.073, -75.200, -12.060],
        },
        "software": {"sumo": version, "seed": SEED},
        "network": {
            **network_stats,
            "network_sha256": sha256(NET_FILE),
            "map_sha256": sha256(map_path),
        },
        "time": {
            "departure_end_seconds": DEPARTURE_END,
            "simulation_end_seconds": SIMULATION_END,
        },
        "scenarios": results,
        "limitations": [
            "Viajes generados aleatoriamente; los intervalos no proceden de aforos.",
            "La red OSM es colaborativa y no constituye geometría oficial certificada.",
            "Los resultados no calibran ni predicen el tráfico real de 2026 en Av. Ferrocarril.",
        ],
    }
    report_path = FRONTEND_DATA / "osm-exploratory-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    report = build()
    print(
        json.dumps(
            {"network": report["network"], "scenarios": report["scenarios"]},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
