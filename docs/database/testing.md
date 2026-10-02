# Pruebas reproducibles de PostgreSQL

La suite real está en `backend/tests/integration/test_postgresql.py`. Sin
TEST_DATABASE_URL se omiten esas seis pruebas; las demás usan memoria explícitamente.
No deben ejecutarse sobre la base de trabajo: truncan las once tablas de aplicación
antes de cada caso. La URL debe apuntar a una base desechable cuyo nombre termine
en `_test`. Se conserva esa base al finalizar para facilitar inspección.

## Preparación

Crear una base exclusiva, por ejemplo `gemelos_integration_test`, con el usuario de
aplicación como propietario. Un administrador debe habilitar PostGIS en ella:

```sql
CREATE DATABASE gemelos_integration_test OWNER digital_twin;
-- Reconectar a gemelos_integration_test antes de ejecutar:
CREATE EXTENSION IF NOT EXISTS postgis;
```

Configurar TEST_DATABASE_URL en el proceso con esa conexión, sin escribir la
contraseña en archivos versionados. Desde la raíz del proyecto y con el entorno
Python activo:

```powershell
$env:DATABASE_URL = $env:TEST_DATABASE_URL
$env:DATA_ROOT = (Resolve-Path data).Path
Push-Location backend
python -m alembic upgrade head
Pop-Location
python -m pytest backend/tests -q
```

Al terminar, cerrar esa consola o retirar DATABASE_URL y TEST_DATABASE_URL de su
entorno antes de arrancar la aplicación habitual. La base principal no se limpia.
La instalación de referencia ejecutó las migraciones con una base vacía y obtuvo
35 pruebas aprobadas el 2 de octubre de 2026.

## Cobertura real

1. Revisión Alembic, extensión PostGIS y semillas que preservan cambios existentes.
2. Registro HTTP, rechazo de FK, siguiente operación válida, recuperación tras
   recrear la aplicación y UPDATE/DELETE mediante SQLAlchemy.
3. Escenarios y tres resultados persistidos y recuperados con otra aplicación.
4. Ingesta histórica repetible y lectura HTTP desde la BD con lectura CSV prohibida.
5. Predicciones confirmadas y recuperación de la sesión tras una escritura fallida.
6. Geometría sintética con SRID 4326 en la base de pruebas.

La prueba de predicciones valida almacenamiento con una entidad técnica, no calidad
de un modelo entrenado. El CRUD completo se verifica por SQL/ORM; la API solo expone
las operaciones documentadas, no UPDATE/DELETE de mediciones.

## Recorrido manual de extremo a extremo

1. Activar CORE_REPOSITORY=sqlalchemy y DEMO_REPOSITORY=sqlalchemy en el entorno local.
2. Aplicar migraciones y ejecutar `python scripts/database.py ingest-historical`.
3. Iniciar backend y frontend. Abrir `/escenarios`, asignar un nombre que identifique
   la prueba y pulsar Crear y ejecutar. Registrar el UUID mostrado.
4. Consultar ese UUID en simulation_scenarios y sus filas en simulation_results.
5. Reiniciar únicamente la API, recargar la página y pulsar Recuperar para ese nombre.
6. Comprobar el mismo UUID y tres resultados. No ejecutar nuevamente el escenario:
   cada ejecución añade nuevas filas de resultados.
7. En `/historico`, comprobar las nueve filas de 2013 y su procedencia.

La interfaz conserva la advertencia de simulación técnica. La prueba no valida
SUMO, datos actuales, GEH ni un broker MQTT. El cierre de la aplicación detiene el
replay, cierra MQTT si está habilitado y libera el motor SQLAlchemy.
