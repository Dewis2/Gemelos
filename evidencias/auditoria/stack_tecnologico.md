# Tecnologías detectadas

| Capa | Tecnología | Evidencia |
| --- | --- | --- |
| API | Python ≥3.12, FastAPI, Pydantic, SQLAlchemy, Alembic | `backend/pyproject.toml` |
| Datos | PostgreSQL/PostGIS, psycopg | `backend/pyproject.toml`, `docker-compose.yml` |
| Web | React 19, TypeScript, Vite 6, React Router, Leaflet | `frontend/package.json` |
| Analítica | pandas, scikit-learn, joblib | `backend/pyproject.toml`, `ml/` |
| Simulación | SUMO, activos OSM versionados | `simulation/sumo/`, `deploy/Dockerfile.staging.backend` |
| Despliegue | Docker, Render, GitHub Actions | `render.yaml`, `deploy/`, `.github/workflows/` |
