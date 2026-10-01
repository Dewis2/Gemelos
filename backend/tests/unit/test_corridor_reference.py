"""Contrato de la topología mínima del corredor usada por el PMV1."""

from __future__ import annotations

from uuid import UUID

from infrastructure.corridor_reference import (
    CORRIDOR_FROM,
    CORRIDOR_NAME,
    CORRIDOR_TO,
    PLACEHOLDER_LANE_COUNT,
    PLACEHOLDER_REFERENCE_SPEED,
    build_corridor,
)


def test_corridor_has_three_segments_and_four_nodes() -> None:
    nodes, segments = build_corridor()
    assert len(segments) == 3
    assert len(nodes) == 4


def test_segment_identifiers_are_valid_and_stable() -> None:
    _, first = build_corridor()
    _, second = build_corridor()
    assert [segment.id for segment in first] == [segment.id for segment in second]
    for segment in first:
        UUID(str(segment.id))
    assert len({segment.id for segment in first}) == 3


def test_segments_reference_two_different_nodes() -> None:
    nodes, segments = build_corridor()
    known = {node.id for node in nodes}
    for segment in segments:
        assert segment.start_intersection_id in known
        assert segment.end_intersection_id in known
        assert segment.start_intersection_id != segment.end_intersection_id


def test_corridor_carries_no_invented_geometry() -> None:
    _, segments = build_corridor()
    assert all(segment.geometry is None for segment in segments)


def test_capacity_values_are_structural_placeholders_not_surveyed_data() -> None:
    """El dominio exige lane_count >= 1 y reference_speed > 0, pero el proyecto
    declara pendientes de validación los carriles y la velocidad del corredor."""
    _, segments = build_corridor()
    for segment in segments:
        assert segment.lane_count == PLACEHOLDER_LANE_COUNT
        assert segment.reference_speed == PLACEHOLDER_REFERENCE_SPEED


def test_segments_never_assert_an_invented_intersection() -> None:
    """Los nodos intermedios son limites tecnicos, no cruces ni semaforos."""
    nodes, _ = build_corridor()
    intermediate = [node.name for node in nodes if "Límite técnico" in node.name]
    assert len(intermediate) == 2
    assert any(node.name.startswith(CORRIDOR_FROM) for node in nodes)
    assert any(node.name.startswith(CORRIDOR_TO) for node in nodes)
    assert all(CORRIDOR_NAME in segment.name for segment in build_corridor()[1])