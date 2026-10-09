# Diccionario de datos

Once tablas de las migraciones `0001` y `0002`. Tipos y nulabilidad contrastados con los modelos SQLAlchemy. PK: primaria; FK: foránea; UQ: unicidad. Las unidades no expresadas por el contrato se señalan como pendientes, sin atribuirles una precisión inexistente.

Las migraciones no generan UUID en SQL. Defaults del servidor: `data_sources.active=true` y los contadores de `dataset_ingestion_runs=0`; los demás campos no tienen default SQL en estas migraciones. Algunos defaults del ORM se aplican únicamente cuando escribe Python.

## intersections

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `name` | `VARCHAR(150)` | No | — | Nombre descriptivo. |
| `geometry` | `geometry(POINT,4326)` | Sí | — | Geometría espacial con SRID 4326; coordenadas longitud/latitud. |

## road_segments

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `name` | `VARCHAR(150)` | No | — | Nombre descriptivo. |
| `start_intersection_id` | `UUID` | No | FK → intersections.id | Nodo de inicio del tramo. |
| `end_intersection_id` | `UUID` | No | FK → intersections.id | Nodo de fin del tramo. |
| `lane_count` | `INTEGER` | No | — | Número de carriles; valor estructural hasta validación. |
| `reference_speed` | `FLOAT` | No | — | Velocidad de referencia; acordar unidad con el adaptador antes de cargar datos. |
| `geometry` | `geometry(LINESTRING,4326)` | Sí | — | Geometría espacial con SRID 4326; coordenadas longitud/latitud. |

## data_sources

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `name` | `VARCHAR(150)` | No | — | Nombre descriptivo. |
| `source_type` | `VARCHAR(50)` | No | — | Tipo de procedencia de datos. |
| `description` | `VARCHAR(500)` | Sí | — | Descripción de la fuente o escenario. |
| `active` | `BOOLEAN` | No | — | Indica si la fuente está activa. |

## traffic_measurements

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `source_id` | `UUID` | No | FK → data_sources.id | Fuente de la medición. |
| `road_segment_id` | `UUID` | No | FK → road_segments.id | Tramo asociado. |
| `timestamp` | `TIMESTAMP WITH TIME ZONE` | No | — | Instante de la observación con zona horaria. |
| `traffic_volume` | `INTEGER` | No | — | Conteo de vehículos; el esquema no define la duración del intervalo. |
| `average_speed` | `FLOAT` | Sí | — | Velocidad media; unidad a documentar con la fuente o simulador. |
| `occupancy` | `FLOAT` | Sí | — | En mediciones, fracción de ocupación entre 0 y 1 validada por el dominio. |

## traffic_signal_plans

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `intersection_id` | `UUID` | No | FK → intersections.id | Intersección del plan. |
| `name` | `VARCHAR(150)` | No | — | Nombre descriptivo. |
| `phases` | `JSONB` | No | — | Lista de fases del plan; estructura JSON validada por la aplicación. |

## traffic_predictions

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `road_segment_id` | `UUID` | No | FK → road_segments.id | Tramo asociado. |
| `prediction_timestamp` | `TIMESTAMP WITH TIME ZONE` | No | — | Instante en que se generó la predicción. |
| `target_timestamp` | `TIMESTAMP WITH TIME ZONE` | No | — | Instante para el que se predice. |
| `predicted_volume` | `FLOAT` | No | — | Volumen estimado; conservar la unidad/granularidad del modelo. |
| `model_version` | `VARCHAR(100)` | No | — | Identificación de la versión del modelo. |

## simulation_scenarios

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `name` | `VARCHAR(150)` | No | — | Nombre descriptivo. |
| `description` | `VARCHAR(1000)` | No | — | Descripción de la fuente o escenario. |
| `configuration` | `JSONB` | No | — | Parámetros del escenario en JSON. |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | No | — | Instante de creación. |

## simulation_results

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `scenario_id` | `UUID` | No | FK → simulation_scenarios.id | Escenario de simulación. |
| `road_segment_id` | `UUID` | No | FK → road_segments.id | Tramo asociado. |
| `travel_time` | `FLOAT` | No | — | Tiempo de viaje; unidad según contrato del simulador. |
| `average_speed` | `FLOAT` | No | — | Velocidad media; unidad a documentar con la fuente o simulador. |
| `delay` | `FLOAT` | No | — | Demora simulada; unidad según contrato del simulador. |
| `queue_length` | `FLOAT` | No | — | Longitud de cola; especificar metros o vehículos según el adaptador. |
| `emissions` | `JSONB` | No | — | Indicadores de emisiones; claves y unidades según simulador. |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | No | — | Instante de creación. |

## traffic_aggregates

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `natural_key` | `VARCHAR(500)` | No | UQ | Clave lógica compuesta serializada para evitar duplicados. |
| `dataset_id` | `VARCHAR(100)` | No | — | Identificador del dataset; no es una FK. |
| `source_record_id` | `VARCHAR(128)` | No | — | Identificador del registro original. |
| `source_provider` | `VARCHAR(200)` | No | — | Proveedor de la fuente. |
| `source_country` | `VARCHAR(80)` | No | — | País de origen. |
| `source_region` | `VARCHAR(100)` | Sí | — | Región de origen cuando está disponible. |
| `source_location_id` | `VARCHAR(120)` | No | — | Identificador de ubicación de origen; no es una FK. |
| `source_location_name` | `VARCHAR(200)` | No | — | Nombre de ubicación según la fuente. |
| `period_start` | `DATE` | No | — | Fecha inicial del periodo original. |
| `period_end` | `DATE` | No | — | Fecha final del periodo original. |
| `temporal_granularity` | `VARCHAR(40)` | No | — | Granularidad original (por ejemplo, mensual o franja); no impone un intervalo. |
| `vehicle_category` | `VARCHAR(100)` | No | — | Categoría vehicular según la fuente. |
| `vehicle_count` | `INTEGER` | No | — | Conteo de vehículos del periodo/categoría. |
| `dataset_scope` | `VARCHAR(80)` | No | — | Ámbito de datos; catálogo de valores en DatasetScope, no ENUM SQL. |
| `metadata_json` | `JSONB` | No | — | Metadatos de procedencia y transformación. |
| `ingestion_run_id` | `VARCHAR(80)` | Sí | — | Referencia textual opcional a una ingesta, sin FK declarada. |

## traffic_locations

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `dataset_id` | `VARCHAR(100)` | No | UQ conjunta | Identificador del dataset; no es una FK. |
| `source_location_id` | `VARCHAR(120)` | No | UQ conjunta | Identificador de ubicación de origen; no es una FK. |
| `name` | `VARCHAR(200)` | No | — | Nombre descriptivo. |
| `type` | `VARCHAR(80)` | No | — | Tipo de ubicación. |
| `operator` | `VARCHAR(250)` | Sí | — | Operador de la ubicación. |
| `status` | `VARCHAR(100)` | Sí | — | Estado de la ubicación o ejecución; vocabulario de la aplicación. |
| `geometry` | `geometry(POINT,4326)` | No | — | Geometría espacial con SRID 4326; coordenadas longitud/latitud. |
| `properties_json` | `JSONB` | No | — | Propiedades adicionales de la ubicación y CRS de origen. |

## dataset_ingestion_runs

| Campo | Tipo SQL | Nulo | Claves | Significado |
|---|---|---|---|---|
| `id` | `UUID` | No | PK | Identificador de la fila. |
| `dataset_id` | `VARCHAR(100)` | No | — | Identificador del dataset; no es una FK. |
| `started_at` | `TIMESTAMP WITH TIME ZONE` | No | — | Inicio de ejecución con zona horaria. |
| `finished_at` | `TIMESTAMP WITH TIME ZONE` | Sí | — | Fin de ejecución; nulo mientras no se registra. |
| `status` | `VARCHAR(40)` | No | — | Estado de la ubicación o ejecución; vocabulario de la aplicación. |
| `files_processed` | `INTEGER` | No | — | Cantidad de archivos procesados. |
| `rows_read` | `INTEGER` | No | — | Filas leídas. |
| `rows_valid` | `INTEGER` | No | — | Filas válidas. |
| `rows_rejected` | `INTEGER` | No | — | Filas rechazadas. |
| `rows_inserted` | `INTEGER` | No | — | Filas insertadas. |
| `rows_updated` | `INTEGER` | No | — | Filas actualizadas. |
| `duplicates` | `INTEGER` | No | — | Duplicados detectados. |
| `error_message` | `TEXT` | Sí | — | Descripción del error, si se registra. |

## Interpretación y limitaciones

`natural_key` concatena dataset_id, source_record_id, source_location_id, period_start y vehicle_category. `DatasetScope` distingue peru_official_demo, huancayo_local_historical y huancayo_local_current en la aplicación; la base almacena texto.

Los rangos se validan parcialmente en el dominio y no mediante CHECK SQL. Los campos JSONB no tienen un esquema JSON impuesto en la base. La referencia ingestion_run_id requiere mejorar el enlace entre ejecuciones y filas; su presencia no acredita trazabilidad completa.

Consultar [integridad e índices](physical-model.md) y [modelo relacional](relational-model.md).
