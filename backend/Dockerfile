FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend/src
WORKDIR /app/backend
COPY backend/pyproject.toml ./
COPY backend/src ./src
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./
RUN pip install --no-cache-dir . eclipse-sumo==1.28.0
RUN apt-get update && apt-get install -y --no-install-recommends \
    libx11-6 libxext6 libxrender1 libgl1 libatomic1 libexpat1 \
    && rm -rf /var/lib/apt/lists/*
COPY simulation/sumo /app/simulation/sumo
COPY frontend/src/data/osm-exploratory-report.json /app/frontend/src/data/osm-exploratory-report.json
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --app-dir src --host 0.0.0.0 --port 8000"]
