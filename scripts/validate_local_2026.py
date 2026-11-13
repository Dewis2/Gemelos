"""Validate a supplied local dataset without importing it into the database."""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ml.src.preprocessing.local_huancayo import validate_local_counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate_local_counts(args.csv, datetime.now(UTC))
    result = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.write_text(result, encoding="utf-8")
    print(result)
    return 0 if report["schema_quality_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
