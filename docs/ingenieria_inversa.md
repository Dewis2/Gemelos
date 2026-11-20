# Ingeniería inversa del prototipo de gemelo digital

Fecha de corte: 20/11/2026. Esta reconstrucción parte del código de `main` (`f9b1f98`) y de pruebas repetidas en una rama de revisión. Describe el sistema **implementado**, no la arquitectura futura del diagrama de contexto.

## 1 Auditoría e inventario

El repositorio versiona 310 archivos antes de esta revisión. Los módulos principales son `frontend/`, `backend/`, `ml/`, `simulation/`, `edge/`, `data/`, `docs/`, `deploy/` e `infrastructure/`. También existe un `Gemelos-main.zip` versionado que duplica una instantánea antigua y complica reconocer la fuente vigente; el código activo es el árbol Git, no el ZIP. Inventario y stack: [archivos](../evidencias/auditoria/inventario_archivos.md), [tecnologías](../evidencias/auditoria/stack_tecnologico.md) y [arquitectura detectada](../evidencias/auditoria/arquitectura_detectada.md).

## 2 Dependencias

React/Vite/TypeScript consume la API FastAPI. La API depende de Pydantic, SQLAlchemy/Alembic, psycopg y adaptadores para ML y SUMO. PostgreSQL/PostGIS conserva el estado persistente; MQTT existe como adaptador, pero está desactivado en staging. Detalle: [backend](../evidencias/dependencias/backend.md), [frontend](../evidencias/dependencias/frontend.md), [infraestructura](../evidencias/dependencias/infraestructura.md).

## 3 Entorno reconstruido

El desarrollo local admite `docker compose` con PostgreSQL/PostGIS, Mosquitto, API y frontend; también se puede ejecutar API y Vite por separado. Staging usa dos servicios Render y PostgreSQL remoto. `render.yaml` exige autenticación de editor, CORS HTTPS y repositorios SQL. Se documentan nombres de variables, no sus valores secretos. Véanse [instalación](../evidencias/configuracion/instalacion.md), [variables](../evidencias/configuracion/variables_entorno.md), [servicios](../evidencias/configuracion/servicios.md).

## 4 Ejecución y funcionalidad observable

El frontend presenta histórico, mapa, predicción, escenarios, fuentes, sistema y demostración regional. La API expone salud, consultas de datos, estado, predicción, replay, escenarios y ejecución exploratoria SUMO. Las consultas son públicas en staging; escrituras requieren token de editor. Los tres escenarios OSM/SUMO producen 113/113, 225/225 y 450/450 viajes finalizados con semilla 30167. No son aforos ni validación vial. Véanse [salida de backend](../evidencias/ejecucion/backend_logs.md), [salida de frontend](../evidencias/ejecucion/frontend_logs.md) y [rutas](../evidencias/ejecucion/endpoints_detectados.md).

## 5 Dominio y arquitectura real

El dominio modela tramos, intersecciones, fuentes, mediciones, predicciones y escenarios. Los casos de uso de la API usan puertos de persistencia, ML, mensajería y simulación; la interfaz tiene un gateway HTTP detrás de un contrato de dominio. La ejecución exploratoria SUMO ahora atraviesa `ExploratorySimulationPort` y dos casos de uso; la revisión detectó y corrigió un acoplamiento anterior de la ruta REST al ejecutor. Véanse [dominio](../evidencias/analisis/dominio.md), [módulos](../evidencias/analisis/modulos.md), [casos de uso](../evidencias/analisis/casos_uso.md), [arquitectura](../evidencias/analisis/arquitectura_real.md).

## 6 Evaluación y hallazgos

La separación de la lógica de dominio respecto de FastAPI/ORM es comprobable en las pruebas con fakes. La función SUMO exploratoria ya atraviesa un puerto y casos de uso, comprobados con un adaptador falso. Se aprobaron 83 pruebas backend; 12 que requieren PostgreSQL se omitieron en este equipo. El frontend pasó TypeScript y compilación. Falta un registro verificable de auditoría de dependencias; npm devolvió `ECONNRESET`. Véanse [calidad](../evidencias/analisis/calidad_arquitectura.md) y [hallazgos](../evidencias/analisis/hallazgos.md).

## 7 Dictamen

La ingeniería inversa acredita un **prototipo funcional cuya ejecución SUMO ya sigue el puerto de aplicación**. No permite afirmar un gemelo calibrado, un flujo IoT de campo, una aplicación móvil ni reconocimiento de imágenes. El [dictamen FURPS+/OWASP](07_auditoria_final.md) conserva los riesgos técnicos y el [informe PMV](informes/Informe_PMV1_PMV2_PMV3_2026-11-13.docx) conserva la evolución por historias de usuario.
