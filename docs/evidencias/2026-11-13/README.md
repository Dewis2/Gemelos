# Evidencias del informe PMV1 PMV2 PMV3

Fecha de captura: 13 de noviembre de 2026, salvo las dos imágenes del informe anterior indicadas abajo. El código OSM/SUMO se integró en `main` mediante el PR 4, commit `6bb6453`.

| Archivo | Origen y resultado visible |
| --- | --- |
| `pmv1-dashboard.png` | Frontend de staging, `/`: estado del gemelo y corredor esquemático. |
| `pmv1-historico.png` | Frontend de staging, `/historico`: nueve aforos municipales de 2013 y advertencia de periodo. |
| `pmv1-prediccion.png` | Frontend de staging, `/prediccion`: procedencia MITV-UCI y métricas experimentales. |
| `pmv1-sistema.png` | Frontend de staging, `/sistema`: estado y arquitectura. |
| `pmv1-inferencia-2026-10-30.png` | Imagen conservada del informe del equipo del 30/10/2026: inferencia experimental. |
| `pmv1-escenario-2026-10-30.png` | Imagen conservada del informe del equipo del 30/10/2026: tres resultados de escenario con valores cero. |
| `pmv2-escenario-backend.png` | Frontend de staging, `/escenarios`: escenario previamente guardado y sus tres filas, identificadas como marcadores de posición. |
| `sumo-baja.png`, `sumo-normal.png`, `sumo-alta.png` | Frontend local del commit integrado en `main`, `/escenarios`: resultados de las tres corridas SUMO. |
| `pmv3-sumo-staging.png` | Frontend de staging, `/escenarios`: publicación del panel OSM/SUMO después del merge. |
| `main-github-top.png` | Repositorio público `https://github.com/Dewis2/Gemelos/tree/main`: commit de merge y carpetas actualizadas. Es un recorte superior de la captura completa. |
| `pmv3-registro-pruebas-frontend.png` | Captura del registro HTML de la salida real de `npm --prefix frontend test` y `npm --prefix frontend run build`; el registro de texto sin modificar se conserva en `frontend-quality-log.txt`. |

Las capturas de staging proceden de `https://gemelos-staging-frontend.onrender.com`. Las imágenes OSM/SUMO muestran **demanda sintética**, no conteos observados. El informe también incluye la captura de conexión DBeaver existente en `docs/pmv2-pmv3/evidencias/` y remite al acta de respaldo y restauración de Render.
