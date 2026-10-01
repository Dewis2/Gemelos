"""Topología mínima del corredor Av. Ferrocarril para el PMV1.

El proyecto declara de forma explícita que la topología, los carriles, los semáforos
y la geometría del corredor están *pendientes de validación* (README, sección
"Limitaciones actuales"). Este módulo no resuelve esa validación: aporta únicamente la
estructura técnica mínima que el gemelo necesita para tener segmentos seleccionables.

Decisiones y su fundamento:

* Los UUID se derivan con ``uuid5`` sobre un espacio de nombres fijo, de modo que el
  corredor sea idéntico en cada arranque y los enlaces del frontend sean estables.
* ``geometry`` queda en ``None``: no se dibuja cartografía sin fuente verificada.
* Los nodos intermedios se nombran como **límites técnicos**, no como intersecciones,
  porque el repositorio no documenta cruces ni semáforos de la vía.
* ``lane_count`` y ``reference_speed`` cumplen el mínimo que exige
  ``RoadSegment.__post_init__``. Son **relleno estructural**, no atributos levantados en
  campo: ver PLACEHOLDER_* y la advertencia del módulo.
* Los puntos P03, P04 y P42 NO se convierten en segmentos. Son puntos de aforo
  histórico (conjunto `huancayo_historical_counts_2013`), una categoría distinta del
  dominio. Solo se cross-referencia el tramo donde los ubica su descripción oficial.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from domain.entities import Intersection, RoadSegment

CORRIDOR_NAME = "Av. Ferrocarril"
CORRIDOR_FROM = "Av. Giráldez"
CORRIDOR_TO = "Av. Huancavelica"
CORRIDOR_LABEL = f"{CORRIDOR_NAME}: {CORRIDOR_FROM}–{CORRIDOR_TO}"

#: Espacio de nombres estable; cambiarlo cambiaría todos los identificadores del corredor.
CORRIDOR_NAMESPACE = uuid5(NAMESPACE_URL, "https://gemelo-digital-huancayo.org/corredor/ferrocarril")

#: Valores exigidos por el contrato de dominio, no datos de la vía.
PLACEHOLDER_LANE_COUNT = 1
PLACEHOLDER_REFERENCE_SPEED = 1.0

#: Ordena el corredor desde Av. Giráldez hasta Av. Huancavelica.
_NODES: tuple[tuple[str, str], ...] = (
    ("giraldez", f"{CORRIDOR_FROM} (inicio del corredor)"),
    ("limite-norte", "Límite técnico norte"),
    ("limite-sur", "Límite técnico sur"),
    ("huancavelica", f"{CORRIDOR_TO} (fin del corredor)"),
)

#: (clave inicial, clave final, nombre, puntos de aforo históricos cuya descripción
#: oficial los ubica en ese tramo).
_SEGMENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "giraldez",
        "limite-norte",
        f"{CORRIDOR_NAME} · tramo norte (ref. P03, P04)",
        "P03 y P04 se describen en el Plan Regulador como próximos a Av. Giráldez.",
    ),
    (
        "limite-norte",
        "limite-sur",
        f"{CORRIDOR_NAME} · tramo centro",
        "Ninguno de los puntos de aforo disponibles está descrito en este tramo.",
    ),
    (
        "limite-sur",
        "huancavelica",
        f"{CORRIDOR_NAME} · tramo sur (ref. P42)",
        "P42 se describe en el Plan Regulador como próximo a Av. Huancavelica.",
    ),
)


def _node_id(key: str):
    return uuid5(CORRIDOR_NAMESPACE, f"node:{key}")


def segment_id(key: str):
    """Identificador estable del tramo, para enlazarlo desde el frontend."""
    return uuid5(CORRIDOR_NAMESPACE, f"segment:{key}")


def build_corridor_nodes() -> list[Intersection]:
    return [Intersection(name=name, id=_node_id(key)) for key, name in _NODES]


def build_corridor_segments() -> list[RoadSegment]:
    segments: list[RoadSegment] = []
    for start, end, name, _ in _SEGMENTS:
        segments.append(
            RoadSegment(
                name=name,
                id=uuid5(CORRIDOR_NAMESPACE, f"segment:{start}-{end}"),
                start_intersection_id=_node_id(start),
                end_intersection_id=_node_id(end),
                lane_count=PLACEHOLDER_LANE_COUNT,
                reference_speed=PLACEHOLDER_REFERENCE_SPEED,
                geometry=None,
            )
        )
    return segments


def build_corridor() -> tuple[list[Intersection], list[RoadSegment]]:
    return build_corridor_nodes(), build_corridor_segments()


def segment_reference_notes() -> dict[str, str]:
    """Notas de trazabilidad por tramo, para exponerlas sin affirmar más de lo que hay."""
    return {
        uuid5(CORRIDOR_NAMESPACE, f"segment:{start}-{end}").urn: note
        for start, end, _, note in _SEGMENTS
    }