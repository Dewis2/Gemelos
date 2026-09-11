# Modelo conceptual

- **Intersection**: nodo vial identificable; su geometría real está pendiente.
- **RoadSegment**: tramo dirigido entre dos intersecciones.
- **DataSource**: origen trazable de una medición (mock, archivo o fuente futura).
- **TrafficMeasurement**: observación temporal asociada a fuente y tramo.
- **TrafficSignalPlan**: conjunto de fases asociado a una intersección.
- **TrafficPrediction**: volumen estimado para un instante objetivo y versión de modelo.
- **SimulationScenario**: configuración explícita de una ejecución what-if.
- **SimulationResult**: indicadores devueltos por simulación para escenario y tramo.

No se precarga una topología: hacerlo antes de validar cartografía crearía datos
ficticios. Las cardinalidades y reglas están representadas en claves foráneas de la
primera migración.

