# Servicios y conexiones

Local: PostgreSQL/PostGIS, Mosquitto, FastAPI y Vite mediante Compose. Staging: `gemelos-staging-api`, `gemelos-staging-frontend` y PostgreSQL de Render. El frontend consulta la API mediante `VITE_API_URL`; CORS restringe el origen. La persistencia SQL se selecciona con `CORE_REPOSITORY` y `DEMO_REPOSITORY`. SUMO se limita a tres demandas predefinidas y verifica sus activos por hash.
