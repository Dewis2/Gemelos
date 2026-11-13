# PMV2 y PMV3: implementación y evidencia (13 de noviembre de 2026)

## Alcance verificado

| Trabajo | Estado y evidencia |
| --- | --- |
| Alembic `0003` y rutinas PostgreSQL | Migración, `CALL` y `SELECT` probados en PostgreSQL 18/PostGIS local aislado. Reversión a `0002` y nueva subida a `0003` probadas. En Render se verificó que `0003` y ambas rutinas ya estaban presentes; no se repitió la migración. |
| Respaldo | `scripts/backup_postgres.py` generó un respaldo Custom de Render con cliente 18.4. Se comprobó con `pg_restore --list`, SHA-256 y una restauración completa en una base local aislada. [Acta de verificación](render-verificacion-2026-11-13.md). |
| HU-11, exportación | `scripts/export_evidence.py` exporta mediciones y predicciones en modo lectura. UUID reemplazados por seudónimos HMAC-SHA256; manifiesto con cantidad y SHA-256 de cada CSV. Ensayado con un registro sintético por tabla en base aislada. |
| HU-12, experimentos | Entrenamientos escriben `run_id`, fecha UTC, hash del dataset, hash del modelo y métricas. Ejecución nacional MTC: 8.946 filas de entrenamiento, 2.340 de test temporal, MAE 7.083,46, RMSE 17.657,61, R² 0,9822. Es un experimento nacional de peajes; no valida Av. Ferrocarril. |
| HU-13, aforos locales 2026 | Validador de esquema, procedencia declarada, fechas y duplicados implementado. Sin aforos reales 2026 disponibles: no se entrenó ni validó un modelo local. |
| HU-14, calibración | Métricas GEH y RMSE para pares observación/simulación, con pruebas unitarias. Sin geometría oficial, conteos reales ni simulación SUMO calibrada: no hay resultados de corredor. |
| HU-15, regresión y rendimiento | 91 pruebas del proyecto aprobadas con PostgreSQL local (88 backend); mypy sin errores; frontend `test` y `build` aprobados. Carga acotada: 750 GET, 750 respuestas 200, 103,51 req/s y p95 124,74 ms en ASGI local con repositorios en memoria. Esto no mide Render ni PostgreSQL. Validación de tamaño/valores de escenarios y cabeceras HTTP de protección básica añadidas. |

## Reproducción segura

Usar `.venv/Scripts/python.exe` en Windows desde la raíz del repositorio.

### Respaldo PostgreSQL 18

Configurar `BACKUP_DATABASE_URL` **solo en la sesión local** y ejecutar:

```powershell
.venv/Scripts/python.exe scripts/backup_postgres.py --output C:\ruta-privada\gemelos.backup
& 'C:\Program Files\PostgreSQL\18\bin\pg_restore.exe' --list C:\ruta-privada\gemelos.backup
```

No subir la copia ni la variable de conexión al repositorio. Comprobar el tamaño, el manifiesto y una restauración en una base vacía y aislada antes de considerar el respaldo válido. El archivo de 0 bytes generado anteriormente con `pg_dump` 17 no sirve.

La conexión PostgreSQL de Render ya fue probada en DBeaver con SSL `require`. El respaldo remoto y su restauración de prueba se realizaron mediante las herramientas locales PostgreSQL 18; véase el [acta de verificación](render-verificacion-2026-11-13.md). La copia permanece fuera del repositorio.

### Migración y pruebas de base

Crear una base propia terminada en `_test`, instalar PostGIS y apuntar a ella `DATABASE_URL` y `TEST_DATABASE_URL`. Aplicar `alembic upgrade head`. La fixture de integración trunca tablas: **nunca** apuntar `TEST_DATABASE_URL` a Render o una base con datos que deban conservarse.

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://USUARIO@127.0.0.1:PUERTO/gemelos_pmv_test'
.venv/Scripts/python.exe -m pytest backend/tests -q
```

### Exportación y entrenamiento

Configurar `EXPORT_DATABASE_URL` y una clave local `EXPORT_PSEUDONYM_KEY` de al menos 32 bytes. La exportación crea una carpeta nueva con dos CSV y `manifest.json`. Conservar la clave de seudonimización fuera del repositorio. Los CSV son **seudonimizados**, no anónimos: fechas, tramo y valores pueden requerir revisión adicional antes de compartirlos.

```powershell
.venv/Scripts/python.exe scripts/export_evidence.py --output-dir C:\ruta-privada\export-001
.venv/Scripts/python.exe scripts/validate_local_2026.py C:\ruta-privada\aforos-2026.csv
.venv/Scripts/python.exe scripts/load_test_local.py --requests 750 --concurrency 10
```

El validador solo comprueba estructura y plausibilidad; la autenticidad de la fuente debe acreditarse por separado. Para calibración, `simulation/calibration.py` compara CSV con `road_segment_id`, `period_start` y `vehicle_count` idénticos en ambos archivos.

## Puertas pendientes para completar PMV3

1. Obtener aforos 2026 con procedencia verificable y autorización de uso.
2. Obtener geometría oficial del corredor y red vial utilizable en SUMO.
3. Calibrar la simulación contra aforos observados y publicar GEH/RMSE con conjunto de validación separado.
4. Ejecutar rendimiento y seguridad en un entorno comparable al despliegue real; la carga ASGI local solo cubre lógica de aplicación.

El respaldo PostgreSQL 18 de Render ya se verificó mediante restauración. La revisión `0003` y sus rutinas ya estaban aplicadas en Render; se comprobó `alembic_version` y `pg_proc` sin repetir la migración.

No se fabrican datos locales ni se presentan métricas nacionales como validación del corredor.
