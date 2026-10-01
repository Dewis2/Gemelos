import {
  COUNT_POINTS,
  CORRIDOR_GEOMETRY_NOTICE,
  CORRIDOR_FROM,
  CORRIDOR_SEQUENCE,
  CORRIDOR_TO,
  CORRIDOR_TECHNICAL_SEGMENTS,
  DAY_PERIODS,
  HISTORICAL_SOURCE,
  SEGMENTATION_NOTICE,
} from "../domain/corridor";

const formatNumber = new Intl.NumberFormat("es-PE");

/** Posición relativa de cada punto de aforo según su descripción oficial. */
const relativePosition: Record<string, number> = { P03: 0.16, P04: 0.28, P42: 0.84 };

/** Hitos del corredor, incluidos los dos límites técnicos de la segmentación del PMV. */
const corridorNodes = [
  { label: CORRIDOR_FROM, position: 0.1 },
  { label: "Límite técnico norte", position: 0.31 },
  { label: "Límite técnico sur", position: 0.69 },
  { label: CORRIDOR_TO, position: 0.9 },
];

/** Punto medio de cada tramo técnico, derivado de los hitos que lo delimitan. */
const segmentPosition = [0.205, 0.5, 0.795];

export function CorridorMap() {
  return (
    <section className="corridor-schematic" aria-label="Esquema del corredor Av. Ferrocarril">
      <div
        className="corridor-axis"
        role="img"
        aria-label={`${CORRIDOR_FROM} a ${CORRIDOR_TO} con los tramos técnicos del PMV y los puntos de aforo P03, P04 y P42`}
      >
        <div className="corridor-line" />

        {corridorNodes.map((node) => (
          <span key={node.label} className="corridor-node" style={{ left: `${node.position * 100}%` }} />
        ))}

        {corridorNodes.map((node) => (
          <span key={`${node.label}-label`} className="corridor-node-label" style={{ left: `${node.position * 100}%` }}>
            {node.label}
          </span>
        ))}

        {CORRIDOR_TECHNICAL_SEGMENTS.map((segment, index) => (
          <span
            key={segment.key}
            className="corridor-segment"
            style={{ left: `${segmentPosition[index] * 100}%` }}
            title={segment.referencePoints.length ? `Puntos de aforo de referencia: ${segment.referencePoints.join(", ")}` : "Sin punto de aforo documentado en este tramo"}
          >
            {segment.label}
          </span>
        ))}

        {COUNT_POINTS.map((point) => (
          <span
            key={point.id}
            className="corridor-marker"
            style={{ left: `${relativePosition[point.id] * 100}%` }}
            title={point.description}
          >
            {point.id}
          </span>
        ))}
      </div>

      <div className="corridor-legend">
        <span className="legend-item"><i className="swatch-segment" /> Segmento del gemelo (segmentación técnica del PMV)</span>
        <span className="legend-item"><i className="swatch-point" /> Punto de aforo histórico ({HISTORICAL_SOURCE.year})</span>
      </div>

      <ul className="point-legend">
        {COUNT_POINTS.map((point) => (
          <li key={point.id}>
            <strong>{point.id}</strong>
            <span className="point-description">{point.description}</span>
            <span className="point-values">
              {DAY_PERIODS.map((period) => `${period.label} ${formatNumber.format(point.values[period.id])}`).join(" · ")}
            </span>
          </li>
        ))}
      </ul>

      <p className="source-note">{SEGMENTATION_NOTICE}</p>
      <p className="source-note">
        Posición relativa de cada punto y de cada tramo según la descripción del punto de aforo y el orden del corredor. La distancia real y las coordenadas no están verificadas en el repositorio, por lo que no se asigna latitud ni longitud.
      </p>
      <p className="source-note">{CORRIDOR_GEOMETRY_NOTICE}</p>
      <p className="source-note">
        Corredor: {CORRIDOR_SEQUENCE.join(" → ")}. Fuente de los aforos: {HISTORICAL_SOURCE.provider} — {HISTORICAL_SOURCE.title}, {HISTORICAL_SOURCE.year}.
      </p>
    </section>
  );
}