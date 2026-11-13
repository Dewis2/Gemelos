# Simulación exploratoria OSM / SUMO

Este módulo ejecuta tres escenarios de demanda **sintética** en una red de
OpenStreetMap alrededor de la Av. Ferrocarril, Huancayo. Es un experimento de
funcionamiento del simulador; no está calibrado con aforos locales y sus cifras no
representan el tránsito observado o futuro de 2026.

## Reproducir en Windows

Desde la raíz del repositorio, con el entorno virtual del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r simulation\requirements.txt
.\.venv\Scripts\python.exe simulation\build_osm_exploration.py
```

La instalación de `eclipse-sumo` incluye `sumo`, `netconvert`, `duarouter` y las
herramientas de Python. También se puede definir `SUMO_HOME` si SUMO está instalado
por separado. Para abrir la ejecución base en la interfaz gráfica:

```powershell
$sumoHome = .\.venv\Scripts\python.exe -c "import sumo; print(sumo.SUMO_HOME)"
& "$sumoHome\bin\sumo-gui.exe" -c simulation\sumo\configuration\osm-normal.sumocfg
```

El comando reconstruye la red, genera las rutas, ejecuta SUMO y actualiza el
reporte y el GeoJSON consumidos por la página **Escenarios** del frontend. Los
archivos de salida detallados y el log quedan en `simulation/sumo/outputs/` y no
se publican en Git. La extracción OSM, la red `.net.xml`, las rutas `.rou.xml` y
los archivos `.sumocfg` sí se conservan en el repositorio para repetir la ejecución.

## Diseño del experimento

| Parámetro | Valor |
| --- | --- |
| Área OSM | `-75.220,-12.073,-75.200,-12.060` (oeste, sur, este, norte) |
| Descarga | API OpenStreetMap `/api/0.6/map`, 13 de noviembre de 2026 |
| Conversión | `netconvert` 1.28.0, nombres de calles incluidos |
| Viajes | `randomTrips.py`, automóvil, distancia mínima de 300 m |
| Semilla | `30167` para los tres escenarios |
| Periodo de salidas | 0 a 900 segundos |
| Demanda baja / normal / alta | Una salida cada 8 / 4 / 2 segundos, respectivamente |
| Fin de simulación | 1800 segundos |
| Indicadores | Viajes completados, duración, espera y velocidad media por viaje |

Las medias se calculan sobre los `tripinfo` de los viajes finalizados; la
velocidad de cada viaje es `longitud de ruta / duración`. Las rutas no son
trayectorias medidas y las tasas de salida no se estimaron con aforos. Las
comparaciones solo muestran el comportamiento de este modelo bajo los parámetros
indicados. La red puede contener supuestos de `netconvert` sobre intersecciones y
carriles. No se calcula GEH, porque faltan conteos observados comparables.

## Resultados de la ejecución incluida

| Demanda | Viajes generados y completados | Duración media | Espera media | Velocidad media de viaje |
| --- | ---: | ---: | ---: | ---: |
| Baja | 113 / 113 | 168,61 s | 34,27 s | 36,34 km/h |
| Normal | 225 / 225 | 182,52 s | 42,89 s | 34,37 km/h |
| Alta | 450 / 450 | 192,16 s | 46,67 s | 33,64 km/h |

Los tres escenarios terminaron con cero vehículos pendientes. El reporte JSON
contiene los hashes de la extracción, la red y las rutas, además de los parámetros
de ejecución. Los comentarios de SUMO con marcas de hora y rutas del equipo se
eliminan de los XML publicados para que sus hashes sean estables al regenerarlos.

## Separación de alcance

El backend desplegado sigue usando `FakeTrafficSimulator` para sus endpoints
`/api/v1/scenarios`; sus resultados no son las ejecuciones de SUMO de este
estudio. La página **Escenarios** presenta ambos bloques por separado. La
geometría oficial del corredor y su calibración permanecen pendientes.

El adaptador TraCI en `backend/src/adapters/outbound/sumo/traci_adapter.py` es
una integración opcional distinta de este experimento reproducible.

