# Base de datos de Gemelos

Responsable del módulo: Marcelo Alen Morris Cordova.

El proyecto dispone de once tablas PostgreSQL/PostGIS y persistencia configurable de la API y los datos históricos. Esta documentación permite preparar la base y reproducir la ingesta
histórica sin depender de una ruta personal ni compartir contraseñas.

- [Modelo conceptual](conceptual-model.md)
- [Modelo relacional](relational-model.md)
- [Modelo físico e integridad](physical-model.md)
- [Diccionario de datos](data-dictionary.md)
- [Verificación de la instalación de referencia](verification.md)

## Estado de integración

| Componente | Implementado | Pendiente |
|---|---|---|
| Esquema | Migraciones 0001 y 0002, once tablas | Ampliaciones para aforos y validación |
| CLI histórica | SQLAlchemy seleccionable con DEMO_REPOSITORY=sqlalchemy | Mejorar trazabilidad por fila y manejo de fallos |
| Replay | Persiste agregados con SQLAlchemy | Validar broker y recuperación de fallos |
| Consulta histórica | Lee PostgreSQL en modo sqlalchemy | Optimizar filtros para grandes volúmenes |
| API principal | Mediciones, predicciones, escenarios y resultados persistentes | Mantenimiento de catálogos por API |
| Red vial | Semilla idempotente de cuatro nodos, tres tramos y fuente técnica | Cartografía validada |

CORE_REPOSITORY=sqlalchemy conecta el núcleo; DEMO_REPOSITORY=sqlalchemy conecta
los agregados históricos. DATABASE_URL por sí sola no selecciona el modo. Las sesiones
se abren y cierran por operación; las escrituras revierten la transacción si fallan.
La semilla no sobrescribe filas existentes. La fuente technical_test identifica datos
de prueba y no aforos presenciales.

## Requisitos y ubicación

Para el entorno nativo se necesitan Python 3.12+, PostgreSQL 16, PostGIS compatible
y las herramientas de consola PostgreSQL. pgAdmin es opcional. Puede elegirse
cualquier carpeta de instalación; poner sus binarios en PATH facilita los ejemplos.

Para instalar en E:, ubicar allí el repositorio, Python, entorno virtual, motor,
directorio del clúster, cachés, temporales y respaldos. Configurar TEMP/TMP y
PIP_CACHE_DIR antes de instalar paquetes. Si se usa Docker, verificar por separado
la ubicación de su disco de datos: el volumen no se mueve al cambiar el repositorio.
Los scripts compartidos no descargan herramientas ni alteran otros servidores.

## Preparar Python

Desde la raíz del repositorio, en Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e "./backend[dev]"
```

En Linux/macOS, sustituir el primer ejecutable por `python3` y el del entorno por
`.venv/bin/python`. Los comandos siguientes muestran el ejecutable de Windows.

## Opción nativa

1. Instalar los binarios PostgreSQL 16 y PostGIS para esa versión siguiendo su
   distribución. Si ya existe un servidor, elegir un puerto y directorio distintos.
2. Si es un clúster nuevo, inicializarlo con el `initdb` de esa instalación. Ejemplo
   PowerShell con un directorio que todavía no contiene un clúster:

   ```powershell
   $pgData = Read-Host 'Ruta absoluta del nuevo directorio de datos'
   initdb -D $pgData -U postgres --encoding=UTF8 --locale=C --auth=scram-sha-256 -W
   ```

   En `postgresql.conf`, configurar `listen_addresses = '127.0.0.1'` y un puerto
   libre (por ejemplo, `5433`). Arrancar con `pg_ctl -D $pgData -l "$pgData/server.log" -w start`.
   El administrador define la contraseña en el prompt; no escribirla en scripts compartidos.
3. Conectar como administrador: `psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -W`.
   Crear el usuario y base solamente si no existen:

   ```sql
   CREATE ROLE digital_twin LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
   \password digital_twin
   CREATE DATABASE digital_twin OWNER digital_twin;
   \connect digital_twin
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

   La extensión se habilita como administrador para que la aplicación no requiera
   ser superusuario. Si se reutiliza una base, confirmar su propietario y permisos.
4. Crear `.env` a partir de `.env.local.example` solo si todavía no existe:

   ```powershell
   if (!(Test-Path .env)) { Copy-Item .env.local.example .env }
   ```

   Reemplazar los dos `CHANGE_ME`, ajustar host/puerto y guardar la configuración
   local. Una contraseña hexadecimal aleatoria evita caracteres especiales de URL;
   para otras contraseñas, codificar correctamente la parte de contraseña en DATABASE_URL.
5. Aplicar y consultar el esquema:

   ```powershell
   .\.venv\Scripts\python.exe scripts/database.py migrate
   .\.venv\Scripts\python.exe scripts/database.py status
   ```

El script resuelve el repositorio desde su propia ubicación y carga su `.env` aunque
se invoque desde otra carpeta. `--env-file RUTA` permite elegir otra configuración.
Las variables ya exportadas tienen prioridad. `status` es de solo lectura y requiere
PostGIS y las migraciones aplicadas; no arranca el servidor ni crea roles.

## Opción Docker

Usar `.env.example` para Docker, sin sobrescribir un `.env` existente. Configurar la
misma contraseña en POSTGRES_PASSWORD y DATABASE_URL. El host `postgres:5432` sirve
entre contenedores; desde Windows/Linux anfitrión se utiliza el puerto publicado
en localhost. No usar la URL interna de Docker para un backend nativo.

```text
docker compose up -d postgres
docker compose run --rm --no-deps backend alembic upgrade head
docker compose exec postgres psql -U digital_twin -d digital_twin -c "SELECT version_num FROM alembic_version;"
```

Esperar que postgres esté saludable antes de ejecutar migraciones. El backend
habitual también migra al arrancar. Compose fija variables internas como DATA_ROOT;
esas rutas de contenedor no son carpetas del anfitrión. No usar `down -v` si se desea
conservar el volumen. En este perfil de desarrollo POSTGRES_USER es el usuario de
inicialización del contenedor; no equivale al rol restringido de la opción nativa.

## Ingesta histórica

Una vez aplicado el esquema:

```powershell
.\.venv\Scripts\python.exe scripts/database.py ingest-historical
```

Este comando fuerza el repositorio SQLAlchemy para esa ejecución y usa el CSV
pequeño incluido en `data/reference`. Escribe agregados y una ejecución de ingesta;
no descarga datasets externos ni alimenta la tabla de mediciones actuales.

Comprobar desde psql o pgAdmin:

```sql
SELECT dataset_id, COUNT(*), SUM(vehicle_count)
FROM traffic_aggregates
GROUP BY dataset_id;
```

En una base nueva se esperan nueve registros de `huancayo_historical_counts_2013`,
cuya suma es 11892. Repetir la carga sin cambios conserva nueve registros y añade
otro registro de ejecución. Son referencias de 2013, no tráfico actual ni un único
aforo del corredor.

## Respaldo y operación

Con herramientas PostgreSQL compatibles y conexión configurada mediante PGHOST,
PGPORT, PGUSER y PGDATABASE, `pg_dump -W -Fc -f respaldo.dump` solicita la contraseña
sin incluirla en el comando. Restaurar con pg_restore en una base de comprobación
separada y verificar antes de reemplazar datos. Respaldos y directorios de datos
no se versionan. PostgreSQL nativo se inicia y detiene con pg_ctl usando el directorio
correcto; los accesos particulares de una computadora no son parte del repositorio.

## Evidencia y límites

La instalación nativa pasó las comprobaciones de PostgreSQL, CRUD, FK, PostGIS,
ingesta repetida, reinicio y respaldo del 1 de octubre. El 2 de octubre se aprobaron
35 pruebas del backend (seis con PostgreSQL real) y la compilación del frontend.
El recorrido de escenarios se verificó desde la interfaz, mediante SQL y después
de reiniciar la API. Consulte [la evidencia](verification.md) y
[las pruebas reproducibles](testing.md). No se afirma validación física del tráfico.

## Archivos que se comparten

Compartir documentación, scripts y plantillas. Excluir `.env`, contraseñas,
credenciales JSON, pgpass, entornos virtuales, binarios, clústeres PostgreSQL,
respaldos y cachés. El `.gitignore` incluye patrones para estos archivos, pero
no retira secretos que ya estuvieran versionados: revisar el diff antes de publicar.
