import pandas as pd

from ml.src.preprocessing.temporal import temporal_split


def test_temporal_split_preserves_chronology() -> None:
    frame = pd.DataFrame(
        {"timestamp": ["2024-01-03", "2024-01-01", "2024-01-02"], "value": [3, 1, 2]}
    )
    train, test = temporal_split(frame, "timestamp", train_fraction=2 / 3)
    assert train["value"].tolist() == [1, 2]
    assert test["value"].tolist() == [3]
