import pandas as pd

#: Canonical input contract of the traffic-flow model.
#:
#: The order is the alphabetical order of the names on purpose: the API adapter
#: `adapters/outbound/ml/joblib_model.py` builds its vector with
#: ``[features[key] for key in sorted(features)]``, so training, inference and
#: serving only agree while this tuple stays sorted. scikit-learn validates the
#: number of columns but not their names, so a drifted order yields silently
#: wrong predictions instead of an error. ``ml/tests/test_temporal_split.py``
#: guards this invariant.
CALENDAR_FEATURES: tuple[str, ...] = ("day_of_week", "hour", "is_weekend", "month")


def build_time_features(
    frame: pd.DataFrame, timestamp_column: str = "timestamp"
) -> pd.DataFrame:
    """Create causal calendar features; does not use future target values."""
    result = frame.copy()
    timestamps = pd.to_datetime(result[timestamp_column], utc=True)
    result["hour"] = timestamps.dt.hour
    result["day_of_week"] = timestamps.dt.dayofweek
    result["month"] = timestamps.dt.month
    result["is_weekend"] = (timestamps.dt.dayofweek >= 5).astype(int)
    return result
