# Ejecución SUMO y seguridad del staging

## Integración

La API ejecuta únicamente `baja`, `normal` o `alta` desde los `.sumocfg` y `.rou.xml`
versionados. Antes de ejecutar, comprueba SHA-256 de red y ruta contra el reporte
publicado. Solo admite una ejecución simultánea. Usa la semilla 30167 y un límite de 90 segundos. Devuelve viajes
insertados/finalizados, duración, espera, pérdida de tiempo y velocidad media de
viaje, calculados desde `tripinfo` y `summary` de SUMO. Los archivos temporales se
eliminan al terminar. La respuesta tiene `study_type: exploratory_uncalibrated`.
La ejecución es sobre la red OSM completa, sin asignación de resultados a los
tres tramos de referencia. No se aceptan rutas, comandos ni parámetros arbitrarios.

Para probar localmente desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m pip install -r simulation\requirements.txt
.\.venv\Scripts\python.exe -m pytest backend\tests\integration\test_exploratory_sumo.py -q
```

## Editor en Render

Las consultas `GET` son públicas. En staging, `POST`, `PUT`, `PATCH` y `DELETE`
requieren token Bearer firmado. `POST /api/v1/auth/login` emite un token de ocho
horas. Se usa una sola cuenta de editor; no hay registro público ni roles.

Antes de publicar la revisión en Render, ejecute:

```powershell
.\.venv\Scripts\python.exe scripts\hash_editor_password.py
```

Elija una contraseña de al menos 16 caracteres y guárdela fuera del repositorio.
En el servicio `gemelos-staging-api` de Render, configure:

| Variable | Valor |
| --- | --- |
| `AUTH_REQUIRED` | `true` |
| `AUTH_USERNAME` | `editor` |
| `AUTH_PASSWORD_HASH` | La línea generada por el script, sin el prefijo `AUTH_PASSWORD_HASH=` |
| `AUTH_SECRET` | La segunda línea generada, sin el prefijo `AUTH_SECRET=`; si Render Blueprint ya generó esta variable, conserve su valor |
| `SUMO_ASSETS_ROOT` | `/app/simulation/sumo` |
| `SUMO_REPORT_PATH` | `/app/frontend/src/data/osm-exploratory-report.json` |

Render ignora `sync: false` en actualizaciones de Blueprints existentes; por eso
`AUTH_PASSWORD_HASH` se debe colocar en el panel del servicio. El servidor falla
al iniciar en staging si faltan credenciales. No introduzca la contraseña ni el
token en variables `VITE_*` o archivos del repositorio. El frontend conserva el
token solo en `sessionStorage` y lo envía en operaciones de escritura.

## Comprobación después del despliegue

1. `GET /health` debe devolver 200; `GET /api/v1/simulations/exploratory` debe devolver el reporte.
2. `POST /api/v1/simulations/exploratory/normal/run` sin token debe devolver 401.
3. Inicie sesión en `/login`; ejecute demanda normal desde `/escenarios` y verifique 225 viajes finalizados y las medias publicadas.
4. Verifique `POST /api/v1/scenarios/{id}/run` devuelve 410 con token; no se publican resultados ficticios por tramo.
5. Ejecute `python scripts/check_staging.py --output docs/evidencias/staging-check.json` para un sondeo acotado de diez GET a `/health` y diez a `/api/v1/digital-twin/state`. Sus latencias solo describen ese momento.

Las pruebas locales de autenticación, CORS y SUMO están en
`backend/tests/integration/test_editor_auth.py` y
`backend/tests/integration/test_exploratory_sumo.py`. GitHub Actions reproduce
las tres ejecuciones con el binario real. Sin datos reales de 2026 ni geometría
oficial, no corresponde publicar GEH/RMSE ni afirmar validación del corredor.
