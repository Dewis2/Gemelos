# Guía de instalación y ejecución local

Esta guía permite descargar, instalar, ejecutar y comprobar el proyecto **Gemelo
Digital Inteligente para la movilidad urbana en la Av. Ferrocarril** en una PC nueva.

Repositorio: <https://github.com/Dewis2/Gemelos>

## 1. ¿Qué se ejecuta?

El proyecto tiene dos aplicaciones principales:

- **Backend:** API REST desarrollada con Python y FastAPI. Usa el puerto `8000`.
- **Frontend:** interfaz desarrollada con React, TypeScript y Vite. Usa el puerto `5173`.

Para trabajar en desarrollo no es obligatorio instalar PostgreSQL, MQTT ni SUMO. El
backend utiliza almacenamiento en memoria de manera predeterminada. Docker permite
levantar también PostgreSQL y Mosquitto cuando se necesite probar la integración
completa.

## 2. Requisitos previos

Instalar:

- Git.
- Python 3.12 o superior.
- Node.js 22 o superior, que incluye `npm`.
- Docker Desktop, únicamente para la alternativa con contenedores.

Comprobar las versiones desde PowerShell o una terminal:

```text
git --version
python --version
node --version
npm --version
```

Si Windows no reconoce `python`, probar `py --version` y sustituir `python` por `py`
en los comandos de esta guía.

## 3. Descargar el proyecto

Abrir PowerShell o una terminal en la carpeta donde se guardará el proyecto:

```text
git clone https://github.com/Dewis2/Gemelos.git
cd Gemelos
```

La carpeta `Gemelos` es desde ese momento la **raíz del proyecto**. Todos los comandos
siguientes se ejecutan desde esa carpeta, salvo que se indique lo contrario.

## 4. Instalación normal en Windows

Esta es la opción recomendada para desarrollar el frontend y probar el PMV sin Docker.

### 4.1. Preparar el backend

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e "./backend[dev]"
```

No es necesario activar el entorno virtual: los comandos utilizan directamente su
intérprete de Python.

Crear la configuración local solo si el archivo `.env` todavía no existe:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Iniciar el backend:

```powershell
$env:PYTHONPATH="backend/src"
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend/src --reload
```

Dejar esta terminal abierta. Comprobar:

- API: <http://localhost:8000>
- Estado: <http://localhost:8000/health>
- Documentación Swagger: <http://localhost:8000/docs>

### 4.2. Preparar el frontend

Abrir una **segunda ventana de PowerShell**, entrar en la raíz del proyecto y ejecutar:

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

Abrir <http://localhost:5173> en el navegador. Las dos terminales deben permanecer
abiertas mientras se utiliza la aplicación.

Para detener cualquiera de los servidores, volver a su terminal y presionar
`Ctrl + C`.

## 5. Instalación normal en Linux o macOS

Desde la raíz del proyecto:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e "./backend[dev]"
cp -n .env.example .env
export PYTHONPATH="backend/src"
./.venv/bin/python -m uvicorn main:app --app-dir backend/src --reload
```

En una segunda terminal, también desde la raíz:

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

Abrir <http://localhost:5173>.

## 6. Alternativa con Docker

Esta opción ejecuta frontend, backend, PostgreSQL/PostGIS y Mosquitto. Requiere Docker
Desktop abierto.

En Windows PowerShell:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build
```

En Linux o macOS:

```bash
cp -n .env.example .env
docker compose up --build
```

El contenedor del backend ejecuta las migraciones automáticamente. Esperar hasta que
los servicios aparezcan como saludables y abrir:

- Frontend: <http://localhost:5173>
- Swagger: <http://localhost:8000/docs>

Para detener los contenedores:

```text
docker compose down
```

Este comando conserva el volumen de PostgreSQL. No usar `docker compose down -v` si
se desean conservar los datos locales.

## 7. Recorrido de comprobación manual

1. Abrir **Dashboard Huancayo** y comprobar que la API figure como `ok`.
2. Entrar en **Demo Perú**.
3. Seleccionar `Huancayo · Aforos históricos 2013`; deben aparecer nueve registros.
4. Probar `Iniciar demostración`, `Pausar`, `Continuar`, `Detener` y `Reiniciar`.
5. Abrir **Predicción** y comprobar las métricas del experimento nacional.
6. Abrir **Fuentes de datos** y revisar procedencia, periodo y limitaciones.
7. Abrir **Sistema** y comprobar el estado del API y del gemelo digital.

Algunos estados no son errores:

- Las fuentes MTC y OSITRAN pueden mostrar cero registros si no se han descargado sus
  archivos originales. Los archivos grandes y originales no se guardan en Git.
- La predicción local responde que no hay modelo desplegado mientras no exista un
  modelo local validado.
- El mapa no dibuja una geometría de la Av. Ferrocarril mientras no exista una red
  vial validada.
- SUMO no genera resultados reales mientras no exista una topología calibrada.

Estas limitaciones se muestran deliberadamente para no presentar datos inventados.

## 8. Ejecutar las pruebas automáticas

### Windows PowerShell

```powershell
$env:PYTHONPATH="backend/src"
.\.venv\Scripts\python.exe -m pytest backend
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
```

### Linux o macOS

```bash
export PYTHONPATH="backend/src"
./.venv/bin/python -m pytest backend
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
```

El resultado esperado actualmente es:

- 21 pruebas del backend aprobadas.
- Verificación de dependencias de la arquitectura frontend aprobada.
- Compilación de producción del frontend completada.

## 9. Descargar actualizaciones del equipo

Antes de comenzar una nueva sesión de trabajo:

```text
git pull origin main
```

Si cambiaron las dependencias, volver a ejecutar:

```powershell
.\.venv\Scripts\python.exe -m pip install -e "./backend[dev]"
npm --prefix frontend install
```

Cada integrante debe trabajar preferiblemente en una rama propia:

```text
git switch -c nombre-integrante/descripcion-corta
```

Después puede guardar y publicar su trabajo:

```text
git add .
git commit -m "descripción breve del cambio"
git push -u origin nombre-integrante/descripcion-corta
```

No se deben compartir archivos `.env`, contraseñas, entornos `.venv`, carpetas
`node_modules` ni datasets originales pesados.

## 10. Solución de problemas frecuentes

### El puerto 8000 o 5173 ya está ocupado

Detener la aplicación que utiliza el puerto. Como alternativa, iniciar el backend en
otro puerto:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend/src --reload --port 8001
```

Crear `frontend/.env.local` con:

```env
VITE_API_URL=http://localhost:8001
```

Reiniciar el frontend después de modificar este archivo.

### El navegador muestra un error de conexión

Comprobar que ambas terminales sigan abiertas y visitar primero
<http://localhost:8000/health>. Si el backend no responde, revisar el mensaje de error
en su terminal.

### PowerShell impide activar el entorno virtual

No hace falta cambiar la política de ejecución. Utilizar los comandos de esta guía
con `.\.venv\Scripts\python.exe`, que no requieren activar el entorno.

### `npm` o `python` no se reconocen

Cerrar y volver a abrir la terminal después de instalar Node.js o Python. En Windows,
comprobar también que el instalador haya agregado la herramienta a `PATH`.

### CORS bloquea el frontend

Usar los puertos predeterminados `5173` y `8000`. Si se cambia el puerto del frontend,
actualizar `CORS_ORIGINS` en `.env` con su dirección exacta y reiniciar el backend.

## 11. Lista rápida de éxito

La instalación está correcta cuando:

- `GET /health` devuelve `{"status":"ok"}`.
- Swagger abre en el puerto `8000`.
- El frontend abre en el puerto `5173`.
- El dashboard identifica el estado del backend.
- La fuente histórica de Huancayo devuelve nueve registros.
- Las pruebas automáticas terminan sin fallos.
