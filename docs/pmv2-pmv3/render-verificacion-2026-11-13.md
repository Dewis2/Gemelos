# Verificación de PostgreSQL de Render — 13 de noviembre de 2026

## Conexión

La conexión externa a `digital_twin_jkbh` respondió desde DBeaver con SSL `require`. La prueba de DBeaver identificó PostgreSQL 18.6 y el controlador PostgreSQL JDBC 42.7.13. La captura aportada por el equipo se conserva en [evidencias/render-dbeaver-conectado-2026-11-13.png](evidencias/render-dbeaver-conectado-2026-11-13.png).

## Respaldo y restauración

Se generó un respaldo PostgreSQL Custom con `pg_dump` 18.4 en una carpeta **fuera del repositorio**:

`C:\Users\Dewis\Documents\Gemelos-respaldos\gemelos-render-2026-11-13.backup`

| Comprobación | Resultado |
| --- | --- |
| Tamaño | 44 585 bytes |
| SHA-256 | `019060a503ea3c323a9aacd6b9124bda00afd38fa61bff646fd87c7b7f88b9cb` |
| `pg_restore --list` | Archivo Custom reconocido |
| Restauración | Completada con `--exit-on-error` en una base local aislada PostgreSQL 18.4 |
| Esquema restaurado | Revisión Alembic `0003`, 13 tablas públicas y procedimiento `sp_register_traffic_measurement` presentes |

El manifiesto del respaldo está junto al archivo `.backup`. La base de restauración de prueba se eliminó después de verificarla y se detuvo el clúster local aislado. El respaldo y su manifiesto se conservan en la carpeta privada indicada.

## Comparación de filas

Se consultaron los conteos de las tablas de aplicación tanto en Render como en la base restaurada. Coincidieron en todas las tablas:

| Tabla | Render | Restauración |
| --- | ---: | ---: |
| `data_sources` | 1 | 1 |
| `dataset_ingestion_runs` | 0 | 0 |
| `intersections` | 4 | 4 |
| `road_segments` | 3 | 3 |
| `simulation_results` | 12 | 12 |
| `simulation_scenarios` | 4 | 4 |
| `traffic_aggregates` | 9 | 9 |
| `traffic_locations` | 0 | 0 |
| `traffic_measurements` | 0 | 0 |
| `traffic_predictions` | 3 | 3 |
| `traffic_signal_plans` | 0 | 0 |

La consulta de Render mostró `alembic_version = 0003`, PostGIS instalado y ambas rutinas de la revisión `0003`. Una llamada de solo lectura a `fn_traffic_summary` respondió `0` mediciones y `0` vehículos para un tramo existente y un intervalo de 2026, coherente con la tabla vacía. **La migración ya estaba aplicada antes de esta verificación; no se volvió a ejecutar.**

Los conteos verifican la restauración a nivel de tablas de aplicación en el momento de la consulta; no sustituyen una comparación fila por fila. Esta verificación tampoco aporta aforos locales de 2026 ni valida la simulación del corredor.
