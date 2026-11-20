# Plan de remediación OWASP

Base: [auditoría OWASP](04_auditoria_owasp.md). El servicio actual es staging; cada cambio debe conservar lectura pública y ejecución autenticada.

| ID | Riesgo / componentes | Prioridad | Mitigación | Validación | Reversión |
| --- | --- | --- | --- | --- | --- |
| S-01 | Intentos ilimitados de login en `routes.py` | Alta | Diseñar límite de intentos por origen confiable o en el perímetro de Render, con registro de rechazos y sin bloquear a todos los usuarios tras un proxy compartido. | Pruebas de 401, límite, recuperación y login válido detrás del proxy real. | Retirar regla perimetral o revertir middleware, preservando auth. |
| S-02 | Estado de componentes desconocido | Alta | Repetir `npm audit` cuando el registro responda y auditar paquetes Python del artefacto desplegado; registrar versión exacta, aviso y decisión. | Resultado reproducible y CI limpio tras actualizaciones. | Volver a imagen/lock anterior si una actualización rompe pruebas. |
| S-03 | Token de 8 h sin revocación individual | Media | Evaluar expiración menor y rotación de secreto en despliegue; documentar revocación global. | Token expirado 401; token vigente 200; sesión de frontend clara. | Recuperar configuración anterior. |
| S-04 | Sin alertas de autenticación/errores | Media | Registrar eventos sin credenciales y fijar umbral de alerta para errores 5xx y rechazos reiterados. | Prueba de evento y aviso en entorno de staging. | Desactivar alerta; no desactivar logs. |
| S-05 | Cabeceras y dependencias de suministro | Media | Evaluar CSP compatible con Leaflet/Vite, fijar acciones CI por digest y dependencias Python de imagen. | UI web, mapas, API y CI funcionan sin errores CSP. | Revertir política o pin concreto. |

El orden recomendado es S-02 y S-01 antes de declarar seguridad suficiente; después S-03, S-04 y S-05. Ninguna tarea se da por cerrada por redactar este plan.
