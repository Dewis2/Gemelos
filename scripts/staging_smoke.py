"""Manual HTTP smoke checks for public staging endpoints (Python stdlib only).

Usage:
  python scripts/staging_smoke.py --frontend https://FRONTEND --api https://API
  python scripts/staging_smoke.py --frontend https://FRONTEND --api https://API --predict

The optional prediction sends a test record to the staging database. This is NOT
a validation of accuracy for Huancayo or evidence of current local traffic.
"""

import argparse
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def ensure_https(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("The staging endpoint must use a public HTTPS URL.")
    if parsed.hostname in {"localhost", "127.0.0.1"}:
        raise ValueError("Localhost is prohibited for Laboratory 11.")
    return url.rstrip("/")


def fetch(url, payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    request = Request(url, data=body, headers=headers, method="POST" if body else "GET")
    try:
        with urlopen(request, timeout=25) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type", "")
            value = json.loads(raw) if "application/json" in content_type else None
            return response.status, value
    except HTTPError as error:
        return error.code, {"error": error.reason}
    except URLError as error:
        raise RuntimeError(f"Cannot reach {url}: {error.reason}") from error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend", required=True)
    parser.add_argument("--api", required=True)
    parser.add_argument("--predict", action="store_true", help="Creates a test prediction")
    args = parser.parse_args()
    frontend = ensure_https(args.frontend)
    api = ensure_https(args.api)
    status, _ = fetch(frontend)
    assert status == 200, f"Frontend status: {status}"
    print("Frontend HTTPS: 200")
    status, body = fetch(api + "/health")
    assert status == 200 and body["status"] == "ok", f"Health: {status}"
    print("Backend health: 200")
    status, segments = fetch(api + "/api/v1/road-segments")
    assert status == 200 and len(segments) == 3, f"Road segments: {status}"
    print("Backend/Postgres road segments: 3")
    status, datasets = fetch(api + "/api/v1/datasets")
    assert status == 200 and datasets, f"Datasets: {status}"
    print("Datasets accessible; provenance must be checked in UI.")
    if args.predict:
        timestamp = datetime.now(timezone.utc)
        features = {
            "day_of_week": timestamp.weekday(),
            "hour": timestamp.hour,
            "is_weekend": int(timestamp.weekday() >= 5),
            "month": timestamp.month,
        }
        status, result = fetch(
            api + "/api/v1/predictions/traffic-flow",
            {
                "road_segment_id": segments[0]["id"],
                "target_timestamp": timestamp.isoformat(),
                "features": features,
            },
        )
        assert status == 201, f"Prediction: {status}, {result}"
        print("Experimental prediction stored:", result["id"])
        print("Model version:", result["model_version"])
        print("Warning: MITV-UCI is not validated for Huancayo.")
    print("Smoke checks completed. Store timestamp, URLs, logs and screenshots as evidence.")


if __name__ == "__main__":
    main()
