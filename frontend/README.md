# Frontend del Gemelo Digital de Huancayo

Interfaz React del producto mínimo viable para consultar datos de movilidad, reproducir históricos, revisar predicciones y ejecutar escenarios. La implementación sigue arquitectura hexagonal para mantener la lógica de aplicación independiente de React y de la API HTTP.

## Requisitos

- Node.js 22 o superior.
- Backend disponible en `http://localhost:8000` o en la URL configurada mediante `VITE_API_URL`.

## Instalación y ejecución

```bash
npm install
npm run dev
```

La aplicación queda disponible en `http://localhost:5173`.

Variables opcionales en `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

Comandos de verificación:

```bash
npm test
npm run build
```

## Arquitectura elegida

La consigna solicita arquitectura hexagonal. En el frontend se aplica con esta dependencia unidireccional:

```text
presentation -> application -> domain
                      ^
                      |
              infrastructure
```

- `src/domain`: modelos y puerto `DigitalTwinGateway`; no importa React ni `fetch`.
- `src/application`: casos de uso y validaciones del PMV.
- `src/infrastructure`: adaptador REST basado en `fetch`.
- `src/presentation`: composición de dependencias y páginas React.
- `src/components` y `src/maps`: adaptadores visuales reutilizables.

React solo conoce la capa de aplicación mediante `ApplicationProvider`. Cambiar el cliente HTTP o usar datos simulados en pruebas no obliga a modificar las páginas.

## Historias de usuario implementadas

| Historia | Vista | Caso de uso | Endpoints principales |
|---|---|---|---|
| HU-01 Consultar tráfico histórico | Demo Perú | Filtrar fuente, región, ubicación y periodo | `GET /api/v1/datasets`, `GET /api/v1/demo/peru/traffic` |
| HU-02 Reproducir datos históricos | Demo Perú | Iniciar, pausar, continuar, detener y reiniciar | `POST /api/v1/demo/peru/replay/*` |
| HU-03 Revisar y solicitar predicción | Predicción | Consultar experimento y solicitar inferencia local | `GET /api/v1/demo/peru/ml`, `POST /api/v1/predictions/traffic-flow` |
| HU-04 Evaluar escenario | Escenarios | Crear configuración y ejecutar simulación | `POST /api/v1/scenarios`, `POST /api/v1/scenarios/{id}/run` |
| HU-05 Supervisar el PMV | Dashboard y Sistema | Consolidar salud, gemelo, datasets y replay | `GET /health`, `GET /api/v1/digital-twin/state` |

## Criterios de alcance

- Los aforos de Huancayo de 2013 siempre se identifican como referencia histórica.
- La inferencia local informa el error real del backend cuando el modelo no está desplegado.
- Un escenario sin red vial puede crearse, pero la interfaz no inventa resultados de simulación.
- El login se mantiene fuera del alcance porque no pertenece a las historias priorizadas del PMV.

La decisión técnica completa está en [`docs/frontend/architecture.md`](../docs/frontend/architecture.md).
