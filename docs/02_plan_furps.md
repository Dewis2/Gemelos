# Plan de mejora FURPS+

Base: [auditoría FURPS+](01_auditoria_furps.md). Los cambios se aplican de forma incremental y se comprueban antes de fusionarlos.

| ID | Objetivo y justificación | Prioridad | Riesgo y dependencias | Validación | Reversión |
| --- | --- | --- | --- | --- | --- |
| F-01 | Separar el botón de SUMO del texto de resultado y anunciar el cambio a tecnologías de asistencia. La captura publicada muestra que ambos quedan pegados. | Alta | Bajo; solo frontend. | `npm test`, `npm run build` y revisión visual a ancho de escritorio y móvil. | Revertir el CSS y el atributo de estado. |
| F-02 | Ejecutar las 12 pruebas de integración PostgreSQL omitidas. Evita inferir compatibilidad de la base a partir de pruebas con memoria. | Alta | Medio; requiere base local aislada con PostGIS. | 0 fallos y 0 omisiones por falta de base; registrar comandos y versión. | No se modifica el servicio remoto; descartar la base de prueba. |
| F-03 | Medir latencia con base y SUMO en un entorno representativo, sin asumir que la instancia gratuita soporta producción. | Media | Medio; acordar carga y ventana para no perturbar staging. | Registrar volumen, concurrencia, p50/p95, errores y recursos. | Detener sondeo; no cambia código. |
| F-04 | Hacer recorrido de teclado y lector de pantalla con usuarios y registrar hallazgos. | Media | Bajo; requiere participantes y protocolo. | Lista de tareas, resultados y correcciones verificadas. | Revertir solo cambios de UI que produzcan regresiones. |
| F-05 | Resolver auditoría de dependencias y fijar versiones desplegadas de Python. | Alta | Medio; potenciales incompatibilidades. | Auditoría de paquetes, CI, pruebas, compilación y despliegue de prueba. | Restaurar lock/imagen anterior. |

Orden: F-01, F-02, F-05, F-03 y F-04. F-01 se implementó en esta revisión; F-02 a F-05 conservan estado pendiente hasta tener evidencia. No se cambia el significado de los resultados científicos ni el contrato REST para cumplir este plan.
