# Corrección formativa - Procedimientos almacenados PostgreSQL (PMV2)

## Alcance

Esta rama propone dos rutinas versionadas en Alembic revision `0003`, sobre
las tablas creadas en las revisiones `0001` y `0002`:

- `public.sp_register_traffic_measurement`: PROCEDURE que inserta una
  medición, valida volumen/velocidad/ocupación y conserva validación de claves
  foráneas mediante restricciones del esquema existente.
- `public.fn_traffic_summary`: función PL/pgSQL de reporte por tramo e intervalo
  temporal, con conteo de registros, volumen total y velocidad media.

El patrón Repository de arquitectura hexagonal se conserva. Las rutinas se
verificaron el 13/11/2026 en una base PostgreSQL 18/PostGIS local aislada,
incluyendo entradas inválidas y reversión de `0003`. No se han aplicado a Render.

## Reproducción

1. Disponer de una base separada de pruebas con sufijo `_test` y PostGIS.
2. Ejecutar `python -m alembic upgrade head` desde el contexto de configuración
   descrito en `docs/database/testing.md`.
3. Definir `TEST_DATABASE_URL` apuntando **solo** a esa base aislada.
4. Ejecutar `python -m pytest backend/tests/integration/test_stored_routines.py -q`.
5. Ejecutar la batería global y registrar fecha, entorno, log, resultado, sha
   de commit y evidencia. Revisar también la reversión de la migración.

## Trazabilidad para la rúbrica

Lista de cotejo: «Que el código en base de datos cumpla requisitos de
procedimientos almacenados».

Evidencias propuestas: migración `0003`, tests
`test_stored_routines.py`, pruebas de migración y log real de PostgreSQL.

Resultado: **probado en PostgreSQL local aislado; pendiente de respaldo e
integración en Render**. El resultado completo de pruebas está en
`docs/pmv2-pmv3/README.md`.

## Consideraciones técnicas

Las rutinas no sustituyen filtros de autorización ni políticas de protección
de datos. La función de resumen solo debe exponerse desde casos de uso con
controles de acceso y parámetros validados. Los futuros aforos locales deben
conservar procedencia y fechas; los datos sintéticos nunca se rotulan como
aforos reales de 2026.
