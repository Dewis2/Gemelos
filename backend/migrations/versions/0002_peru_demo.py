"""Add official Peru demo aggregates, locations and ingestion runs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "traffic_aggregates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("natural_key", sa.String(500), nullable=False, unique=True),
        sa.Column("dataset_id", sa.String(100), nullable=False),
        sa.Column("source_record_id", sa.String(128), nullable=False),
        sa.Column("source_provider", sa.String(200), nullable=False),
        sa.Column("source_country", sa.String(80), nullable=False),
        sa.Column("source_region", sa.String(100)),
        sa.Column("source_location_id", sa.String(120), nullable=False),
        sa.Column("source_location_name", sa.String(200), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("temporal_granularity", sa.String(40), nullable=False),
        sa.Column("vehicle_category", sa.String(100), nullable=False),
        sa.Column("vehicle_count", sa.Integer(), nullable=False),
        sa.Column("dataset_scope", sa.String(80), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False),
        sa.Column("ingestion_run_id", sa.String(80)),
    )
    op.create_index(
        "ix_traffic_aggregates_dataset_period",
        "traffic_aggregates",
        ["dataset_id", "period_start"],
    )
    op.create_index(
        "ix_traffic_aggregates_location", "traffic_aggregates", ["source_location_id"]
    )
    op.create_table(
        "traffic_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", sa.String(100), nullable=False),
        sa.Column("source_location_id", sa.String(120), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(80), nullable=False),
        sa.Column("operator", sa.String(250)),
        sa.Column("status", sa.String(100)),
        sa.Column("geometry", Geometry("POINT", srid=4326), nullable=False),
        sa.Column("properties_json", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint(
            "dataset_id", "source_location_id", name="uq_traffic_locations_dataset_source"
        ),
    )
    op.create_index(
        "ix_traffic_locations_source_location_id",
        "traffic_locations",
        ["source_location_id"],
    )
    op.create_table(
        "dataset_ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", sa.String(100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("files_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_read", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_valid", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
    )
    op.create_index(
        "ix_dataset_ingestion_runs_dataset_id", "dataset_ingestion_runs", ["dataset_id"]
    )


def downgrade() -> None:
    op.drop_table("dataset_ingestion_runs")
    op.drop_table("traffic_locations")
    op.drop_table("traffic_aggregates")
