# Dependencias del frontend

`frontend/package.json` y `frontend/package-lock.json`: React 19 renderiza vistas, React Router gestiona rutas y Leaflet/React Leaflet muestran mapas. TypeScript y Vite compilan el proyecto. `npm run test` comprueba tipos y reglas de arquitectura; no incluye pruebas automatizadas de interacción. `npm audit --omit=dev` devolvió `ECONNRESET` el 20/11/2026: no existe dictamen de vulnerabilidades de npm en esta revisión.
