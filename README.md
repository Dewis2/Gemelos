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
frontend/      dashboard React mínimo
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

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e "./backend[dev]"
cp .env.example .env
```

Cambie la contraseña local del ejemplo si el servicio será accesible fuera de la
máquina. Nunca confirme `.env` en Git.

## Ejecución

Backend:

```bash
python -m uvicorn main:app --app-dir backend/src --reload
```

Abra `http://localhost:8000/docs`. En la composición actual, la API usa el adaptador
en memoria para poder arrancar sin servicios; el proceso pierde esos datos al cerrar.
La migración PostGIS y sus adaptadores están preparados para conectarse en la siguiente
iteración de la raíz de composición.

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
- Datos locales actuales: pendientes.
- Modelo entrenado y evaluación: pendientes.
- Integración persistente seleccionada en runtime: pendiente; la PoC usa memoria.
- Broker conectado al ciclo de vida de FastAPI: pendiente.
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
