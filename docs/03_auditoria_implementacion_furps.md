# Verificación de implementación FURPS+

Fecha de corte: 20/11/2026. Referencia: [plan](02_plan_furps.md).

| ID | Estado | Evidencia y límite |
| --- | --- | --- |
| F-01 | Implementado en la rama de esta revisión | `frontend/src/styles.css` añade separación y ajuste de línea a la barra de SUMO; `ExploratorySumoPanel.tsx` expone el resultado como estado accesible. TypeScript y compilación terminaron correctamente. Falta una comprobación visual de interacción del cambio publicado. |
| F-02 | Pendiente | La batería local informa 12 pruebas omitidas porque no se configuró PostgreSQL de prueba. |
| F-03 | Pendiente | El sondeo público anterior fue 10/10 para GET; no cuantifica capacidad ni ejecución SUMO. |
| F-04 | Pendiente | La revisión estática de etiquetas no equivale a una sesión con usuarios. |
| F-05 | Pendiente | `npm audit` devolvió `ECONNRESET` dos veces; las dependencias Python tienen rangos y no un lock de despliegue. |

La modificación F-01 no cambia dominio, base de datos ni resultados. Tras la revisión arquitectónica de SUMO, el backend aprobó 83 pruebas con 12 omitidas; el frontend pasó su prueba de arquitectura y compilación. La auditoría no declara cerradas las demás brechas.
