"""Value objects del dominio.

Se incorporan conforme se validan las semanticas del corredor. `TrafficFeatures`
formaliza el contrato de entrada del modelo de prediccion.
"""

from domain.value_objects.traffic_features import (
    FEATURE_CONTRACT,
    FEATURE_NAMES,
    TrafficFeatures,
)

__all__ = ["FEATURE_CONTRACT", "FEATURE_NAMES", "TrafficFeatures"]
