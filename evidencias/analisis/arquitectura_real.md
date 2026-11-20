# Arquitectura real

Flujo SUMO tras la revisión: navegador → gateway HTTP → ruta FastAPI → `RunExploratorySimulation` → `ExploratorySimulationPort` → `ExploratorySumoRunner` → archivos SUMO → respuesta HTTP. El contenedor ensambla estas piezas. El reporte de solo lectura sigue el mismo esquema con `GetExploratoryReport`. Las reglas de dominio no importan FastAPI ni el binario SUMO.
