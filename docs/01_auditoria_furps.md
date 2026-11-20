# Auditoría FURPS+ del gemelo digital

Fecha de corte: 20/11/2026. Alcance: código y documentación de `main` hasta `f9b1f98`, más pruebas locales de esta revisión. Escala de evidencia: 0 ausente, 1 inicial, 2 parcial, 3 suficiente para el prototipo y 4 medido en un entorno representativo. Los puntos son una valoración interna, no una certificación.

## Resumen

El proyecto funciona como prototipo web con API, persistencia, ML nacional y simulación exploratoria. No hay datos locales actuales ni geometría oficial para validar el tráfico del corredor. La mayor brecha de calidad es la validación operativa: las pruebas PostgreSQL se omiten sin una base aislada y el ensayo de carga anterior se hizo con ASGI en memoria.

| Dimensión | Puntos / 4 | Evidencia | Brecha y riesgo |
| --- | ---: | --- | --- |
| Funcionalidad | 3 | [Historias y capturas](evidencias/2026-11-18/README.md), rutas REST en `backend/src/adapters/inbound/api/routes.py`, 83 pruebas aprobadas tras el cambio | La inferencia local y la calibración no están disponibles; MQTT extremo a extremo no se acredita en staging. |
| Usabilidad | 2 | Rutas React, etiquetas en formularios, mensajes de error, CSS adaptable y mapa con atribución | No hay evaluación con usuarios ni prueba sistemática de teclado/lector de pantalla. El estado de SUMO aparecía pegado al botón en la captura publicada. |
| Fiabilidad | 2 | 83 pruebas aprobadas tras el cambio, hashes de activos SUMO, timeout de 90 s, límite de una ejecución, copias PostgreSQL restauradas | 12 pruebas PostgreSQL omitidas en este entorno; no hay prueba prolongada de recuperación ni SLO en nube. |
| Rendimiento | 2 | Compilación Vite; sondeo acotado 10/10 GET 200 en noviembre; carga ASGI local documentada | La carga ASGI no mide Render/PostgreSQL/SUMO concurrente. La instancia gratuita puede dormir y producir espera de arranque. |
| Soportabilidad | 3 | Puertos y adaptadores, diagramas, migraciones, CI, pruebas unitarias y guías | Un ZIP antiguo está versionado; Python usa rangos amplios de dependencias; faltaba un inventario de arquitectura real consolidado. |
| **Total** | **12/20** |  | **Cumplimiento parcial para un prototipo; no demuestra calidad productiva.** |

## Pruebas repetidas en esta revisión

- `.venv/Scripts/python.exe -m pytest backend/tests -q`: 83 aprobadas y 12 omitidas tras el nuevo caso de uso; las omitidas requieren PostgreSQL de prueba.
- `npm --prefix frontend run test`: TypeScript y regla de dependencias correctos.
- `npm --prefix frontend run build`: compilación correcta, 112 módulos transformados.
- `npm --prefix frontend audit --omit=dev --json`: no produjo dictamen porque el registro npm cerró la conexión (`ECONNRESET`) en dos intentos. No se interpreta como cero vulnerabilidades.

## Mejoras ordenadas

1. Corregir separación y anuncio accesible del resultado SUMO en la interfaz.
2. Ejecutar la batería PostgreSQL en una base aislada y conservar el resultado.
3. Medir endpoints y ejecución SUMO en un entorno comparable a staging, con límites de carga acordados.
4. Revisar teclado, contraste, estados de carga y mensajes con participantes reales.
5. Registrar versiones exactas y resultados de auditoría de dependencias cuando el registro esté disponible.

Las limitaciones científicas se registran por separado en [PMV2 y PMV3](pmv2-pmv3/README.md); una mejor puntuación de software no sustituye datos observados.
