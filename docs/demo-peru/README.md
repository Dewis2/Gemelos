# Demo Perú con datos oficiales históricos

## 1. Objetivo

Esta modalidad demuestra el recorrido técnico completo de datos históricos oficiales
sin presentarlos como tráfico urbano de la Av. Ferrocarril. La pantalla siempre indica
fuente, periodo y alcance.

## 2. Fuentes y procedencia

| Dataset | Entidad | Periodo real descargado | Licencia publicada |
|---|---|---:|---|
| Flujo vehicular en unidades de peaje | MTC | 2014-01 a 2026-03 | No especificada en el catálogo |
| Unidades de peaje (GeoJSON) | MTC | cortes 2024-12-30 y 2025-06-30 | Catálogo sin licencia; PDF indica ODC Attribution |
| Tráfico Vehicular - CARRETERAS | OSITRAN | 2019-01 a 2026-03 | Open Data Commons Attribution |
| Aforos históricos Huancayo | Municipalidad Provincial de Huancayo | 2013 | NO DETERMINADO |

La discrepancia de licencia del GeoJSON MTC se conserva como limitación. Los recursos
originales no se redistribuyen automáticamente y están ignorados por Git.

## 3. Descargar, inspeccionar e ingerir

Desde la raíz del repositorio:

```powershell
.venv\Scripts\python.exe scripts\demo_peru.py datasets download mtc-toll-flow
.venv\Scripts\python.exe scripts\demo_peru.py datasets download mtc-toll-locations
.venv\Scripts\python.exe scripts\demo_peru.py datasets download ositran-road-traffic
.venv\Scripts\python.exe scripts\demo_peru.py datasets inspect mtc-toll-flow
.venv\Scripts\python.exe scripts\demo_peru.py datasets inspect ositran-road-traffic
.venv\Scripts\python.exe scripts\demo_peru.py datasets ingest mtc-toll-flow --dry-run
.venv\Scripts\python.exe scripts\demo_peru.py datasets find-region JUNIN
```

`--force`, `--limit` y `--verbose` están disponibles donde corresponden. `--dry-run`
valida y normaliza sin insertar. El atajo siguiente descarga únicamente lo que falte
y regenera catálogos y reportes:

```powershell
.venv\Scripts\python.exe scripts\demo_peru.py prepare
```

## 4. Estructura de datos

El puerto `TrafficDatasetPort` ofrece metadatos, periodos, ubicaciones, validación y un
stream de `TrafficAggregate`. El modelo normalizado conserva `dataset_id`, registro de
origen, proveedor, región disponible, ubicación, periodo, granularidad, categoría,
conteo, alcance y todas las columnas originales dentro de `metadata`.

No se crean velocidad, carril, hora ni GPS por vehículo cuando la fuente no los tiene.
Los mappings reales están registrados en `data/reports/*_schema_report.json`.

## 5. PostgreSQL/PostGIS

La migración `0002_peru_demo.py` crea `traffic_aggregates`, `traffic_locations` y
`dataset_ingestion_runs`. `traffic_aggregates.natural_key` es única y permite una
ingesta idempotente. El GeoJSON declara `urn:ogc:def:crs:OGC:1.3:CRS84`; se valida
antes de preparar los puntos PostGIS. El reporte distingue entidades leídas,
insertables e insertadas: nunca marca una inserción que no fue ejecutada.

## 6. Docker y ejecución

```bash
docker compose up --build
```

Compose ejecuta migraciones y levanta PostgreSQL/PostGIS, Mosquitto, FastAPI y React.
Los secretos se reciben por variables de entorno. Abra:

- API: `http://localhost:8000/docs`
- Demo Perú: `http://localhost:5173/demo-peru`

Para materializar todas las ubicaciones validadas en PostGIS después del arranque:

```bash
docker compose exec backend python -m application.cli datasets ingest mtc-toll-locations
```

## 7. Replay y MQTT

Seleccione fuente, ubicación, periodo y velocidad; pulse **Iniciar demostración**.
El replay conserva `original_period` y añade `replay_emitted_at`. Un mes continúa
siendo un mes, aunque se emita cada 1 s o de forma acelerada.

Topics:

- `demo/peru/mtc/traffic`
- `demo/peru/ositran/traffic`
- `demo/peru/digital-twin/state`
- `huancayo/ferrocarril/traffic` (solo referencia/local Huancayo)

## 8. Endpoints

- `GET /api/v1/datasets`
- `GET /api/v1/datasets/{dataset_id}`
- `GET /api/v1/demo/peru/locations`
- `GET /api/v1/demo/peru/traffic`
- `GET /api/v1/demo/peru/junin`
- `GET /api/v1/demo/peru/comparison`
- `GET /api/v1/demo/peru/ml`
- `POST /api/v1/demo/peru/replay/start`
- `POST /api/v1/demo/peru/replay/pause`
- `POST /api/v1/demo/peru/replay/continue`
- `POST /api/v1/demo/peru/replay/stop`
- `POST /api/v1/demo/peru/replay/reset`
- `GET /api/v1/demo/peru/replay/status`
- `GET /api/v1/demo/peru/state`

## 9. Dashboard

La pantalla incluye filtros, KPIs calculados, serie temporal, categorías, mapa Leaflet,
estado técnico y log del flujo. El mapa usa las coordenadas oficiales del GeoJSON; no
dibuja geometría del corredor Huancayo.

## 10. Junín

El descubrimiento usa exclusivamente `DEPARTAMENTO` del flujo y `DEPARTAMEN` del
GeoJSON. Los resultados reales se registran en `data/reports/peru_junin_discovery.json`.
La pertenencia a Junín no convierte un peaje en medición urbana del corredor.

## 11. Experimento ML

```powershell
.venv\Scripts\python.exe ml\experiments\peru_toll_traffic\train.py
```

Predice el total del siguiente mes con división temporal y compara baseline ingenuo,
regresión lineal y Random Forest. Las métricas y la serie real/predicha provienen de la
ejecución y se guardan en `ml/models/demo_peru/metadata.json`. El modelo `.joblib` se
mantiene fuera de Git.

## 12. Limitaciones y separación de ámbitos

- **Datos nacionales:** demuestran pipeline, replay, PostGIS, MQTT, API, dashboard y ML.
- **Huancayo 2013:** referencia local histórica P03/P04/P42; no representa 2026.
- **Av. Ferrocarril actual:** no disponible; es necesaria para calibración y validación.
- MTC/OSITRAN no se inyectan como demanda SUMO de Huancayo.
- Una demo funcional no equivale a validar el modelo de movilidad del corredor.

## 13. Guion para el profesor

1. Ejecute `scripts/demo_peru.py prepare`.
2. Ejecute `docker compose up --build`.
3. Abra **Demo Perú** y seleccione MTC.
4. Active **Junín**, elija un peaje y un periodo.
5. Pulse **Iniciar demostración** y observe estado, eventos, KPIs y gráficos.
6. Revise el experimento ML nacional y sus métricas reales.
7. Cambie a Huancayo y muestre P03/P04/P42 con la advertencia de 2013.
8. Explique que la validación de la Av. Ferrocarril requiere datos locales actuales.
