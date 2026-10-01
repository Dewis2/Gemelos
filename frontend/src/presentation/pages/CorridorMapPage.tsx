import { useEffect, useState } from "react";
import { COUNT_POINTS, CORRIDOR_FROM, CORRIDOR_NAME, CORRIDOR_SCOPE, CORRIDOR_TO, HISTORICAL_SOURCE } from "../../domain/corridor";
import { CorridorMap } from "../../maps/CorridorMap";
import { useApplication } from "../ApplicationContext";
import { DataProvenanceNotice } from "../components/DataProvenanceNotice";

export function CorridorMapPage() {
  const application = useApplication();
  const [geometryStatus, setGeometryStatus] = useState<string | null>(null);

  useEffect(() => {
    application.loadDashboard().then((overview) => setGeometryStatus(overview.twin.geometry_status)).catch(() => setGeometryStatus(null));
  }, [application]);

  return (
    <div className="feature-page">
      <header className="page-heading">
        <p className="eyebrow">Representación espacial</p>
        <h2>Mapa del corredor</h2>
        <p>{CORRIDOR_NAME}, {CORRIDOR_SCOPE}. Esquema del corredor con los puntos de aforo P03, P04 y P42 y su estado.</p>
      </header>

      <DataProvenanceNotice category="local_historical">{HISTORICAL_SOURCE.label}</DataProvenanceNotice>

      <section className="panel">
        <h3>{CORRIDOR_FROM} → {CORRIDOR_TO}</h3>
        <CorridorMap />
        <p className="source-note">
          Estado de la geometría según el backend: <strong>{geometryStatus ?? "no disponible"}</strong>.
        </p>
      </section>

      <section className="dataset-grid">
        {COUNT_POINTS.map((point) => (
          <article className="panel" key={point.id}>
            <div className="dataset-title">
              <span>Punto de aforo</span>
              <small>{HISTORICAL_SOURCE.year}</small>
            </div>
            <h3>{point.id}</h3>
            <p className="muted">{point.description}</p>
            <p className="empty">
              Geolocalización: pendiente de validación. El repositorio no contiene coordenadas verificadas para este punto.
            </p>
          </article>
        ))}
      </section>
    </div>
  );
}
