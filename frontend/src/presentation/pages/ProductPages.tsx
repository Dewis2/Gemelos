import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type {
  DashboardOverview,
  DatasetMetadata,
  DemoMlResult,
  RoadSegment,
  ScenarioExecution,
  TrafficPrediction,
} from "../../domain/models";
import { CorridorMap } from "../../maps/CorridorMap";
import { useApplication } from "../ApplicationContext";

const formatNumber = new Intl.NumberFormat("es-PE", { maximumFractionDigits: 2 });

function PageError({ message }: { message: string }) {
  return <div className="error-box" role="alert">{message}</div>;
}

function LoadingPanel({ label = "Consultando el sistema…" }: { label?: string }) {
  return <section className="panel loading-panel"><span className="spinner" />{label}</section>;
}

export function Dashboard() {
  const application = useApplication();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    application.loadDashboard().then(setOverview).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "No se pudo cargar el panel.");
    });
  }, [application]);

  return <>
    <header className="page-heading"><p className="eyebrow">PMV integrado</p><h2>Centro de control del gemelo digital</h2><p>Un punto de entrada para consultar evidencia, reproducir históricos y verificar el estado técnico del prototipo.</p></header>
    {error && <PageError message={error} />}
    {!overview ? <LoadingPanel /> : <>
      <div className="cards dashboard-cards">
        <article><span>API</span><strong className="status-ok">{overview.health.status.toUpperCase()}</strong><small>{overview.health.stage}</small></article>
        <article><span>Estado del gemelo</span><strong>{overview.twin.status}</strong><small>{overview.twin.geometry_status}</small></article>
        <article><span>Fuentes catalogadas</span><strong>{overview.datasets.length}</strong><small>Con procedencia y limitaciones</small></article>
        <article><span>Replay</span><strong>{overview.replay.status}</strong><small>{overview.replay.replay_position} / {overview.replay.replay_total} eventos</small></article>
      </div>
      <section className="journey-grid" aria-label="Historias de usuario implementadas">
        <Link to="/demo-peru"><span>HU-01</span><strong>Consultar y filtrar tráfico</strong><small>MTC, OSITRAN y referencia histórica local</small></Link>
        <Link to="/demo-peru"><span>HU-02</span><strong>Reproducir datos históricos</strong><small>Inicio, pausa, continuación, detención y reinicio</small></Link>
        <Link to="/prediccion"><span>HU-03</span><strong>Revisar predicción</strong><small>Métricas del experimento y solicitud por tramo</small></Link>
        <Link to="/escenarios"><span>HU-04</span><strong>Evaluar un escenario</strong><small>Creación y ejecución mediante la API</small></Link>
      </section>
      <CorridorMap />
    </>}
  </>;
}

export function MapPage() {
  return <><header className="page-heading"><p className="eyebrow">Representación espacial</p><h2>Mapa del corredor</h2><p>La geometría local se publicará únicamente cuando exista una fuente geoespacial validada.</p></header><CorridorMap /></>;
}

function MlChart({ data }: { data: DemoMlResult["prediction_series"] }) {
  const max = Math.max(...data.flatMap((item) => [item.actual, item.predicted]), 1);
  const points = (key: "actual" | "predicted") => data.map((item, index) => `${(index / Math.max(data.length - 1, 1)) * 100},${48 - (item[key] / max) * 42}`).join(" ");
  return <div className="chart-wrap prediction-chart"><svg viewBox="0 0 100 52" role="img" aria-label="Valores reales y predicción"><polyline className="actual" points={points("actual")} /><polyline className="predicted" points={points("predicted")} /></svg><div className="legend"><span>● Real histórico</span><span>● Predicción</span></div></div>;
}

export function PredictionPage() {
  const application = useApplication();
  const [segments, setSegments] = useState<RoadSegment[]>([]);
  const [ml, setMl] = useState<DemoMlResult | null>(null);
  const [segmentId, setSegmentId] = useState("");
  const [targetTimestamp, setTargetTimestamp] = useState("");
  const [volume, setVolume] = useState("1000");
  const [speed, setSpeed] = useState("30");
  const [prediction, setPrediction] = useState<TrafficPrediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Promise.all([application.listRoadSegments(), application.getMlExperiment().catch(() => null)])
      .then(([rows, experiment]) => { setSegments(rows); setSegmentId(rows[0]?.id ?? ""); setMl(experiment); })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo preparar la predicción."));
  }, [application]);

  const submit = (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError(null); setPrediction(null);
    application.predictTraffic({ roadSegmentId: segmentId, targetTimestamp, features: { traffic_volume: Number(volume), average_speed: Number(speed) } })
      .then(setPrediction)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo generar la predicción."))
      .finally(() => setBusy(false));
  };

  const selectedMetrics = ml ? ml.metrics[ml.selected_model] : null;
  return <div className="feature-page"><header className="page-heading"><p className="eyebrow">HU-03 · Analítica predictiva</p><h2>Predicción de flujo vehicular</h2><p>Separa la evidencia nacional ya entrenada de una inferencia local, que solo se habilita cuando existen tramos y modelo desplegado.</p></header>
    {error && <PageError message={error} />}
    {ml && selectedMetrics ? <section className="panel"><div className="section-heading"><div><h3>Experimento nacional validado temporalmente</h3><p className="muted">Test {ml.test_period.min} → {ml.test_period.max}</p></div><div className="metric-row"><span>Modelo<strong>{ml.selected_model}</strong></span><span>MAE<strong>{formatNumber.format(selectedMetrics.mae)}</strong></span><span>RMSE<strong>{formatNumber.format(selectedMetrics.rmse)}</strong></span><span>R²<strong>{selectedMetrics.r2.toFixed(4)}</strong></span></div></div><MlChart data={ml.prediction_series} /><p className="source-note">{ml.warning}</p></section> : <section className="panel"><h3>Experimento nacional no disponible</h3><p className="empty">Ejecute el entrenamiento o configure la ruta de metadata para publicar sus métricas en esta vista.</p></section>}
    <section className="panel form-panel"><div><h3>Solicitar inferencia local</h3><p className="muted">El backend responderá 503 mientras el modelo local no esté desplegado; el frontend conserva esa limitación de forma explícita.</p></div><form onSubmit={submit}><label>Tramo<select value={segmentId} onChange={(event) => setSegmentId(event.target.value)} disabled={!segments.length}><option value="">{segments.length ? "Seleccione" : "Sin tramos registrados"}</option>{segments.map((segment) => <option key={segment.id} value={segment.id}>{segment.name}</option>)}</select></label><label>Fecha objetivo<input type="datetime-local" value={targetTimestamp} onChange={(event) => setTargetTimestamp(event.target.value)} /></label><label>Volumen observado<input type="number" min="0" value={volume} onChange={(event) => setVolume(event.target.value)} /></label><label>Velocidad media km/h<input type="number" min="0" value={speed} onChange={(event) => setSpeed(event.target.value)} /></label><button className="primary" disabled={busy || !segments.length}>{busy ? "Calculando…" : "Generar predicción"}</button></form></section>
    {prediction && <section className="result-banner"><span>Volumen estimado</span><strong>{formatNumber.format(prediction.predicted_volume)}</strong><small>Modelo {prediction.model_version} · objetivo {new Date(prediction.target_timestamp).toLocaleString("es-PE")}</small></section>}
  </div>;
}

export function ScenariosPage() {
  const application = useApplication();
  const [name, setName] = useState("Hora punta con demanda elevada");
  const [description, setDescription] = useState("Evaluación exploratoria para el corredor priorizado.");
  const [demand, setDemand] = useState("1.15");
  const [signalOffset, setSignalOffset] = useState("0");
  const [incident, setIncident] = useState(false);
  const [execution, setExecution] = useState<ScenarioExecution | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError(null); setExecution(null);
    application.createAndRunScenario({ name, description, configuration: { demand_multiplier: Number(demand), signal_offset_seconds: Number(signalOffset), incident } })
      .then(setExecution)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo ejecutar el escenario."))
      .finally(() => setBusy(false));
  };

  return <div className="feature-page"><header className="page-heading"><p className="eyebrow">HU-04 · Simulación</p><h2>Escenarios what-if</h2><p>La vista registra la configuración en el backend y solicita su ejecución mediante el puerto REST.</p></header>{error && <PageError message={error} />}
    <section className="panel form-panel"><div><h3>Nuevo escenario</h3><p className="muted">Los parámetros quedan trazables como configuración; no se presentan como resultados observados.</p></div><form onSubmit={submit}><label>Nombre<input value={name} onChange={(event) => setName(event.target.value)} /></label><label>Descripción<input value={description} onChange={(event) => setDescription(event.target.value)} /></label><label>Multiplicador de demanda<input type="number" min="0.1" step="0.05" value={demand} onChange={(event) => setDemand(event.target.value)} /></label><label>Offset semafórico s<input type="number" step="1" value={signalOffset} onChange={(event) => setSignalOffset(event.target.value)} /></label><label className="check-field"><input type="checkbox" checked={incident} onChange={(event) => setIncident(event.target.checked)} />Incluir incidente</label><button className="primary" disabled={busy}>{busy ? "Ejecutando…" : "Crear y ejecutar"}</button></form></section>
    {execution && <section className="panel"><h3>{execution.scenario.name}</h3><p className="muted">ID {execution.scenario.id}</p>{execution.results.length ? <div className="table-scroll"><table><thead><tr><th>Tramo</th><th>Tiempo</th><th>Velocidad</th><th>Demora</th><th>Cola</th></tr></thead><tbody>{execution.results.map((result) => <tr key={result.id}><td>{result.road_segment_id}</td><td>{formatNumber.format(result.travel_time)} s</td><td>{formatNumber.format(result.average_speed)} km/h</td><td>{formatNumber.format(result.delay)} s</td><td>{formatNumber.format(result.queue_length)}</td></tr>)}</tbody></table></div> : <p className="empty">El escenario se creó correctamente, pero la red todavía no contiene tramos para producir resultados de simulación.</p>}</section>}
  </div>;
}

export function SourcesPage() {
  const application = useApplication();
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { application.listDatasets().then(setDatasets).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo cargar el catálogo.")); }, [application]);
  return <div className="feature-page"><header className="page-heading"><p className="eyebrow">Trazabilidad de datos</p><h2>Fuentes y limitaciones</h2><p>Cada conjunto conserva proveedor, cobertura, granularidad, licencia declarada y advertencias de uso.</p></header>{error && <PageError message={error} />}{!datasets.length && !error ? <LoadingPanel /> : <section className="dataset-grid">{datasets.map((dataset) => <article className="panel" key={dataset.dataset_id}><div className="dataset-title"><span>{dataset.provider}</span><small>{dataset.country}</small></div><h3>{dataset.title}</h3><dl><div><dt>Periodo</dt><dd>{dataset.period_min ?? "—"} → {dataset.period_max ?? "—"}</dd></div><div><dt>Granularidad</dt><dd>{dataset.temporal_granularity} · {dataset.spatial_granularity}</dd></div><div><dt>Licencia</dt><dd>{dataset.license || "No especificada"}</dd></div></dl>{dataset.limitations.length > 0 && <ul>{dataset.limitations.map((item) => <li key={item}>{item}</li>)}</ul>}</article>)}</section>}</div>;
}

export function StatusPage() {
  const application = useApplication();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const refresh = useCallback(() => { setError(null); application.loadDashboard().then(setOverview).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo verificar el sistema.")); }, [application]);
  useEffect(refresh, [refresh]);
  const services = useMemo(() => overview ? [{ name: "API REST", value: overview.health.status }, { name: "Gemelo digital", value: overview.twin.status }, { name: "Geometría", value: overview.twin.geometry_status }, ...Object.entries(overview.replay.technical_status).map(([name, value]) => ({ name: name.replaceAll("_", " "), value }))] : [], [overview]);
  return <div className="feature-page"><header className="page-heading"><p className="eyebrow">Observabilidad</p><h2>Estado del sistema</h2><p>Supervisión del API, estado digital y etapas del flujo de demostración.</p></header>{error && <PageError message={error} />}<div className="toolbar"><button onClick={refresh}>Actualizar estado</button></div>{!overview ? <LoadingPanel /> : <section className="status-grid">{services.map((service) => <article className="panel" key={service.name}><span>{service.name}</span><strong data-status={service.value}>{service.value}</strong></article>)}</section>}</div>;
}

export function LoginPage() {
  return <div className="login"><p className="eyebrow">Alcance del PMV</p><h2>Acceso no implementado</h2><p>La autenticación no forma parte de las historias priorizadas. No existen usuarios ni credenciales reales.</p><Link to="/">Volver al panel</Link></div>;
}
