# Modelo conceptual

- **Intersection**: nodo vial identificable; su geometría real está pendiente.
- **RoadSegment**: tramo dirigido entre dos intersecciones.
- **DataSource**: origen trazable de una medición (mock, archivo o fuente futura).
- **TrafficMeasurement**: observación temporal asociada a fuente y tramo.
- **TrafficSignalPlan**: conjunto de fases asociado a una intersección.
- **TrafficPrediction**: volumen estimado para un instante objetivo y versión de modelo.
- **SimulationScenario**: configuración explícita de una ejecución what-if.
- **SimulationResult**: indicadores devueltos por simulación para escenario y tramo.

- **TrafficAggregate**: observaciones agregadas de datasets históricos, con procedencia.
- **TrafficLocation**: ubicaciones geográficas de datasets externos.
- **DatasetIngestionRun**: ejecuciones y contadores de ingesta.

Son once entidades: ocho del núcleo en la migración `0001` y tres de demostración
en `0002`. `alembic_version` y los objetos de PostGIS son técnicos y no se cuentan.

Una intersección puede ser inicio o fin de varios tramos y tener varios planes.
Una fuente y un tramo tienen muchas mediciones; un tramo también tiene muchas
predicciones y resultados. Cada resultado pertenece a un escenario y un tramo.

Las tres entidades de demostración no tienen claves foráneas declaradas entre sí
ni hacia el núcleo. `source_location_id` e `ingestion_run_id` son referencias lógicas,
no garantías de integridad referencial. Los peajes externos no equivalen a tramos
de la avenida Ferrocarril.

El backend siembra cuatro nodos y tres tramos técnicos en el repositorio seleccionado
(PostgreSQL o memoria). La semilla persistente no sobrescribe filas existentes. No se trata de
una topología oficial ni de semillas persistentes; sus geometrías siguen nulas.
Las migraciones crean el esquema sin cargar esa red.

Consultar [modelo relacional](relational-model.md), [diccionario](data-dictionary.md)
y [estado de integración](README.md#estado-de-integración).

