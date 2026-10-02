# Verificación de la instalación de referencia

Responsable: Marcelo Alen Morris Cordova. Entorno nativo de Windows, PostgreSQL
16.15 y PostGIS 3.6.2. Esquema del repositorio `a1cb31a`, migraciones 0001 y 0002.

Este registro resume las comprobaciones ejecutadas el 1 de octubre de 2026.
Se omiten contraseñas, rutas personales y archivos binarios. No equivale a una
suite de integración compartida ni certifica el entorno Docker.

| Comprobación | Resultado observado |
|---|---|
| Motor y extensión | PostgreSQL 16.15; PostGIS 3.6.2 disponibles |
| Alembic | Revisión 0002 |
| Esquema | Once tablas de aplicación presentes |
| CRUD | INSERT, SELECT, UPDATE y DELETE ejecutados sobre mediciones temporales |
| Rollback | Nodos, fuente y tramo de prueba no quedaron almacenados |
| Integridad referencial | Se rechazó la medición con referencias inexistentes |
| PostGIS | Geometría de prueba válida con SRID 4326 |
| Primera ingesta histórica | 9 leídos, 9 válidos, 9 insertados, 0 rechazados |
| Reingesta del mismo archivo | 0 insertados, 9 duplicados detectados |
| Conteo SQL | 9 agregados históricos; suma de vehicle_count = 11892 |
| Reinicio PostgreSQL | Se conservaron los nueve IDs y sus valores |
| Respaldo/restauración | La base temporal restaurada coincidió con los registros originales |
| Dependencias Python | pip check sin incompatibilidades |
| Pruebas existentes de backend | 29 aprobadas; una advertencia de deprecación de Starlette/httpx |

Los nueve registros pertenecen al dataset `huancayo_historical_counts_2013`.
Su suma es una comprobación del contenido histórico y no un conteo actual del
corredor. Las pruebas de backend se ejecutaron en modo memoria, separadas de las
comprobaciones PostgreSQL.

Los originales de esta evidencia se conservaron localmente en los reportes
`verificacion-bd.json`, `verificacion-reinicio.json` y el inventario de dependencias.
El respaldo no se adjunta al repositorio.

El 2 de octubre se verificó además el comando portable `scripts/database.py status`
contra esa instalación, su ejecución desde otra carpeta, el rechazo de la contraseña
de ejemplo y la correspondencia de las once tablas y 85 campos del diccionario con
los modelos y migraciones. La integración posterior se describe a continuación.


## Integración local del 2 de octubre de 2026

Se conectó la API a SQLAlchemy con sesiones por operación y semillas idempotentes.
La consulta histórica lee PostgreSQL en modo DEMO_REPOSITORY=sqlalchemy.

- 35 pruebas aprobadas: 29 existentes y seis sobre PostgreSQL/PostGIS real.
- Base aislada gemelos_integration_test; migraciones aplicadas desde cero.
- CRUD SQL, FK con recuperación posterior, SRID 4326, semillas sin sobrescritura,
  predicciones persistentes e ingesta idempotente.
- Mediciones, escenarios y resultados recuperados con una nueva aplicación.
- Frontend compilado; escenario creado desde el navegador y confirmado por SQL.
- API detenida y reiniciada; escenario recuperado desde la interfaz con tres filas.
- ID de evidencia: 40dc579b-9d1f-48a9-bc3b-d5b637c36e4f.

Los resultados del simulador son marcadores de posición, no métricas físicas.
MQTT y Docker no forman parte de esta ejecución. Persiste una advertencia de
deprecación de Starlette/httpx. Reproducción: [testing.md](testing.md).
Los logs y capturas originales se conservan localmente fuera del repositorio.
