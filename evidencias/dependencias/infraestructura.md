# Dependencias de infraestructura

`docker-compose.yml` integra servicios locales; `render.yaml` describe API, web estática y PostgreSQL remoto. El Dockerfile de staging instala SUMO y copia sus activos. PostgreSQL/PostGIS, Render y los mosaicos OSM son dependencias externas. MQTT está desactivado en staging (`MQTT_ENABLED=false`). La cuenta gratuita de Render puede dormir por inactividad; el primer sondeo agotó 30 s y el reintento respondió HTTP 200.
