"""Add versioned database routines for validated traffic measurements and reporting.

The application can continue using SQLAlchemy repositories. These routines provide
an explicit, tested PostgreSQL stored-procedure interface where required by the
academic checklist, without silently changing the existing API contract.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE PROCEDURE public.sp_register_traffic_measurement(
            p_id UUID,
            p_source_id UUID,
            p_road_segment_id UUID,
            p_timestamp TIMESTAMPTZ,
            p_traffic_volume INTEGER,
            p_average_speed DOUBLE PRECISION DEFAULT NULL,
            p_occupancy DOUBLE PRECISION DEFAULT NULL
        )
        LANGUAGE plpgsql
        AS $procedure$
        BEGIN
            IF p_traffic_volume IS NULL OR p_traffic_volume < 0 THEN
                RAISE EXCEPTION 'traffic_volume must be non-negative'
                    USING ERRCODE = '22023';
            END IF;
            IF p_average_speed IS NOT NULL AND p_average_speed < 0 THEN
                RAISE EXCEPTION 'average_speed must be non-negative'
                    USING ERRCODE = '22023';
            END IF;
            IF p_occupancy IS NOT NULL
                AND (p_occupancy < 0 OR p_occupancy > 1) THEN
                RAISE EXCEPTION 'occupancy must be between 0 and 1'
                    USING ERRCODE = '22023';
            END IF;

            INSERT INTO traffic_measurements (
                id, source_id, road_segment_id, timestamp,
                traffic_volume, average_speed, occupancy
            ) VALUES (
                p_id, p_source_id, p_road_segment_id, p_timestamp,
                p_traffic_volume, p_average_speed, p_occupancy
            );
        END;
        $procedure$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION public.fn_traffic_summary(
            p_road_segment_id UUID,
            p_from TIMESTAMPTZ,
            p_to TIMESTAMPTZ
        )
        RETURNS TABLE (
            measurement_count BIGINT,
            volume_total BIGINT,
            average_speed DOUBLE PRECISION
        )
        LANGUAGE sql
        STABLE
        AS $function$
            SELECT
                COUNT(*)::BIGINT,
                COALESCE(SUM(m.traffic_volume), 0)::BIGINT,
                AVG(m.average_speed)::DOUBLE PRECISION
            FROM traffic_measurements AS m
            WHERE m.road_segment_id = p_road_segment_id
              AND m.timestamp >= p_from
              AND m.timestamp < p_to;
        $function$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP FUNCTION IF EXISTS public.fn_traffic_summary(
            UUID, TIMESTAMPTZ, TIMESTAMPTZ
        )
        """
    )
    op.execute(
        """
        DROP PROCEDURE IF EXISTS public.sp_register_traffic_measurement(
            UUID, UUID, UUID, TIMESTAMPTZ,
            INTEGER, DOUBLE PRECISION, DOUBLE PRECISION
        )
        """
    )
