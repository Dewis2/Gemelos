"""Strategy para la política de ámbito de un conjunto de datos de tráfico.

Este módulo hace explícito el patrón Strategy, que antes quedaba diluido entre un
`if` dentro del servicio de consulta y adaptadores intercambiables inyectados una sola
vez (lo cual es Adapter + Dependency Injection, no Strategy).

La diferencia que se quiere representar:

* **Adapter + DI** — el simulador o el publicador se eligen *una vez* en la raíz de
  composición y no cambian durante la vida del caso de uso.
* **Strategy** — el contexto `TrafficScopeResolver` *selecciona* la política aplicable
  en cada petición, según el conjunto de datos consultado, y admite sustituirla o
  registrar nuevas en tiempo de ejecución.

La política tiene significado en el dominio: el proyecto separa de forma explícita el
aforo histórico local de Huancayo de las fuentes oficiales regionales de demostración,
y cada ámbito exige una advertencia distinta. Antes esa decisión estaba incrustada como
condicional dentro de `PeruDemoQueryService.traffic`.

No cambia ningún endpoint, texto ni resultado: las advertencias son exactamente las
mismas que producía el condicional anterior.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class TrafficScopeStrategy(Protocol):
    """Estrategia: decide la política de aviso aplicable a un conjunto de datos."""

    @property
    def key(self) -> str:
        """Identificador de la estrategia."""

    def admits(self, dataset_id: str) -> bool:
        """Indica si esta estrategia aplica al conjunto indicado."""

    def warning(self) -> str:
        """Advertencia que debe acompañar a los datos de ese ámbito."""


class LocalHistoricalScope:
    """Aforos históricos del corredor, de la Municipalidad Provincial de Huancayo (2013).

    Son referencia histórica del corredor y no representan el tráfico actual, por lo que
    la interfaz debe decirlo de forma expresa.
    """

    key = "local_historical"

    def __init__(self, dataset_id: str = "huancayo_historical_counts_2013") -> None:
        self._dataset_id = dataset_id

    def admits(self, dataset_id: str) -> bool:
        return dataset_id == self._dataset_id

    def warning(self) -> str:
        return "Aforos históricos municipales. No representan tráfico actual de 2026."


class NationalDemoScope:
    """Fuentes oficiales regionales (MTC, OSITRAN) usadas como evidencia técnica.

    Corresponden a peajes y carreteras fuera del corredor urbano, así que la interfaz
    debe separarlas del corredor Av. Ferrocarril.
    """

    key = "national_demo"

    def admits(self, dataset_id: str) -> bool:
        return True

    def warning(self) -> str:
        return (
            "Demostración con datos históricos oficiales. No representa "
            "tiempo real ni tráfico urbano de la Av. Ferrocarril."
        )


def default_scope_strategies() -> tuple[TrafficScopeStrategy, ...]:
    """Orden de resolución: primero la específica y después la general."""
    return (LocalHistoricalScope(), NationalDemoScope())


class TrafficScopeResolver:
    """Contexto Strategy: selecciona y permite intercambiar la política aplicable."""

    def __init__(
        self, strategies: Sequence[TrafficScopeStrategy] | None = None
    ) -> None:
        self._strategies: list[TrafficScopeStrategy] = list(
            default_scope_strategies() if strategies is None else strategies
        )

    @property
    def strategies(self) -> tuple[TrafficScopeStrategy, ...]:
        return tuple(self._strategies)

    def resolve(self, dataset_id: str) -> TrafficScopeStrategy:
        """Devuelve la primera estrategia que admite el conjunto de datos."""
        for strategy in self._strategies:
            if strategy.admits(dataset_id):
                return strategy
        raise LookupError(f"No hay ninguna estrategia de ámbito para {dataset_id!r}")

    def register(self, strategy: TrafficScopeStrategy, *, first: bool = False) -> None:
        """Añade una estrategia en tiempo de ejecución, opcionalmente como primera."""
        if first:
            self._strategies.insert(0, strategy)
        else:
            self._strategies.append(strategy)
