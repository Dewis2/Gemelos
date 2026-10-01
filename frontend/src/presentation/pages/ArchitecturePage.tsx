import { useCallback, useEffect, useMemo, useState } from "react";
import type { DashboardOverview, DemoMlResult } from "../../domain/models";
import { CORRIDOR_SCOPE, ML_INFERENCE_CONTRACT } from "../../domain/corridor";
import { useApplication } from "../ApplicationContext";
import { DataProvenanceNotice } from "../components/DataProvenanceNotice";
import { SourceTag } from "../components/SourceTag";

function PageError({ message }: { message: string }) {
  return <div className="error-box" role="alert">{message}</div>;
}

function LoadingPanel({ label = "Consultando el sistema…" }: { label?: string }) {
  return <section className="panel loading-panel"><span className="spinner" />{label}</section>;
}

type StageStatus = "operativo" | "parcial" | "pendiente";

const STATUS_LABELS: Record<StageStatus, string> = {
  operativo: "Operativo",
  parcial: "Parcial",
  pendiente: "Pendiente",
};

interface Stage {
  name: string;
  role: string;
  status: StageStatus;
  evidence: string;
}

export function ArchitecturePage() {
  const application = useApplication();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [ml, setMl] = useState<DemoMlResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setError(null);
    Promise.all([application.loadDashboard(), application.getMlExperiment().catch(() => null)])
      .then(([overviewResult, mlResult]) => {
        setOverview(overviewResult);
        setMl(mlResult);
      })
      .catch((reason: unknown) =>
        setError(reason instanceof Error ? reason.message : "No se pudo verificar el sistema."),
      );
  }, [application]);

  useEffect(refresh, [refresh]);

  const stages = useMemo<Stage[]>(() => {
    if (!overview) return [];
    const replay = overview.replay;
    const repositoryStatus = replay.technical_status.repository ?? "pending";
    const mqttStatus = replay.technical_status.mqtt ?? "pending";
    return [
      {
        name: "Frontend",
        role: "Vite + TypeScript, presentación y casos de uso de cliente",
        status: "operativo",
        evidence: "Capas hexagonal verificadas por lint en cada compilación.",
      },
      {
        name: "FastAPI",
        role: "API REST del gemelo",
        status: overview.health.status === "ok" ? "operativo" : "parcial",
        evidence: `Healthcheck ${overview.health.status} (${overview.health.stage}).`,
      },
      {
        name: "Casos de uso",
        role: "Aplicación:gemelo, tráfico, predicción y escenarios",
        status: "operativo",
        evidence: `${overview.twin.road_segment_count} tramos y ${overview.datasets.length} fuentes catalogadas.`,
      },
      {
        name: "Machine Learning",
        role: "Random Forest para volumen vehicular a corto plazo",
        status: ml ? "operativo" : "parcial",
        evidence: ml
          ? `${ml.selected_model} · ${ml.rows_total ?? "—"} registros · ${ml.model_version ?? "—"}`
          : "Experimento no publicado por el backend.",
      },
      {
        name: "PostgreSQL / PostGIS",
        role: "Persistencia de agregados y ubicaciones",
        status: repositoryStatus === "loaded" ? "operativo" : "parcial",
        evidence: repositoryStatus === "loaded"
          ? "Ingesta verificada en la reproducción histórica."
          : `Sin escritura registrada todavía (estado: ${repositoryStatus}).`,
      },
      {
        name: "MQTT",
        role: "Publicación de eventos históricos y del gemelo",
        status: mqttStatus === "published" ? "operativo" : "parcial",
        evidence: mqttStatus === "published"
          ? "Eventos publicados durante la reproducción histórica."
          : `Sin publicación registrada en esta sesión (estado: ${mqttStatus}).`,
      },
      {
        name: "SUMO / TraCI",
        role: "Simulación de escenarios",
        status: "pendiente",
        evidence:
          "No operativa: el gemelo usa un adaptador de prueba determinista. No existe topología validada ni archivo .sumocfg.",
      },
    ];
  }, [overview, ml]);

  return (
    <div className="feature-page">
      <header className="page-heading">
        <p className="eyebrow">Arquitectura hexagonal</p>
        <h2>Sistema y arquitectura</h2>
        <p>Estado real de cada pieza del corredor {CORRIDOR_SCOPE}.</p>
      </header>

      {error && <PageError message={error} />}

      <section className="panel">
        <h3>Flujo de una solicitud</h3>
        <ol className="flow-diagram">
          <li><strong>Frontend</strong><span>React</span></li>
          <li><strong>FastAPI</strong><span>controller</span></li>
          <li><strong>Caso de uso</strong><span>aplicación</span></li>
          <li><strong>Adaptadores</strong><span>ML · MQTT · SUMO</span></li>
          <li><strong>Persistencia</strong><span>PostgreSQL/PostGIS</span></li>
        </ol>
        <p className="source-note">
          El dominio no depende de ninguna capa externa. En el frontend,{" "}
          <code>check-architecture.mjs</code> impide que <code>fetch</code> aparezca fuera de{" "}
          <code>infrastructure/</code> y que el dominio importe framework o adaptadores.
        </p>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Estado de cada componente</h3>
            <p className="muted">Verificado contra la API en el momento de la consulta.</p>
          </div>
          <div className="toolbar"><button onClick={refresh}>Actualizar estado</button></div>
        </div>
        {!overview ? <LoadingPanel /> : (
          <div className="component-grid">
            {stages.map((stage) => (
              <article className="panel component-card" key={stage.name} data-status={stage.status}>
                <div className="component-head">
                  <strong>{stage.name}</strong>
                  <span className="status-chip" data-status={stage.status}>{STATUS_LABELS[stage.status]}</span>
                </div>
                <p className="component-role">{stage.role}</p>
                <p className="source-note">{stage.evidence}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <h3>Piezas aún no operativas</h3>
        <ul className="warning-list">
          <li>SUMO / TraCI no está conectado: la simulación usa un adaptador de prueba y no produce métricas físicas.</li>
          <li>La geometría del corredor sigue en estado {overview?.twin.geometry_status ?? "pending_validation"}; el mapa es esquemático.</li>
          <li>No existen datos locales actuales de la Av. Ferrocarril: los aforos disponibles son históricos de 2013.</li>
          <li>El modelo publicado no ha sido validado con datos locales de Huancayo.</li>
        </ul>
      </section>

      <section className="panel">
        <h3>Clasificación de la información</h3>
        <div className="dataset-badges">
          <SourceTag category="local_historical" />
          <SourceTag category="ml_experiment" />
          <SourceTag category="regional_demo" />
          <SourceTag category="simulated" />
        </div>
        <DataProvenanceNotice category="simulated">
          {ML_INFERENCE_CONTRACT.notValidatedNotice}
        </DataProvenanceNotice>
      </section>
    </div>
  );
}