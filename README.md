# Gemelo Digital Inteligente para la movilidad urbana en la Av. Ferrocarril

Base tecnológica universitaria de Ingeniería de Sistemas e Informática para representar,
observar, predecir y simular —de forma progresiva— la movilidad del corredor de la
Av. Ferrocarril entre la Av. Giráldez y la Av. Huancavelica, Huancayo, Perú.

> **Estado: prototipo / PMV.** No existen en este repositorio aforos locales actuales
> de 2026, sensores instalados, una red SUMO validada ni resultados experimentales.
> Toda métrica futura deberá acompañarse de datos, método y evidencia reproducible.

## Problema y objetivo

La información de movilidad suele estar fragmentada entre mediciones, modelos y
herramientas de simulación. El proyecto busca construir el núcleo de un gemelo digital
que reciba observaciones autorizadas o simuladas explícitamente, mantenga una
representación vial, estime flujo vehicular, ejecute escenarios *what-if* en SUMO y
exponga resultados comparables mediante REST y un dashboard.

El alcance actual es una PoC de arquitectura y contratos. La cartografía exacta, la
calibración, la evaluación con datos locales, la seguridad productiva y la operación
en tiempo real están por validar.

## Arquitectura

El backend implementa **Arquitectura Hexagonal / Ports and Adapters** y el despliegue
general adopta una vista **Edge–Cloud orientada a eventos**.

```text
Fuente futura / MockCollector → Edge → MQTT → FastAPI / Digital Twin Core
                                                ├─ PostgreSQL + PostGIS
                                                ├─ ML (scikit-learn)
                                                └─ SUMO (TraCI)
                                                       ↓
                                                Dashboard React
```

Diagramas PlantUML: [arquitectura hexagonal](docs/architecture/hexagonal-architecture.puml),
[componentes](docs/architecture/component-diagram.puml),
[despliegue](docs/architecture/deployment-diagram.puml),
[flujo de datos](docs/architecture/data-flow.puml) y
[secuencia](docs/architecture/sequence-diagram.puml).

## Evidencia de arquitectura hexagonal

- `backend/src/domain`: entidades y reglas sin FastAPI, ORM, MQTT, SUMO o ML.
- `backend/src/application/ports`: contratos de entrada y salida.
- `backend/src/application/use_cases`: coordinación de operaciones del gemelo.
- `backend/src/adapters/inbound`: REST y consumidor MQTT.
- `backend/src/adapters/outbound`: memoria, SQLAlchemy, joblib, TraCI y MQTT.
- `backend/src/infrastructure`: configuración, logging, sesión y modelos ORM.

Las dependencias apuntan hacia adentro: los casos de uso conocen `Protocol`, no
implementaciones. `ApplicationContainer` es la raíz de composición que conecta los
adaptadores, por lo que cambiar PostgreSQL, el modelo ML, la fuente o SUMO no obliga
a modificar el dominio.

## Architecture patterns used

### Repository

| Elemento | Archivo |
|---|---|
| Puertos (contratos) | `backend/src/application/ports/outbound/ports.py` |
| Puertos de agregados de demo | `backend/src/application/ports/outbound/traffic_dataset_port.py` |
| Implementación en memoria | `backend/src/adapters/outbound/persistence/memory.py` (`InMemoryStore`) |
| Implementación SQLAlchemy | `backend/src/adapters/outbound/persistence/sqlalchemy_repository.py` |
| Implementación de agregados | `backend/src/adapters/outbound/persistence/demo_repository.py` |

Los casos de uso reciben `TrafficRepository`, `PredictionRepository`,
`ScenarioRepository`, `SimulationRepository` y `RoadNetworkRepository` como `Protocol`,
nunca como clases concretas.

### Dependency Injection

| Elemento | Archivo |
|---|---|
| Raíz de composición (backend) | `backend/src/adapters/inbound/api/container.py` (`ApplicationContainer`) |
| Proveedor para FastAPI | `backend/src/adapters/inbound/api/dependencies.py` (`get_container`) |
| Composición del frontend | `frontend/src/presentation/ApplicationContext.tsx` |
| Aplicación de cliente | `frontend/src/application/DigitalTwinApplication.ts` |

El contenedor instancia los adaptadores y los inyecta en los casos de uso; el frontend
compone `FetchDigitalTwinGateway` detrás de `DigitalTwinGateway`. No hay
`new` de infraestructura dentro de la lógica de negocio.

### Factory Method

| Elemento | Archivo |
|---|---|
| Fábrica de persistencia | `backend/src/adapters/outbound/persistence/factory.py` (`build_traffic_aggregate_repository`) |
| Fábrica de adaptadores de dataset | `backend/src/adapters/outbound/datasets/__init__.py` y `backend/src/application/cli.py` (`adapters(root)`) |
| Fábrica de la topología del corredor | `backend/src/infrastructure/corridor_reference.py` (`build_corridor`) |

`build_traffic_aggregate_repository("memory" \| "sqlalchemy")` sustituye la rama
condicional que antes tenía el composition root, de modo que elegir persistencia no
requiere tocar `HistoricalReplayService` ni el caso de uso.

### Strategy

Strategy se aplica a la **política de ámbito** de cada conjunto de datos de tráfico:
si una respuesta corresponde al aforo histórico local de Huancayo o a una fuente
oficial regional, y qué advertencia debe acompañarla.

| Elemento | Archivo / clase | Responsabilidad |
|---|---|---|
| Abstracción Strategy | `backend/src/application/services/traffic_scope.py` (`TrafficScopeStrategy`, `Protocol`) | Define `key`, `admits(dataset_id)` y `warning()` |
| Estrategia concreta 1 | `backend/src/application/services/traffic_scope.py` (`LocalHistoricalScope`) | Aplica al aforo municipal de 2013; advierte que no representa tráfico actual |
| Estrategia concreta 2 | `backend/src/application/services/traffic_scope.py` (`NationalDemoScope`) | Aplica a MTC y OSITRAN; advierte que no son tráfico urbano del corredor |
| Contexto (selección e intercambio) | `backend/src/application/services/traffic_scope.py` (`TrafficScopeResolver`) | Elige la primera estrategia que admite el conjunto y permite `register(...)` en tiempo de ejecución |
| Consumidor del contexto | `backend/src/application/services/peru_demo.py` (`PeruDemoQueryService.traffic`) | Delega la advertencia a la estrategia resuelta |
| Pruebas | `backend/tests/unit/test_traffic_scope_strategy.py` | Demuestran selección e intercambio |

Esta política estaba antes incrustada como condicional dentro de
`PeruDemoQueryService.traffic`; el refactor no cambia ninguna respuesta, solo hace
explícita la decisión y permite cambiarla sin tocar el servicio.

**Diferencia con Adapter y Dependency Injection.** `TrafficSimulatorPort`
(`FakeTrafficSimulator` / `SumoTrafficSimulator`) y `EventPublisherPort`
(`LoggingEventPublisher` / `MqttEventPublisher`) son adaptadores intercambiables
elegidos **una vez** en la raíz de composición: eso es Adapter + DI, no Strategy.
Strategy exige un contexto que **selecciona** entre estrategias en cada petición, como
hace `TrafficScopeResolver` con `admits(dataset_id)`.

### Adapter

| Elemento | Archivo |
|---|---|
| Entrada REST | `backend/src/adapters/inbound/api/routes.py`, `schemas.py` |
| Entrada MQTT | `backend/src/adapters/inbound/mqtt/consumer.py` |
| Salida ML (joblib) | `backend/src/adapters/outbound/ml/joblib_model.py` |
| Salida SUMO/TraCI | `backend/src/adapters/outbound/sumo/` |
| Salida de persistencia | `backend/src/adapters/outbound/persistence/` |
| Salida de fuentes | `backend/src/adapters/outbound/datasets/` |
| Salida MQTT | `backend/src/adapters/outbound/mqtt/publisher.py` |

## Unit tests with Fakes/Mocks

Las pruebas de la capa Application se ejecutan **sin PostgreSQL, sin MQTT y sin
servicios externos**: todos los puertos de salida se sustituyen por dobles en memoria.

| Prueba | Qué demuestra |
|---|---|
| `tests/unit/test_use_cases_with_fakes.py::test_prediction_delegates_to_the_port_and_persists` | `PredictTrafficFlow` depende del `MachineLearningPort` y del `PredictionRepository`, no de joblib ni de SQLAlchemy; usa `FakeMachineLearningModel` e `InMemoryStore` |
| `::test_invalid_features_are_rejected_before_calling_the_model` (9 casos) | La regla de negocio del contrato del modelo se ejecuta **antes** de la inferencia; con fakes se comprueba que el modelo no se invoca y que no se persiste nada |
| `::test_prediction_rejects_unknown_road_segment` | El caso de uso valida contra `RoadNetworkRepository` sin tocar la base de datos |
| `::test_prediction_failure_does_not_persist_a_partial_result` | Un fallo del adaptador de ML no deja predicciones parciales |
| `::test_register_measurement_persists_through_the_repository_port` | `RegisterTrafficMeasurement` persiste y publica con `FakeEventPublisher`, sin broker |
| `::test_repository_returns_latest_measurements_in_reverse_chronology` | Comportamiento del repositorio en memoria |
| `::test_domain_rejects_invalid_measurement_state` | Invariantes del dominio sin infraestructura |
| `::test_scenario_run_persists_one_row_per_segment` | Orquestación de escenario con `FakeTrafficSimulator`, sin SUMO |
| `::test_factory_returns_memory_repository_by_default` / `::test_factory_rejects_unknown_persistence` | El Factory Method decide la implementación y falla de forma explícita |
| `tests/unit/test_traffic_scope_strategy.py::test_registering_a_new_strategy_changes_the_selection_at_runtime` | El contexto Strategy cambia la estrategia seleccionada en tiempo de ejecución |
| `::test_service_warning_changes_when_the_strategy_is_swapped` | El intercambio se propaga al servicio real sin alterar el resto del resultado |

Además, `backend/tests/unit/datasets/` comprueba el aislamiento entre fuentes y el
replay histórico, y `backend/tests/integration/test_api.py` cubre los códigos HTTP
(201 predicción, 422 variables inválidas, 404 tramo desconocido, 503 modelo ausente)
con `TestClient` y el contenedor de pruebas.

Ejecución:

```bash
python -m pytest backend/tests -q   # no requiere Docker ni base de datos
```

## Trazabilidad de una predicción

Cada salto del recorrido es localizable en el código:

| # | Paso | Archivo / clase |
|---|---|---|
| 1 | Usuario / Frontend | `frontend/src/presentation/pages/PredictionPage.tsx` |
| 2 | Aplicación de cliente | `frontend/src/application/DigitalTwinApplication.ts` (`predictTraffic`) |
| 3 | Controller / Adapter IN | `backend/src/adapters/inbound/api/routes.py` (`predict_traffic`) y `schemas.py` (`PredictionCreate`) |
| 4 | Input Port | `backend/src/application/ports/inbound/use_cases.py` (`PredictionCommand`) |
| 5 | Use Case | `backend/src/application/use_cases/predictions.py` (`PredictTrafficFlow`) |
| 6 | Servicio IA (puerto) | `backend/src/application/ports/outbound/ports.py` (`MachineLearningPort`) |
| 7 | Adapter OUT de IA | `backend/src/adapters/outbound/ml/joblib_model.py` (`JoblibTrafficModel`) |
| 8 | Regla de negocio | `backend/src/domain/value_objects/traffic_features.py` (`TrafficFeatures`) |
| 9 | Output Port | `PredictionRepository` y `RoadNetworkRepository` en `ports/outbound/ports.py` |
| 10 | Adapter OUT / Persistencia | `backend/src/adapters/outbound/persistence/memory.py` o `sqlalchemy_repository.py` |
| 11 | Respuesta | `PredictionResponse` en `schemas.py` → `PredictionPage` |

El orden alfabético de las variables de entrada es parte del contrato: el paso 7
construye el vector con `sorted(features)`, igual que el entrenamiento.

Recorrido equivalente de una consulta de tráfico, donde se ve el Strategy:

```text
GET /api/v1/demo/peru/traffic?dataset_id=...
  -> routes.py (Adapter IN)                          TrafficDatasetPort
  -> PeruDemoQueryService.traffic                    contexto
  -> TrafficScopeResolver.resolve(dataset_id)        Strategy: selecciona
  -> LocalHistoricalScope | NationalDemoScope         Strategy: ejecuta
  -> TrafficDatasetPort.stream_measurements          Adapter OUT
  -> TrafficAggregateRepositoryPort.add              Repository
  -> respuesta con la advertencia de la estrategia
```

## Stack

- Python 3.12+, FastAPI, Pydantic, SQLAlchemy y Alembic.
- PostgreSQL 16 con PostGIS.
- pandas, NumPy, scikit-learn y joblib.
- Eclipse Mosquitto y paho-mqtt.
- SUMO y TraCI (instalación opcional y separada en esta fase).
- React, TypeScript, Vite y base preparada para Leaflet.
- pytest, pytest-asyncio, HTTPX, Ruff, Black y MyPy.
- Docker, Docker Compose y GitHub Actions.

## Estructura

```text
backend/       núcleo hexagonal, API, ORM, migraciones y tests
data/          política, referencias verificadas y placeholders
docs/          arquitectura, base de datos, API, datasets y ADR
edge/          colector mock, normalización y buffer
frontend/      PMV React con arquitectura hexagonal
ml/            features, división temporal, entrenamiento, evaluación e inferencia
simulation/    estructura SUMO/TraCI sin geometría ficticia
scripts/       comandos auxiliares
```

## Requisitos

- Python 3.12 o superior.
- Node.js 22+ para el frontend.
- Docker Desktop y Compose para PostgreSQL/Mosquitto.
- SUMO solo para ejecutar simulaciones reales, después de validar la red.

## Instalación local

Para preparar el proyecto en una PC nueva, consulte la
[guía completa de instalación y ejecución local](docs/GUIA_INSTALACION_LOCAL.md).

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e "./backend[dev]"
cp -n .env.local.example .env
```

Reemplace `CHANGE_ME` con su contraseña local y ajuste el puerto. Para trabajar
sin PostgreSQL, configure `DEMO_REPOSITORY=memory`; para persistir la demostración,
siga la [guía de base de datos](docs/database/README.md). Nunca confirme `.env` en Git.

## Ejecución

### Demostración del PMV1 con Docker (recomendado)

Requiere **Docker Desktop** en ejecución y las variables de `.env` completas
(`DATABASE_URL` y `POSTGRES_PASSWORD` son obligatorias).

```bash
# 1. Entrar al entorno virtual del proyecto
.venv\Scripts\activate          # Windows PowerShell
source .venv/bin/activate       # Linux / macOS

# 2. Generar el modelo predictivo (descarga MITV-UCI y entrena)
python -m ml.scripts.fetch_mitv
python -m ml.scripts.train_and_publish

# 3. Levantar el sistema completo
docker compose up --build
```

| Servicio | URL |
|---|---|
| **Frontend (grabar aquí)** | http://localhost:5173 |
| Backend / OpenAPI | http://localhost:8000/docs |
| Healthcheck | http://localhost:8000/health |

El paso 2 es necesario porque el artefacto `ml/models/traffic_model.joblib` está
excluido de Git. Sin él, `POST /api/v1/predictions/traffic-flow` responde 503.
Ambos scripts son idempotentes y reproducibles: el primero verifica el perfil del
dataset y el segundo escribe el modelo y `metadata.json` con métricas de la corrida.

### Ejecución del backend sin Docker

Backend:

```bash
python -m uvicorn main:app --app-dir backend/src --reload
```

Abra `http://localhost:8000/docs`. Las plantillas activan CORE_REPOSITORY=sqlalchemy
y DEMO_REPOSITORY=sqlalchemy. Aplique las migraciones antes de iniciar la API.
Cada operación usa su propia sesión PostgreSQL. Para trabajar sin base de datos,
configure ambos valores como memory; ese modo pierde los datos al cerrar.

Frontend:

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

Pruebas y calidad:

```bash
python -m pytest
ruff check backend/src backend/tests ml/src ml/tests edge
mypy backend/src
black --check backend/src backend/tests ml/src ml/tests edge
```

## Docker y base de datos

La guía específica de [base de datos](docs/database/README.md) incluye las once
tablas, el modelo relacional, el diccionario y la instalación nativa o con Docker.
Use `.env.local.example` para un backend nativo y `.env.example` para Compose.

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend alembic upgrade head
```

Compose inicia `backend`, `postgres`, `mosquitto` y `frontend`, todos con healthchecks
donde corresponde. PostgreSQL usa PostGIS y la migración crea `POINT`/`LINESTRING`,
UUID, `TIMESTAMPTZ`, claves foráneas e índices iniciales. No hay secretos de producción.

## API REST inicial

- `GET /health`
- `GET /api/v1/road-segments`
- `GET /api/v1/intersections`
- `POST /api/v1/traffic-measurements`
- `GET /api/v1/digital-twin/state`
- `POST /api/v1/predictions/traffic-flow`
- `POST /api/v1/scenarios`
- `POST /api/v1/scenarios/{scenario_id}/run`
- `GET /api/v1/scenarios/{scenario_id}/results`
- `GET /api/v1/scenarios/compare?scenario_ids=...&scenario_ids=...`

Los schemas Pydantic son independientes del dominio y nunca se retornan modelos ORM.
CORS es configurable. JWT está previsto para una fase posterior; hoy no existen
usuarios, login real ni credenciales.

## MQTT y Edge

El contrato está en [docs/api/mqtt-contracts.md](docs/api/mqtt-contracts.md). El edge
valida UUID y volumen, normaliza el tiempo a UTC, agrega timestamp si falta y usa un
buffer JSONL ante fallo de publicación. `MockCollector` solo entrega registros
proporcionados por el desarrollador: no representa hardware instalado.

Mosquitto permite acceso anónimo únicamente en el entorno local de la PoC. Un
despliegue externo requiere autenticación, TLS, ACL y gestión segura de secretos.

## Machine Learning

El objetivo de IA es predecir flujo vehicular. El pipeline ofrece regresión lineal
como baseline y Random Forest, con división temporal (nunca `random split`) y métricas
MAE, RMSE y R². La evaluación no declara un modelo ganador. XGBoost no se instala por
defecto.

```bash
python -m ml.src.training.train ruta/dataset.csv --model linear
python -m ml.src.training.train ruta/dataset.csv --model random-forest
```

El CSV debe incluir `timestamp` y `traffic_volume` o indicar los nombres por flags.
Los artefactos pesados están ignorados. Sin un modelo presente, el endpoint responde
503 con un mensaje explícito, en lugar de fabricar una predicción.

### Experimento publicado del PMV1

El modelo que sirve `POST /api/v1/predictions/traffic-flow` es un Random Forest
entrenado sobre **MITV-UCI** (Metro Interstate Traffic Volume, Minnesota, EE. UU.,
48 204 registros horarios, DOI `10.24432/C5X60B`) mediante el script reproducible:

```bash
python -m ml.scripts.fetch_mitv          # descarga y verifica el dataset externo
python -m ml.scripts.train_and_publish   # entrena y publica modelo + metadata.json
```

El experimento usa las cuatro variables temporales `day_of_week`, `hour`, `is_weekend`
y `month`. **El orden alfabético de esos nombres es parte del contrato**: el adaptador
`JoblibTrafficModel` construye el vector con `sorted(features)`, y un orden distinto
serviría predicciones incorrectas sin emitir error.

> **Este modelo es una PoC técnica.** Sus observaciones pertenecen a Minnesota, EE. UU.
> No ha sido validado con datos locales actuales de la Av. Ferrocarril y sus volúmenes
> **no son comparables** con los aforos municipales de Huancayo de 2013.

Además, como el modelo no incluye la vía como variable, **el resultado es idéntico para
cualquier segmento del corredor**: el `road_segment_id` solo se exige por contrato del
endpoint.

## Demo con datos oficiales del Perú

La plataforma puede ejecutarse con datos históricos oficiales publicados por MTC y
OSITRAN para demostrar ingesta, validación, almacenamiento, PostGIS, API, replay,
MQTT, Digital Twin Core, dashboard, analítica y un experimento ML independiente.

Los archivos originales se descargan desde la Plataforma Nacional de Datos Abiertos
y permanecen fuera de Git. Para preparar catálogos y reportes reproducibles:

```powershell
.venv\Scripts\python.exe scripts\demo_peru.py prepare
```

Después, inicie el sistema y abra `http://localhost:5173/demo-peru`:

```bash
docker compose up --build
```

La pantalla identifica siempre la fuente, conserva el periodo histórico original y
separa los topics `demo/peru/mtc/traffic`, `demo/peru/ositran/traffic` y
`huancayo/ferrocarril/traffic`.

> **Esta demostración verifica el funcionamiento técnico del software. No constituye
> una validación del modelo de movilidad de la Av. Ferrocarril.**

Los registros P03, P04 y P42 corresponden a aforos históricos y NO representan el
tráfico actual de Huancayo en 2026. Consulte [la guía completa](docs/demo-peru/README.md).

## SUMO / TraCI

`SumoTrafficSimulator` permite cargar escenario, iniciar/detener, fijar demanda,
avanzar pasos y consultar vehículos, velocidad y cola. La ausencia de SUMO/TraCI o
de `.sumocfg` produce un error controlado. `FakeTrafficSimulator` soporta tests.

SUMO queda fuera del contenedor inicial: aún no existe una topología validada y su
instalación elevaría innecesariamente el peso de la PoC. Consulte
[simulation/README.md](simulation/README.md).

## Datasets

Se separan tres niveles en [data/README.md](data/README.md):

1. **Metro Interstate Traffic Volume (UCI, DOI 10.24432/C5X60B):** 48 204
   observaciones horarias de Minnesota, EE. UU.; solo benchmark técnico externo.
2. **Huancayo 2013:** nueve valores verificados del Plan Regulador de Rutas de
   Transporte Urbano, conservados como referencia histórica.
3. **Local 2026:** inexistente por ahora; placeholder pendiente de campaña u acceso
   oficial.

**Estos aforos son históricos y NO representan el tráfico de Huancayo en 2026.**

## Corredor y topología del PMV1

El backend siembra la estructura mínima del corredor mediante
`backend/src/infrastructure/corridor_reference.py`, conectada en el composition root.
Aporta cuatro nodos y tres tramos con UUID deterministas (`uuid5`):

| Tramo | Puntos de aforo asociados |
|---|---|
| Av. Ferrocarril · tramo norte | P03, P04 |
| Av. Ferrocarril · tramo centro | — |
| Av. Ferrocarril · tramo sur | P42 |

La segmentación es **técnica del PMV**, no una división oficial del municipio:

- `geometry` es `null` en todos los tramos y el mapa es un esquema sin coordenadas.
- Los nodos intermedios son **límites técnicos**, no intersecciones ni semáforos verificados.
- `lane_count` y `reference_speed` cumplen el mínimo que exige `RoadSegment`; son
  **valores estructurales no validados en campo**, no atributos levantados en el sitio.
- P03, P04 y P42 siguen siendo puntos de aforo histórico, no segmentos del gemelo.

El sistema no dibuja geometría ficticia mientras la cartografía no esté validada.

## Roadmap

### PMV1 — Gemelo mínimo observable

Estructura hexagonal, BD, API, fuentes de datos, red SUMO pendiente/validada, escenario
básico y visualización mínima.

### PMV2 — Gemelo predictivo

Baseline ML, Random Forest, API de predicción, MQTT, SUMO/TraCI, escenarios *what-if*
y dashboard conectado.

### PMV3 — Gemelo evaluado

Validación con datos locales actuales, seguridad, pruebas de carga, calibración,
dashboard final, reportes y documentación de evidencia.

## Limitaciones actuales

- Topología, carriles, semáforos y geometría del corredor: pendientes de validación.
- Datos locales actuales: pendientes. Los nueve aforos disponibles son de 2013.
- Modelo entrenado: disponible como PoC técnica sobre MITV-UCI (Minnesota). **No está
  validado con datos locales de Huancayo** y no distingue segmentos del corredor.
- Simulación: los escenarios se crean y se ejecutan, pero el adaptador activo no produce
  métricas físicas; las cifras que devuelve son ceros por construcción y la interfaz las
  marca como marcador de posición.
- SUMO/TraCI: implementado como adaptador, no operativo (requiere topología validada y
  un `.sumocfg`; no se incluye en el contenedor).
- Persistencia configurable con CORE_REPOSITORY y DEMO_REPOSITORY; plantillas PostgreSQL.
- MQTT es opcional; el cliente se cierra al terminar FastAPI. No se validó el broker en la instalación nativa.
- Calibración/validación SUMO, seguridad y rendimiento: por medir.
- El mapa muestra un aviso y no dibuja geometría ficticia.

## Equipo

- Zevallos Meza Christian John
- Escobar Cardenas Carlos Leonardo
- Chicmana Vincula Fabricio Renzo
- Ochoa Segovia Brayan José

## Licencia

MIT. Consulte [LICENSE](LICENSE). Las fuentes de datos mantienen sus propias licencias
y condiciones de uso.

## Preparación para GitHub

```bash
git init
git add .
git commit -m "feat: initial digital twin hexagonal architecture"
```

No se realiza `push` automáticamente. Antes de publicar, revise `.env`, licencias de
datos, resultados de CI y cualquier archivo local no intencional.
