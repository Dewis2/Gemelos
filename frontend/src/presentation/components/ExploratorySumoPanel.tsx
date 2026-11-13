import { useState } from "react";
import report from "../../data/osm-exploratory-report.json";
import { ExploratoryOsmMap } from "../../maps/ExploratoryOsmMap";

const levels = ["baja", "normal", "alta"] as const;
type Level = (typeof levels)[number];
const labels: Record<Level, string> = { baja: "Baja", normal: "Normal", alta: "Alta" };
const number = new Intl.NumberFormat("es-PE", { maximumFractionDigits: 2 });

export function ExploratorySumoPanel() {
  const [level, setLevel] = useState<Level>("normal");
  const selected = report.scenarios[level];

  return (
    <section className="panel osm-simulation-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Red OpenStreetMap · SUMO</p>
          <h3>Simulación exploratoria</h3>
          <p className="muted">Tres ejecuciones reproducibles con viajes sintéticos. El selector compara resultados ya calculados; no son aforos ni predicciones del tráfico real.</p>
        </div>
        <label className="osm-scenario-select">
          Escenario
          <select value={level} onChange={(event) => setLevel(event.target.value as Level)}>
            {levels.map((item) => <option key={item} value={item}>Demanda {labels[item].toLowerCase()}</option>)}
          </select>
        </label>
      </div>

      <div className="osm-simulation-layout">
        <div>
          <ExploratoryOsmMap />
          <p className="source-note">Verde: tramos llamados Avenida Ferrocarril en OSM. Red colaborativa, sin validación municipal. © OpenStreetMap contributors (ODbL).</p>
        </div>
        <div>
          <div className="osm-metrics">
            <span>Viajes completados<strong>{number.format(selected.vehicles_arrived)} / {number.format(selected.routes_generated)}</strong></span>
            <span>Duración media<strong>{number.format(selected.mean_trip_duration_seconds ?? 0)} s</strong></span>
            <span>Espera media<strong>{number.format(selected.mean_waiting_seconds ?? 0)} s</strong></span>
            <span>Velocidad media de viaje<strong>{number.format(selected.mean_trip_speed_kmh ?? 0)} km/h</strong></span>
          </div>
          <p className="source-note">
            Una salida sintética cada {selected.synthetic_departure_interval_seconds} s durante {report.time.departure_end_seconds} s; semilla {report.software.seed}. Los indicadores se calcularon sobre viajes completados.
          </p>
        </div>
      </div>

      <div className="table-scroll">
        <table>
          <thead><tr><th>Demanda</th><th>Viajes</th><th>Duración media (s)</th><th>Espera media (s)</th><th>Velocidad media (km/h)</th></tr></thead>
          <tbody>{levels.map((item) => {
            const row = report.scenarios[item];
            return <tr key={item} aria-current={level === item ? "true" : undefined}>
              <td>{labels[item]}</td>
              <td>{number.format(row.vehicles_arrived)}</td>
              <td>{number.format(row.mean_trip_duration_seconds ?? 0)}</td>
              <td>{number.format(row.mean_waiting_seconds ?? 0)}</td>
              <td>{number.format(row.mean_trip_speed_kmh ?? 0)}</td>
            </tr>;
          })}</tbody>
        </table>
      </div>
      <p className="source-note">SUMO {report.software.sumo.replace("Eclipse SUMO sumo ", "")} · {report.network.passenger_edges} enlaces aptos para automóviles · {report.network.ferrocarril_edges} enlaces identificados como Av. Ferrocarril. La red y las rutas se pueden regenerar desde la extracción OSM incluida en el repositorio.</p>
    </section>
  );
}
