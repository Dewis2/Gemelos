import pandas as pd

from ml.src.features.features import CALENDAR_FEATURES, build_time_features
from ml.src.preprocessing.temporal import temporal_split


def test_temporal_split_preserves_chronology() -> None:
    frame = pd.DataFrame(
        {"timestamp": ["2024-01-03", "2024-01-01", "2024-01-02"], "value": [3, 1, 2]}
    )
    train, test = temporal_split(frame, "timestamp", train_fraction=2 / 3)
    assert train["value"].tolist() == [1, 2]
    assert test["value"].tolist() == [3]


def test_calendar_features_match_the_api_vector_order() -> None:
    """The API adapter orders features with ``sorted(features)``.

    scikit-learn only validates the column count, so training with a different
    order would serve silently wrong predictions instead of raising.
    """
    assert list(CALENDAR_FEATURES) == sorted(CALENDAR_FEATURES)
    assert list(CALENDAR_FEATURES) == ["day_of_week", "hour", "is_weekend", "month"]


def test_build_time_features_derives_the_contract_columns() -> None:
    frame = pd.DataFrame({"timestamp": ["2024-05-04T08:00:00Z"]})
    built = build_time_features(frame)
    # 2024-05-04 is a Saturday (pandas dayofweek 5).
    assert built.loc[0, "day_of_week"] == 5
    assert built.loc[0, "hour"] == 8
    assert built.loc[0, "month"] == 5
    assert built.loc[0, "is_weekend"] == 1
    for feature in CALENDAR_FEATURES:
        assert feature in built.columns
