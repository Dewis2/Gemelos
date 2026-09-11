"""Initial PostGIS schema for the digital-twin PoC."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "intersections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("geometry", Geometry("POINT", srid=4326), nullable=True),
    )
    op.create_table(
        "road_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("start_intersection_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("intersections.id"), nullable=False),
        sa.Column("end_intersection_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("intersections.id"), nullable=False),
        sa.Column("lane_count", sa.Integer(), nullable=False),
        sa.Column("reference_speed", sa.Float(), nullable=False),
        sa.Column("geometry", Geometry("LINESTRING", srid=4326), nullable=True),
    )
    op.create_table(
        "data_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "traffic_measurements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("road_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("road_segments.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("traffic_volume", sa.Integer(), nullable=False),
        sa.Column("average_speed", sa.Float(), nullable=True),
        sa.Column("occupancy", sa.Float(), nullable=True),
    )
    op.create_index("ix_traffic_measurements_timestamp", "traffic_measurements", ["timestamp"])
    op.create_index("ix_traffic_measurements_road_segment_id", "traffic_measurements", ["road_segment_id"])
    op.create_index("ix_traffic_measurements_source_id", "traffic_measurements", ["source_id"])
    op.create_table(
        "traffic_signal_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("intersection_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("intersections.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("phases", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_traffic_signal_plans_intersection_id", "traffic_signal_plans", ["intersection_id"])
    op.create_table(
        "traffic_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("road_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("road_segments.id"), nullable=False),
        sa.Column("prediction_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("predicted_volume", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=False),
    )
    op.create_index("ix_traffic_predictions_target_timestamp", "traffic_predictions", ["target_timestamp"])
    op.create_index("ix_traffic_predictions_road_segment_id", "traffic_predictions", ["road_segment_id"])
    op.create_table(
        "simulation_scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("configuration", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "simulation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulation_scenarios.id"), nullable=False),
        sa.Column("road_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("road_segments.id"), nullable=False),
        sa.Column("travel_time", sa.Float(), nullable=False),
        sa.Column("average_speed", sa.Float(), nullable=False),
        sa.Column("delay", sa.Float(), nullable=False),
        sa.Column("queue_length", sa.Float(), nullable=False),
        sa.Column("emissions", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_simulation_results_scenario_segment", "simulation_results", ["scenario_id", "road_segment_id"])


def downgrade() -> None:
    for table in [
        "simulation_results",
        "simulation_scenarios",
        "traffic_predictions",
        "traffic_signal_plans",
        "traffic_measurements",
        "data_sources",
        "road_segments",
        "intersections",
    ]:
        op.drop_table(table)

