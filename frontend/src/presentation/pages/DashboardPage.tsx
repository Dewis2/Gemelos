import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { DashboardOverview, DemoMlResult } from "../../domain/models";
import {
  CORRIDOR_FROM,
  CORRIDOR_NAME,
  CORRIDOR_SCOPE,
  CORRIDOR_TO,
  HISTORICAL_YEAR,
  ML_INFERENCE_CONTRACT,
  PROJECT_TITLE,
} from "../../domain/corridor";
import { CorridorMap } from "../../maps/CorridorMap";
import { useApplication } from "../ApplicationContext";
import { DataProvenanceNotice } from "../components/DataProvenanceNotice";
import { PendingKpi } from "../components/PendingKpi";
import { SourceTag } from "../components/SourceTag";

const formatNumber = new Intl.NumberFormat("es-PE");

function KpiCard({
  label,
  value,
  source,
  category,
}: {
  label: string;
  value: string;
  source: string;
  category?: "local_historical" | "regional_demo";
}) {
  return (
    <article className="kpi">
      <span>{label}</span>
      <strong>{value}</strong>
      {category && <SourceTag category={category} />}
      <small className="kpi-source">{source}</small>
    </article>
  );
}

export function DashboardPage() {
  const application = useApplication();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [ml, setMl] = useState<DemoMlResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([application.loadDashboard(), application.getMlExperiment().catch(() => null)])
      .then(([overviewResult, mlResult]) => {
        setOverview(overviewResult);
        setMl(mlResult);
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo cargar el panel."));
  }, [application]);

  if (error) return <div className="error-box" role="alert">{error}</div>;
  if (!overview) return <section className="panel loading-panel"><span className="spinner" />Consultando el sistema…</section>;

  const replay = overview.replay;
  const replayHasFlow = ["running", "paused", "completed"].includes(replay.status) && replay.vehicle_count !== null;
  const modelStatus = ml
    ? `Publicado · ${ml.selected_model}`
    : "Experimento no publicado";

  return (
    <div className="feature-page">
      <header className="page-heading">
        <p className="eyebrow">Gemelo digital inteligente</p>
        <h2>{CORRIDOR_NAME}</h2>
        <p className="project-scope">{PROJECT_TITLE}</p>
        <p>{CORRIDOR_SCOPE}. Huancayo, Junín, Perú. Panel de control del gemelo digital para el análisis predictivo y la simulación de movilidad urbana del corredor.</p>
      </header>

      <section className="corridor-strip">
        <div><span>Corredor</span><strong>{CORRIDOR_NAME}</strong></div>
        <div><span>Tramo</span><strong>{CORRIDOR_FROM} → {CORRIDOR_TO}</strong></div>
        <div><span>Estado del gemelo</span><strong>{overview.twin.status}</strong><small>{overview.twin.geometry_status}</small></div>
        <div><span>Identificación en el backend</span><strong className="corridor-id">{overview.twin.corridor}</strong></div>
      </section>

      <section className="kpi-grid kpi-main" aria-label="Indicadores del corredor">
        {replayHasFlow ? (
          <KpiCard
            label="Flujo vehicular"
            value={`${formatNumber.format(replay.vehicle_count ?? 0)} veh`}
            source={`${replay.source_provider ?? "Fuente no declarada"} · periodo histórico ${replay.current_historical_period ?? "—"}`}
            category={replay.current_dataset?.includes("huancayo") ? "local_historical" : "regional_demo"}
          />
        ) : (
          <PendingKpi
            label="Flujo vehicular"
            reason={`No hay una reproducción histórica activa (estado: ${replay.status}). Inicia una en Demostración técnica o consulte los aforos en Datos históricos.`}
          />
        )}
        <PendingKpi label="Velocidad promedio" reason="El backend no expone un endpoint de velocidad por punto en el PMV1." />
        <PendingKpi label="Nivel de congestión" reason="Requiere velocidad y occupancy medidos; no hay fuente de medición en el corredor." />
        <PendingKpi label="Tiempo estimado de viaje" reason="El backend no expone un endpoint de tiempos de viaje por tramo en el PMV1." />
        <article className="kpi">
          <span>Predicción de flujo</span>
          <strong>{modelStatus}</strong>
          <SourceTag category="ml_experiment" />
          <small className="kpi-source">
            {ml
              ? `Experimento ${ml.training_dataset} · validación local no realizada.`
              : ML_INFERENCE_CONTRACT.datasetUnresolvedNotice}
            <Link to="/prediccion"> Ir a Predicción IA</Link>
          </small>
        </article>
        <article className="kpi">
          <span>Simulación de escenarios</span>
          <strong>{overview.twin.road_segment_count} tramos en el gemelo</strong>
          <SourceTag category="simulated" />
          <small className="kpi-source">
            El escenario se crea y se ejecuta de extremo a extremo, pero el simulador actual no produce métricas físicas.
            <Link to="/escenarios"> Ir a Escenarios</Link>
          </small>
        </article>
        <article className="kpi">
          <span>Fuente y fecha del dato</span>
          <strong className="kpi-source-strong">Ver detalle por bloque</strong>
          <small className="kpi-source">Cada indicador declara su origen; los datos locales del corredor son históricos de {HISTORICAL_YEAR}.</small>
        </article>
      </section>

      <DataProvenanceNotice category="ml_experiment">
        {ML_INFERENCE_CONTRACT.datasetUnresolvedNotice}
      </DataProvenanceNotice>

      <section className="panel">
        <h3>Esquema del corredor</h3>
        <CorridorMap />
      </section>

      <section className="cards dashboard-cards" aria-label="Estado técnico del sistema">
        <article><span>API</span><strong className="status-ok">{overview.health.status.toUpperCase()}</strong><small>{overview.health.stage}</small></article>
        <article><span>Estado del gemelo</span><strong>{overview.twin.status}</strong><small>{overview.twin.geometry_status}</small></article>
        <article><span>Fuentes catalogadas</span><strong>{overview.datasets.length}</strong><small>Con procedencia y limitaciones</small></article>
        <article><span>Reproducción histórica</span><strong>{replay.status}</strong><small>{replay.replay_position} / {replay.replay_total} eventos</small></article>
      </section>

      <section className="journey-grid" aria-label="Secciones del sistema">
        <Link to="/mapa"><span>01</span><strong>Mapa del corredor</strong><small>Esquema Giráldez → Huancavelica con P03, P04 y P42</small></Link>
        <Link to="/historico"><span>02</span><strong>Datos históricos</strong><small>Aforos municipales de {HISTORICAL_YEAR} por punto y franja horaria</small></Link>
        <Link to="/prediccion"><span>03</span><strong>Predicción IA</strong><small>Ejecución del modelo y métricas del experimento</small></Link>
        <Link to="/escenarios"><span>04</span><strong>Escenarios</strong><small>Configuración y ejecución de simulaciones</small></Link>
        <Link to="/fuentes"><span>05</span><strong>Fuentes de datos</strong><small>Procedencia, uso permitido y limitaciones</small></Link>
        <Link to="/sistema"><span>06</span><strong>Sistema</strong><small>Estado de servicios y arquitectura</small></Link>
      </section>
    </div>
  );
}
