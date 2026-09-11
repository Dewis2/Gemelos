# Modelo físico PostgreSQL/PostGIS

La migración `0001_initial_schema.py` crea ocho tablas con UUID. Los instantes usan
`TIMESTAMPTZ` mediante `DateTime(timezone=True)`. `intersections.geometry` es
`POINT(SRID 4326)` y `road_segments.geometry` es `LINESTRING(SRID 4326)`; ambos son
nulables hasta validar geometría.

Se incluyen índices iniciales para timestamps, `road_segment_id`, `source_id` y
consultas por escenario. No hay particionamiento ni índices especializados prematuros.
Las credenciales provienen del entorno y la migración habilita PostGIS de forma
idempotente.

