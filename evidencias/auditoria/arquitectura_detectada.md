# Arquitectura detectada

El backend separa `domain`, `application`, `adapters` e `infrastructure`. El frontend separa `domain`, `application`, `infrastructure` y `presentation`. El navegador usa un gateway HTTP; FastAPI traduce solicitudes a casos de uso. La ejecución exploratoria SUMO ahora atraviesa `ExploratorySimulationPort` y dos casos de uso. El contenedor compone los adaptadores. La existencia de estas capas no demuestra por sí sola desempeño, seguridad ni calibración científica.
