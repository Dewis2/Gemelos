# Modelo físico PostgreSQL/PostGIS

La migración `0001_initial_schema.py` crea ocho tablas con UUID. Los instantes usan
`TIMESTAMPTZ` mediante `DateTime(timezone=True)`. `intersections.geometry` es
`POINT(SRID 4326)` y `road_segments.geometry` es `LINESTRING(SRID 4326)`; ambos son
nulables hasta validar geometría.

Se incluyen índices iniciales para timestamps, `road_segment_id`, `source_id` y
consultas por escenario. No hay particionamiento ni índices especializados prematuros.
Las credenciales provienen del entorno y la migración habilita PostGIS de forma
idempotente.

## Ampliación de demostración

La migración `0002_peru_demo.py` añade `traffic_aggregates`, `traffic_locations` y
`dataset_ingestion_runs`: once tablas de aplicación en total. La instalación se
gestiona mediante Alembic; no ejecutar otro SQL de creación sobre una base migrada.

Los agregados conservan periodos como DATE, sin afirmar una hora exacta.
`traffic_locations.geometry` es POINT(4326) obligatorio. Fases, configuración,
emisiones y metadatos usan JSONB. El [diccionario](data-dictionary.md) detalla cada campo.

## Integridad implementada

- Ocho FK: dos extremos de tramo, fuente y tramo de medición, intersección de plan,
  tramo de predicción, escenario y tramo de resultado. Sin borrado en cascada.
- Unicidad de `traffic_aggregates.natural_key` y de `(dataset_id, source_location_id)`
  en `traffic_locations`.
- `source_location_id` e `ingestion_run_id` en agregados no son FK.
- Las migraciones no definen generación UUID en el servidor. Los clientes deben
  proporcionar los IDs; algunos modelos ORM usan `uuid4` del lado Python.
- Defaults SQL: `data_sources.active=true` y contadores de ingesta en cero.
- Los rangos del dominio (conteo no negativo, ocupación 0–1, carriles positivos)
  no están implementados como CHECK en estas migraciones.

## Índices existentes

| Tabla | Columnas o finalidad |
|---|---|
| traffic_measurements | timestamp, road_segment_id, source_id (separados) |
| traffic_signal_plans | intersection_id |
| traffic_predictions | target_timestamp, road_segment_id (separados) |
| simulation_results | (scenario_id, road_segment_id) |
| traffic_aggregates | (dataset_id, period_start), source_location_id; unicidad natural_key |
| traffic_locations | source_location_id; unicidad (dataset_id, source_location_id) |
| dataset_ingestion_runs | dataset_id |
| intersections, road_segments, traffic_locations | GiST de geometría generado por GeoAlchemy2 |

Las PK también cuentan con índices. No existen particionamiento ni TimescaleDB.

## Alcance y ampliaciones pendientes

La instalación de referencia se comprobó en PostgreSQL 16.15/PostGIS 3.6.2 nativo;
Compose declara `postgis/postgis:16-3.4`. Registrar las versiones reales al presentar
evidencias. No se ha certificado aquí el entorno Docker mediante ejecución.

Faltan contratos y, según el alcance acordado, nuevas migraciones para campañas,
intervalos de aforo, movimientos, ejecuciones de simulación y pares de volúmenes
observados/simulados para GEH. `model_version` no constituye un registro completo
de experimentos ML. Estas ampliaciones no forman parte del esquema implementado.

