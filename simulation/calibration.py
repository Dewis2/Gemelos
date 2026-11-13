"""Compare observed and simulated counts without assuming either is real."""

import argparse
import csv
import json
import math
from pathlib import Path


def read_counts(path: Path) -> dict[tuple[str, str], int]:
    values: dict[tuple[str, str], int] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"road_segment_id", "period_start", "vehicle_count"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name}: required columns are {sorted(required)}")
        for number, row in enumerate(reader, 2):
            key = (row["road_segment_id"].strip(), row["period_start"].strip())
            count = int(row["vehicle_count"])
            if not all(key) or count < 0 or key in values:
                raise ValueError(f"{path.name}: invalid or duplicate row {number}")
            values[key] = count
    if not values:
        raise ValueError(f"{path.name}: no records")
    return values


def compare(
    observed: dict[tuple[str, str], int], simulated: dict[tuple[str, str], int]
) -> dict[str, float | int]:
    if observed.keys() != simulated.keys():
        raise ValueError(
            "Observed and simulated files must have identical segment/period keys"
        )
    geh_values = []
    squared_errors = []
    for key, observed_count in observed.items():
        simulated_count = simulated[key]
        total = observed_count + simulated_count
        geh_values.append(
            math.sqrt(2 * (observed_count - simulated_count) ** 2 / total)
            if total
            else 0.0
        )
        squared_errors.append((observed_count - simulated_count) ** 2)
    return {
        "paired_points": len(geh_values),
        "mean_geh": round(sum(geh_values) / len(geh_values), 4),
        "share_geh_below_5": round(sum(v < 5 for v in geh_values) / len(geh_values), 4),
        "rmse_vehicles": round(math.sqrt(sum(squared_errors) / len(squared_errors)), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate paired counts for SUMO calibration"
    )
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--simulated", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = compare(read_counts(args.observed), read_counts(args.simulated))
    text = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
