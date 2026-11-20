# Dictamen integrado de calidad y seguridad

Fecha de corte: 20/11/2026. Se basa en la [auditoría FURPS+](01_auditoria_furps.md), su [verificación](03_auditoria_implementacion_furps.md), la [auditoría OWASP](04_auditoria_owasp.md) y su [verificación](06_auditoria_implementacion_owasp.md).

| Aspecto | Dictamen | Fundamento |
| --- | --- | --- |
| Calidad FURPS+ | Cumple parcialmente como prototipo | 12/20 en la escala interna; 83 pruebas backend aprobadas, 12 PostgreSQL omitidas; frontend compilado. |
| Seguridad OWASP | Cumple parcialmente para staging | Autenticación de escritura y CORS probados; dependencias y alertas pendientes de evaluación. |
| Funcionalidad existente | Conservada en las pruebas disponibles | Se separó la ejecución SUMO mediante puerto y casos de uso y se mejoró el espaciado y anuncio del estado de UI; no cambiaron datos ni contratos HTTP. |
| Riesgo operativo | Medio para staging, alto para producción | La base y SUMO en nube no tienen una prueba integral de carga/recuperación; autenticación y vigilancia son básicas. |

**Recomendación final: no apto para producción.** El despliegue académico puede seguir utilizándose con su etiqueta de prototipo y advertencias científicas. Antes de un uso operacional se requieren aforos actuales y geometría oficial, pruebas de base y carga representativa, auditoría de dependencias, control de intentos de login y alertamiento. Los cambios implementados no convierten la simulación sintética en una predicción validada.
