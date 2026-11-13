from simulation.calibration import compare


def test_identical_counts_have_zero_error() -> None:
    values = {("segment-1", "2026-11-01T08:00-05:00"): 100}
    result = compare(values, values)
    assert result == {
        "paired_points": 1,
        "mean_geh": 0.0,
        "share_geh_below_5": 1.0,
        "rmse_vehicles": 0.0,
    }
