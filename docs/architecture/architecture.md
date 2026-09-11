# Arquitectura del sistema

## Dos vistas complementarias

La arquitectura hexagonal gobierna el código del backend: el dominio permanece
independiente y la aplicación solo conoce contratos. FastAPI y MQTT conducen casos
de uso; PostgreSQL/PostGIS, scikit-learn/joblib, TraCI y MQTT implementan puertos de
salida. El archivo `container.py` es la raíz de composición donde se eligen adaptadores.

La vista Edge–Cloud describe el despliegue: un colector edge normaliza eventos, el
broker los desacopla y el núcleo coordina persistencia, predicción y simulación. En
esta PoC no se afirma la existencia de sensores, nube operativa ni ejecución en
tiempo real.

## Reglas de dependencia

1. `domain` no importa frameworks ni infraestructura.
2. `application` importa dominio y define puertos.
3. `adapters` implementa esos puertos y traduce formatos externos.
4. `infrastructure` contiene configuración, ORM y arranque técnico.
5. La inyección de dependencias ensambla todo en el borde de la aplicación.

## Estado actual

El adaptador en memoria permite probar la API sin servicios. PostgreSQL/PostGIS está
modelado y migrado, pero su selección en la raíz de composición queda como siguiente
paso. El adaptador SUMO requiere red validada; el adaptador ML requiere un artefacto
entrenado. Son fallos controlados, no resultados simulados presentados como reales.

