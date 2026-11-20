# Casos de uso observados

Consultar y filtrar tráfico (HU-01); reproducir histórico (HU-02); revisar evidencia de predicción nacional y solicitar inferencia local cuando exista modelo (HU-03); crear/comparar escenarios (HU-04); consultar fuentes y estado, y ejecutar demanda SUMO exploratoria autenticada. Esta última llama `RunExploratorySimulation.execute(level)` a través de `ExploratorySimulationPort`, con prueba de puerto falso.
