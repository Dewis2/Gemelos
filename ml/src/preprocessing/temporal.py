import pandas as pd


def temporal_split(
    frame: pd.DataFrame, timestamp_column: str, train_fraction: float = 0.8
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    ordered = frame.sort_values(timestamp_column).reset_index(drop=True)
    split_at = int(len(ordered) * train_fraction)
    if split_at == 0 or split_at == len(ordered):
        raise ValueError("dataset is too small for the requested temporal split")
    return ordered.iloc[:split_at].copy(), ordered.iloc[split_at:].copy()
