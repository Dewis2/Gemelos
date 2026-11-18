"""Bounded, read-only checks for the deployed API; writes a shareable JSON result."""

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path


def measure(url: str) -> dict[str, float | int | str]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except (urllib.error.URLError, TimeoutError):
        status = 0
    return {
        "status": status,
        "milliseconds": round((time.perf_counter() - started) * 1000, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", default="https://gemelos-staging-api.onrender.com"
    )
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.base_url.startswith("https://") or not 1 <= args.requests <= 40:
        parser.error("Use HTTPS y entre 1 y 40 solicitudes.")
    checks = {}
    for path in ("/health", "/api/v1/digital-twin/state"):
        url = args.base_url.rstrip("/") + path
        with ThreadPoolExecutor(max_workers=2) as pool:
            samples = list(pool.map(measure, [url] * args.requests))
        times = sorted(float(item["milliseconds"]) for item in samples)
        checks[path] = {
            "request_count": len(samples),
            "status_counts": {
                str(code): sum(item["status"] == code for item in samples)
                for code in sorted({item["status"] for item in samples})
            },
            "latency_ms": {
                "min": times[0],
                "median": round(statistics.median(times), 2),
                "p95": times[min(len(times) - 1, int(0.95 * len(times)))],
                "max": times[-1],
            },
        }
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "base_url": args.base_url,
        "concurrency": 2,
        "checks": checks,
        "scope": (
            "Sondeo acotado de salud y estado del gemelo (consulta de repositorio); "
            "no mide SUMO ni capacidad máxima."
        ),
    }
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
