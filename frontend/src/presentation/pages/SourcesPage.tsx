import { useEffect, useState } from "react";
import type { DatasetMetadata } from "../../domain/models";
import {
  DOCUMENTED_ACADEMIC_DATASET,
  HISTORICAL_SOURCE,
  REGIONAL_DATASET_NOTICE,
  SIMULATION_COMPONENTS,
  classifyDataset,
} from "../../domain/corridor";
import { useApplication } from "../ApplicationContext";
import { DataProvenanceNotice } from "../components/DataProvenanceNotice";
import { SourceTag } from "../components/SourceTag";

const USE_LABELS: Record<string, string> = {
  demo: "Demostración técnica",
  ingestion_validation: "Validación de ingesta",
  dashboard: "Panel de control",
  ml_experiment: "Experimento de ML",
  huancayo_local_validation: "Validación local de Huancayo",
};

const LOCAL_VALIDATION_LABELS: Record<string, string> = {
  true: "Validación local disponible",
  false: "Sin validación local",
};

function DatasetCard({ dataset }: { dataset: DatasetMetadata }) {
  const category = classifyDataset(dataset.dataset_id);
  return (
    <article className="panel" key={dataset.dataset_id}>
      <div className="dataset-title">
        <span>{dataset.provider}</span>
        <small>{dataset.country}</small>
      </div>
      <h3>{dataset.title}</h3>
      <div className="dataset-badges">
        <SourceTag category={category} />
        <span className="source-tag" data-category="neutral">{dataset.source_type}</span>
      </div>
      <dl>
        <div><dt>Identificador</dt><dd><code>{dataset.dataset_id}</code></dd></div>
        <div><dt>Periodo</dt><dd>{dataset.period_min ?? "—"} → {dataset.period_max ?? "—"}</dd></div>
        <div><dt>Granularidad</dt><dd>{dataset.temporal_granularity} · {dataset.spatial_granularity}</dd></div>
        <div><dt>Licencia</dt><dd>{dataset.license || "No especificada"}</dd></div>
        <div><dt>Validación local</dt><dd>{LOCAL_VALIDATION_LABELS[String(dataset.local_validation)] ?? String(dataset.local_validation)}</dd></div>
        <div><dt>Fuente</dt><dd>{dataset.source_page || "No declarada"}</dd></div>
      </dl>
      <h4>Uso dentro del proyecto</h4>
      <ul className="use-list">
        {Object.entries(dataset.allowed_uses).map(([use, allowed]) => (
          <li key={use} data-allowed={allowed}>
            <span>{USE_LABELS[use] ?? use}</span>
            <strong>{allowed ? "Permitido" : "No permitido"}</strong>
          </li>
        ))}
      </ul>
      {dataset.limitations.length > 0 && (
        <>
          <h4>Limitaciones</h4>
          <ul>{dataset.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
        </>
      )}
    </article>
  );
}

export function SourcesPage() {
  const application = useApplication();
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    application.listDatasets().then(setDatasets).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo cargar el catálogo."));
  }, [application]);

  const local = datasets.filter((dataset) => classifyDataset(dataset.dataset_id) === "local_historical");
  const regional = datasets.filter((dataset) => classifyDataset(dataset.dataset_id) === "regional_demo");

  return (
    <div className="feature-page">
      <header className="page-heading">
        <p className="eyebrow">Trazabilidad de datos</p>
        <h2>Fuentes de datos</h2>
        <p>Cada conjunto conserva proveedor, cobertura, granularidad, licencia declarada, uso permitido y advertencias de uso.</p>
      </header>

      {error && <div className="error-box" role="alert">{error}</div>}

      <section className="panel">
        <h3>Clasificación de las fuentes</h3>
        <div className="dataset-badges">
          <SourceTag category="local_historical" />
          <SourceTag category="ml_experiment" />
          <SourceTag category="regional_demo" />
          <SourceTag category="simulated" />
        </div>
        <p className="source-note">
          Las cuatro categorías no son intercambiables: cada indicador del sistema declara a cuál pertenece.
        </p>
      </section>

      <section>
        <h3>Histórico local del corredor</h3>
        <DataProvenanceNotice category="local_historical">{HISTORICAL_SOURCE.label}</DataProvenanceNotice>
      </section>
      <section className="dataset-grid">
        {local.length ? local.map((dataset) => <DatasetCard key={dataset.dataset_id} dataset={dataset} />) : <p className="empty">No hay conjuntos locales registrados.</p>}
      </section>

      <section>
        <h3>Experimental para inteligencia artificial</h3>
        <DataProvenanceNotice category="ml_experiment">{DOCUMENTED_ACADEMIC_DATASET.notice}</DataProvenanceNotice>
        <article className="panel">
          <div className="dataset-title">
            <span>{DOCUMENTED_ACADEMIC_DATASET.name}</span>
            <small>{DOCUMENTED_ACADEMIC_DATASET.geography}</small>
          </div>
          <h3>Dataset académico documentado para la PoC</h3>
          <dl>
            <div><dt>Ámbito geográfico</dt><dd>{DOCUMENTED_ACADEMIC_DATASET.geography}</dd></div>
            <div><dt>Estado</dt><dd>{DOCUMENTED_ACADEMIC_DATASET.status}</dd></div>
            <div><dt>Uso en el proyecto</dt><dd>Experimentación técnica del pipeline de predicción. No representa tráfico de Huancayo.</dd></div>
          </dl>
          <h4>Limitaciones</h4>
          <ul>
            <li>El contexto geográfico es distinto al del corredor Av. Ferrocarril.</li>
            <li>No se ha validado ningún modelo con aforos locales actuales.</li>
            <li>Sus volúmenes no son comparables con los aforos municipales de {HISTORICAL_SOURCE.year}.</li>
          </ul>
        </article>
      </section>

      <section>
        <h3>Regionales y de demostración técnica</h3>
        <DataProvenanceNotice category="regional_demo">{REGIONAL_DATASET_NOTICE}</DataProvenanceNotice>
        <div className="dataset-grid">
          {regional.length ? regional.map((dataset) => <DatasetCard key={dataset.dataset_id} dataset={dataset} />) : <p className="empty">No hay conjuntos regionales registrados.</p>}
        </div>
      </section>
    <section>
        <h3>Simulación y componentes técnicos</h3>
        <DataProvenanceNotice category="simulated">
          Estas piezas producen indicadores técnicos, no observaciones. Ninguna cifra que salga de ellas describe la movilidad del corredor.
        </DataProvenanceNotice>
        <div className="dataset-grid">
          {[SIMULATION_COMPONENTS.fakeSimulator, SIMULATION_COMPONENTS.sumo].map((component) => (
            <article className="panel" key={component.name}>
              <div className="dataset-title">
                <span>{component.name}</span>
                <small>{component.role}</small>
              </div>
              <div className="dataset-badges">
                <SourceTag category="simulated" />
                <span className="source-tag" data-category="neutral">No es una fuente de datos</span>
              </div>
              <p className="muted">{component.notice}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
