"""Factory Method para elegir la implementacion concreta de un puerto de salida.

El proyecto ofrece dos persistencias para los agregados de trafico: memoria, para que
la PoC arranque sin servicios, y PostgreSQL/PostGIS cuando se configura `DEMO_REPOSITORY`.
Esta fabrica concentrate esa decision para que `ApplicationContainer` no la escriba con un
`if` y el caso de uso siga dependiendo solo del puerto.

No es sobrearquitectura: sustituye una rama condicional real del composition root.
"""

from __future__ import annotations

from adapters.outbound.persistence.demo_repository import (
    InMemoryTrafficAggregateRepository,
    SqlAlchemyTrafficAggregateRepository,
)
from application.ports.outbound import TrafficAggregateRepositoryPort

SUPPORTED_PERSISTENCIES = ("memory", "sqlalchemy")


def build_traffic_aggregate_repository(
    persistence: str = "memory",
) -> TrafficAggregateRepositoryPort:
    """Devuelve el repositorio de agregados segun la persistencia configurada.

    `memory` es el valor por defecto y no necesita sesion de base de datos. La rama
    `sqlalchemy` importa el `SessionFactory` de infraestructura solo cuando se usa,
    de modo que elegir memoria no cargue la configuracion de la base.
    """
    key = (persistence or "memory").casefold()
    if key not in SUPPORTED_PERSISTENCIES:
        raise ValueError(
            f"Persistencia no soportada: {persistence!r}. "
            f"Use una de {list(SUPPORTED_PERSISTENCIES)}."
        )
    if key == "sqlalchemy":
        from infrastructure.database.session import SessionFactory

        return SqlAlchemyTrafficAggregateRepository(SessionFactory)
    return InMemoryTrafficAggregateRepository()