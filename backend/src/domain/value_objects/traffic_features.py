"""Contrato de variables de entrada del modelo de flujo vehicular.

El modelo se entrena con cuatro variables temporales. Este value object concentra la
regla de negocio que las valida, de modo que el caso de uso, la API y las pruebas
compartan una unica definicion en lugar de repetir comprobaciones.

La convencion de `day_of_week` coincide con `pandas.Timestamp.dayofweek` (lunes = 0,
domingo = 6). El orden alfabetico de los nombres forma parte del contrato porque el
adaptador de inferencia construye el vector con `sorted(features)`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from domain.exceptions import DomainValidationError

#: variable -> (valor minimo, valor maximo) admitidos.
FEATURE_CONTRACT: dict[str, tuple[int, int]] = {
    "day_of_week": (0, 6),
    "hour": (0, 23),
    "is_weekend": (0, 1),
    "month": (1, 12),
}

FEATURE_NAMES: tuple[str, ...] = tuple(sorted(FEATURE_CONTRACT))


@dataclass(frozen=True, slots=True)
class TrafficFeatures:
    """Variables de entrada ya validadas del modelo de prediccion."""

    day_of_week: int
    hour: int
    is_weekend: int
    month: int

    @classmethod
    def from_mapping(cls, values: Mapping[str, float]) -> TrafficFeatures:
        missing = sorted(name for name in FEATURE_NAMES if name not in values)
        if missing:
            raise DomainValidationError(
                f"Faltan variables de entrada del modelo: {', '.join(missing)}."
            )
        unknown = sorted(name for name in values if name not in FEATURE_CONTRACT)
        if unknown:
            raise DomainValidationError(
                f"Variables no esperadas por el modelo: {', '.join(unknown)}."
            )

        parsed: dict[str, int] = {}
        for name, (minimum, maximum) in FEATURE_CONTRACT.items():
            raw = values[name]
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                raise DomainValidationError(f"La variable {name} debe ser numerica.")
            if float(raw) != int(raw):
                raise DomainValidationError(f"La variable {name} debe ser un numero entero.")
            value = int(raw)
            if not minimum <= value <= maximum:
                raise DomainValidationError(
                    f"La variable {name} debe estar entre {minimum} y {maximum}; recibio {value}."
                )
            parsed[name] = value

        if parsed["is_weekend"] != int(parsed["day_of_week"] in {5, 6}):
            raise DomainValidationError(
                "La variable is_weekend no coincide con day_of_week: solo sábado y domingo valen 1."
            )
        return cls(**parsed)

    def as_mapping(self) -> dict[str, float]:
        return {name: float(getattr(self, name)) for name in FEATURE_NAMES}