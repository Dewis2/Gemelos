# Contratos MQTT iniciales

Topics propuestos:

- `huancayo/ferrocarril/traffic/measurements`
- `huancayo/ferrocarril/traffic/speed`
- `huancayo/ferrocarril/events`
- `huancayo/ferrocarril/predictions`
- `huancayo/ferrocarril/digital-twin/state`

Payload de medición:

```json
{
  "source_id": "UUID",
  "road_segment_id": "UUID",
  "timestamp": "2026-09-11T12:00:00-05:00",
  "traffic_volume": 0,
  "average_speed": null,
  "occupancy": null
}
```

Los números del ejemplo describen forma y tipos, no un aforo observado. En producción
se definirá versión de esquema, autenticación, TLS, retención, QoS y política de
reintentos tras medir las necesidades reales.

