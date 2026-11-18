# Evidencias de integración y staging · 18 de noviembre de 2026

## Ejecución local reproducible

| Comprobación | Resultado |
| --- | --- |
| Backend `python -m pytest backend/tests -q` | 82 pasadas, 12 omitidas (PostgreSQL opcional) |
| Frontend `npm --prefix frontend run test` | Dependencias de arquitectura válidas |
| Frontend `npm --prefix frontend run build` | Compilación de producción correcta |
| Ruff y MyPy | Sin errores |
| Imagen Linux de staging | Construcción Docker completada |
| SUMO 1.28 dentro de la imagen Linux | 113, 225 y 450 viajes finalizados en baja, normal y alta |
| SUMO alta con límite de memoria de 512 MiB | 450 viajes finalizados |
| Autenticación local | GET público, POST sin token 401, login válido y POST con token aceptado, token alterado 401 |
| Interfaz local `/escenarios` | Botón de ejecución normal pasó a «Resultado recién calculado por SUMO» y mostró semilla 30167 y hashes de red/ruta |

El primer arranque del binario SUMO en `python:3.12-slim` reveló bibliotecas
compartidas ausentes (`libX11`, `libXext`, `libXrender`, `libGL`, `libatomic` y
`libexpat`). Se añadieron al Dockerfile y se repitió la ejecución en Linux con
los tres escenarios. El ensayo de 512 MiB ejecutó únicamente el proceso de
simulación; no es una medida del servicio completo conectado a PostgreSQL.

La primera prueba desde el navegador local reveló una ruta relativa incorrecta
cuando el backend se iniciaba desde la raíz. Se resolvieron los activos desde
la ubicación del paquete y se repitió la ejecución normal con resultado correcto.
En GitHub Actions, la primera reproducción detectó que Git normalizaba a LF
los XML generados en Windows, por lo que el SHA-256 de bytes difería. El
reporte y el verificador ahora calculan SHA-256 sobre XML con LF canónico.

## Servicio publicado antes de esta revisión

Los resultados JSON adjuntos se tomaron contra la versión que estaba publicada
antes de integrar estos cambios. No verifican todavía el nuevo endpoint SUMO ni
la autenticación en Render.

- [`staging-health-before-deploy.json`](staging-health-before-deploy.json):
  18 respuestas HTTP 200 y dos tiempos de espera en 20 solicitudes GET `/health`.
- [`staging-health-and-db-before-deploy.json`](staging-health-and-db-before-deploy.json):
  10/10 HTTP 200 en `/health` y 10/10 HTTP 200 en
  `/api/v1/digital-twin/state`, con dos clientes concurrentes. Medianas:
  238,76 ms y 228,00 ms, respectivamente.

Estos son sondeos acotados de disponibilidad y latencia; no constituyen una
prueba de capacidad máxima ni sustituyen una evaluación de seguridad de
producción.

## Comprobación publicada en `main`

El 18 de noviembre de 2026, Render marcó **Live** el despliegue automático del
commit `b8b70a4` del PR #5. La captura proporcionada por el propietario del
servicio está en [`render-api-live-main.png`](render-api-live-main.png).
Las tres comprobaciones de GitHub Actions del commit de merge concluyeron en
`success`: calidad, pruebas de backend y preparación de staging.

| Comprobación externa | Resultado |
| --- | --- |
| `GET /health` | HTTP 200, `status: ok` |
| `GET /api/v1/simulations/exploratory` | HTTP 200; `study_type: exploratory_uncalibrated`; JSON idéntico al reporte versionado |
| Escenario normal publicado | 225 viajes finalizados de 225; duración media 182,52 s; espera media 42,89 s; velocidad media 34,37 km/h |
| `POST /api/v1/simulations/exploratory/normal/run` sin token | HTTP 401, mensaje «Inicie sesión como editor.» |
| Preflight CORS desde el frontend para ese `POST` | HTTP 200; autoriza `authorization,content-type` y el origen exacto del frontend |
| `GET /api/v1/digital-twin/state` | HTTP 200; estado `prototype` y geometría `pending_validation` |
| Frontend `/login` | Abre el formulario «Acceso de editor» |
| Frontend `/escenarios` | Muestra los tres niveles de demanda, el botón de ejecución y las métricas publicadas |

El sondeo repetido después del despliegue está en
[`staging-health-and-db-after-deploy.json`](staging-health-and-db-after-deploy.json):
10/10 respuestas HTTP 200 en `/health` y 10/10 en
`/api/v1/digital-twin/state`. Las medianas fueron 234,98 ms y 264,79 ms,
respectivamente, con dos clientes concurrentes. Son valores puntuales, no una
prueba de capacidad.

El propietario del servicio confirmó manualmente que inició sesión como editor
y ejecutó la demanda normal desde `/escenarios` en Render. Las capturas
[`render-sumo-normal-live-overview.png`](render-sumo-normal-live-overview.png) y
[`render-sumo-normal-live-results.png`](render-sumo-normal-live-results.png)
muestran «Resultado recién calculado por SUMO», 225/225 viajes finalizados,
182,52 s de duración media, 42,89 s de espera media y 34,37 km/h de velocidad
media. La respuesta autenticada de la API no se inspeccionó desde este equipo;
la evidencia corresponde a la interfaz del navegador del propietario. No se
almacena la contraseña ni un token en este repositorio. La ejecución local y en
Linux también finalizó los tres escenarios, como consta arriba.

## Alcance científico

No existen aforos locales fechados de 2026 ni geometría oficial utilizable. Por
ello los resultados SUMO solo respaldan funcionamiento exploratorio de software;
no validan ni calibran el tráfico real del corredor.
