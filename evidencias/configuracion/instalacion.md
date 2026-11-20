# Instalación reproducible

1. Clonar `https://github.com/Dewis2/Gemelos.git`.
2. Para el entorno integrado local, ejecutar `docker compose up --build` desde la raíz y seguir `README.md` para URLs y carga inicial.
3. Para desarrollo separado, crear un entorno Python 3.12, instalar `backend` con extras `dev`, ejecutar `npm ci` en `frontend` y seguir las instrucciones de los README de cada servicio.
4. Verificar `python -m pytest backend/tests -q`, `npm --prefix frontend run test` y `npm --prefix frontend run build`.

El repositorio no distribuye contraseñas de Render.
