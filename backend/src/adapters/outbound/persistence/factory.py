"""Factory Method para elegir la implementacion concreta de un puerto de salida.

El proyecto ofrece dos persistencias para los agregados de trafico: memoria, para que
la PoC arranque sin servicios, y PostgreSQL/PostGIS cuando se configura `DEMO_REPOSITORY`.
Esta fabrica concentrate esa decision para que `ApplicationContainer` no la escriba con un
`if` y el caso de uso siga dependiendo solo del puerto.

No es sobrearquitectura: sustituye una rama condicional real del composition root.
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from adapters.outbound.persistence.demo_repository import (
    InMemoryTrafficAggregateRepository,
    SqlAlchemyTrafficAggregateRepository,
)
from application.ports.outbound import TrafficAggregateRepositoryPort

SUPPORTED_PERSISTENCIES = ("memory", "sqlalchemy")


def build_traffic_aggregate_repository(
    persistence: str = "memory",
    *,
    session_factory: Callable[[], Session] | None = None,
) -> TrafficAggregateRepositoryPort:
    """Devuelve el repositorio de agregados segun la persistencia configurada.

    `memory` es el valor por defecto y no necesita sesion de base de datos. La rama
    `sqlalchemy` usa la fabrica de sesiones inyectada por la aplicacion. Si se omite,
    importa `SessionFactory` como alternativa para los clientes existentes. Elegir
    memoria no carga la configuracion de la base.
    """
    key = (persistence or "memory").casefold()
    if key not in SUPPORTED_PERSISTENCIES:
        raise ValueError(
            f"Persistencia no soportada: {persistence!r}. "
            f"Use una de {list(SUPPORTED_PERSISTENCIES)}."
        )
    if key == "sqlalchemy":
        if session_factory is None:
            from infrastructure.database.session import SessionFactory

            session_factory = SessionFactory
        return SqlAlchemyTrafficAggregateRepository(session_factory)
    return InMemoryTrafficAggregateRepository()
