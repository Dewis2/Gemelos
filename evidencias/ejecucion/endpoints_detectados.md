# Endpoints detectados

Rutas de `backend/src/adapters/inbound/api/routes.py`: `GET /health`; `POST /api/v1/auth/login`; `GET /api/v1/simulations/exploratory`; `POST /api/v1/simulations/exploratory/{level}/run`; consultas de datasets, tráfico, Junín, ML, replay, estado del gemelo, escenarios y predicción bajo `/api/v1/`. `level` acepta solo baja, normal y alta. En staging, las lecturas son públicas y las escrituras requieren sesión de editor; una prueba anterior verificó HTTP 401 sin token para SUMO. La lista completa está en `/docs` de la API.
