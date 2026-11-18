# Evidencias de integración y staging · 18 de noviembre de 2026

## Ejecución local reproducible

| Comprobación | Resultado |
| --- | --- |
| Backend `python -m pytest backend/tests -q` | 81 pasadas, 12 omitidas (PostgreSQL opcional) |
| Frontend `npm --prefix frontend run test` | Dependencias de arquitectura válidas |
| Frontend `npm --prefix frontend run build` | Compilación de producción correcta |
| Ruff y MyPy | Sin errores |
| Imagen Linux de staging | Construcción Docker completada |
| SUMO 1.28 dentro de la imagen Linux | 113, 225 y 450 viajes finalizados en baja, normal y alta |
| SUMO alta con límite de memoria de 512 MiB | 450 viajes finalizados |
| Autenticación local | GET público, POST sin token 401, login válido y POST con token aceptado, token alterado 401 |

El primer arranque del binario SUMO en `python:3.12-slim` reveló bibliotecas
compartidas ausentes (`libX11`, `libXext`, `libXrender`, `libGL`, `libatomic` y
`libexpat`). Se añadieron al Dockerfile y se repitió la ejecución en Linux con
los tres escenarios. El ensayo de 512 MiB ejecutó únicamente el proceso de
simulación; no es una medida del servicio completo conectado a PostgreSQL.

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
producción. Tras configurar las variables de editor y publicar la revisión,
se deben repetir las comprobaciones según
[`docs/pmv2-pmv3/staging-sumo-security.md`](../../pmv2-pmv3/staging-sumo-security.md).

## Alcance científico

No existen aforos locales fechados de 2026 ni geometría oficial utilizable. Por
ello los resultados SUMO solo respaldan funcionamiento exploratorio de software;
no validan ni calibran el tráfico real del corredor.
