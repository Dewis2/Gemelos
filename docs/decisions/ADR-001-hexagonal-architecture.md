# ADR-001: Arquitectura Hexagonal + Event Driven + Edge–Cloud

- Estado: aceptada para la PoC
- Fecha: 2026-09-11

## Contexto

El proyecto debe integrar fuentes que aún pueden cambiar, persistencia geoespacial,
modelos de predicción, SUMO y una interfaz web. Todavía no existen datos locales 2026,
una red vial validada ni infraestructura física confirmada. La arquitectura debe
permitir avanzar sin convertir esas incógnitas en dependencias rígidas.

## Decisión

Usar Arquitectura Hexagonal en el backend, eventos MQTT en los límites de integración
y una vista de despliegue Edge–Cloud. El dominio contiene entidades y reglas puras;
los casos de uso dependen de puertos; FastAPI/MQTT son adaptadores de entrada y
PostgreSQL, ML, SUMO y MQTT son adaptadores de salida.

## Alternativas

Un monolito tradicional sería más corto al inicio, pero mezclaría ORM, API y dominio,
dificultando reemplazos y pruebas sin servicios. Microservicios puros aportarían
aislamiento de despliegue, pero su operación, observabilidad y contratos distribuidos
son prematuros para un equipo universitario y una PoC sin carga medida.

## Consecuencias

Beneficios: desacoplamiento, testabilidad, reemplazo progresivo de sensores, base de
datos, motor ML y SUMO, además de escalabilidad gradual sin partir de microservicios.

Limitaciones: más abstracciones, mayor curva de aprendizaje, contratos adicionales y
complejidad inicial. La raíz de composición y la documentación deberán mantenerse
para que las capas no se conviertan en estructura ceremonial.
