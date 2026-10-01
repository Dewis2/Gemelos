from pathlib import Path

import joblib
import pandas as pd

from ml.src.features.features import CALENDAR_FEATURES


def predict(model_path: Path, features: dict[str, float]) -> float:
    if not model_path.is_file():
        raise FileNotFoundError(f"Validated model not found: {model_path}")
    model = joblib.load(model_path)
    ordered_names = list(CALENDAR_FEATURES)
    frame = pd.DataFrame(
        [[features[name] for name in ordered_names]], columns=ordered_names
    )
    return max(0.0, float(model.predict(frame)[0]))
