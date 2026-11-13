"""Bounded ASGI load check with memory repositories and no remote writes."""

import argparse
import asyncio
import json
import logging
import statistics
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from adapters.inbound.api import create_app
from infrastructure.config import Settings

PATHS = (
    "/health",
    "/api/v1/road-segments",
    "/api/v1/datasets",
    "/api/v1/digital-twin/state",
    "/api/v1/scenarios",
)


async def run(requests: int, concurrency: int) -> dict[str, object]:
    if not 1 <= requests <= 1000 or not 1 <= concurrency <= 50:
        raise ValueError("requests must be 1–1000 and concurrency 1–50")
    settings = Settings(
        _env_file=None,
        core_repository="memory",
        demo_repository="memory",
        mqtt_enabled=False,
        ml_model_path="nonexistent-local-load-model.joblib",
    )
    app = create_app(settings)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    transport = httpx.ASGITransport(app=app)
    semaphore = asyncio.Semaphore(concurrency)
    durations: list[float] = []
    statuses: Counter[int] = Counter()
    by_route: Counter[str] = Counter()

    async with httpx.AsyncClient(
        transport=transport, base_url="http://local.test"
    ) as client:

        async def one(index: int) -> None:
            route = PATHS[index % len(PATHS)]
            async with semaphore:
                start = perf_counter()
                response = await client.get(route)
                durations.append((perf_counter() - start) * 1000)
                statuses[response.status_code] += 1
                by_route[route] += 1

        start_total = perf_counter()
        await asyncio.gather(*(one(i) for i in range(requests)))
        elapsed = perf_counter() - start_total
    app.state.container.close()
    ordered = sorted(durations)
    return {
        "environment": "local in-process ASGI; memory repositories; no network or PostgreSQL",
        "method": "GET only",
        "requests": requests,
        "concurrency": concurrency,
        "responses_by_status": dict(sorted(statuses.items())),
        "requests_by_route": dict(by_route),
        "duration_seconds": round(elapsed, 3),
        "throughput_requests_per_second": round(requests / elapsed, 2),
        "latency_ms_p50": round(statistics.median(ordered), 2),
        "latency_ms_p95": round(ordered[int((len(ordered) - 1) * 0.95)], 2),
        "latency_ms_max": round(max(ordered), 2),
        "passed": statuses == {200: requests},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=750)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = asyncio.run(run(args.requests, args.concurrency))
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    print(output)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
