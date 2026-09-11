import json
from collections.abc import Sequence

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(
    actual: Sequence[float], predicted: Sequence[float]
) -> dict[str, float]:
    """Return MAE, RMSE and R² without interpreting them as project validation."""
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            {"status": "provide actual and predicted values through the Python API"}
        )
    )
