from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]
import numpy as np


class ModelNotReadyError(RuntimeError):
    """Raised when inference is requested before a validated model is available."""


class JoblibTrafficModel:
    def __init__(self, model_path: str | Path) -> None:
        self._path = Path(model_path)
        self._model: Any | None = None

    def _load(self) -> Any:
        if not self._path.exists():
            raise ModelNotReadyError(
                f"No trained model at {self._path}. Train and validate one with project data first."
            )
        if self._model is None:
            self._model = joblib.load(self._path)
        return self._model

    def predict_traffic(self, features: dict[str, float]) -> tuple[float, str]:
        model = self._load()
        ordered = np.asarray([[features[key] for key in sorted(features)]], dtype=float)
        prediction = float(model.predict(ordered)[0])
        version = str(getattr(model, "model_version", self._path.stem))
        return prediction, version
