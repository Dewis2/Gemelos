# Política y niveles de datos

## A. Dataset académico externo

**Metro Interstate Traffic Volume**, UCI Machine Learning Repository, contiene
48 204 observaciones horarias (DOI: `10.24432/C5X60B`). Sus observaciones pertenecen
a Minnesota, Estados Unidos, y solo sirven para experimentación técnica del pipeline.
No constituyen evidencia sobre Huancayo ni deben mezclarse con una evaluación local.

## B. Benchmark histórico de Huancayo

`reference/huancayo_historical_counts.csv` transcribe únicamente los nueve valores
proporcionados del *Plan Regulador de Rutas de Transporte Urbano* de la Municipalidad
Provincial de Huancayo (2013). Se conserva año, fuente y uso permitido como metadatos.

> **Estos aforos son históricos y NO representan el tráfico de Huancayo en 2026.**

## C. Dataset local actual

No existe todavía en el repositorio. `local_2026/` es solo un marcador: pendiente
de campaña de aforo o acceso a datos oficiales actuales. Nunca se deben presentar
datos sintéticos o benchmarks externos como mediciones locales actuales.
