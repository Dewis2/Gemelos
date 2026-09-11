# Edge Collector

El colector recibe registros de una fuente autorizada, valida identificadores y
rangos, normaliza el timestamp a UTC y publica JSON en MQTT. Si la publicación
falla, conserva temporalmente el evento en un buffer local para reintento.

`MockCollector` sirve para desarrollo: acepta entradas proporcionadas por el
desarrollador, pero no representa sensores físicos instalados.

