import pandas as pd


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
