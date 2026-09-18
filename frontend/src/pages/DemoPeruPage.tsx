import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import type { DatasetMetadata, DemoMlResult, DemoState, TrafficLocation, TrafficQueryResult } from "../types/api";
import { useApplication } from "../presentation/ApplicationContext";

const sourceNames: Record<string, string> = {
  mtc_peru_toll_flow: "MTC · Flujo vehicular",
  ositran_peru_road_traffic: "OSITRAN · Tráfico carreteras",
  huancayo_historical_counts_2013: "Huancayo · Aforos históricos 2013",
};

const markerIcon = L.divIcon({ className: "toll-marker", html: "<span></span>", iconSize: [18, 18] });
const formatNumber = new Intl.NumberFormat("es-PE");

function LineChart({ data }: { data: { period: string; vehicle_count: number }[] }) {
  if (!data.length) return <p className="empty">Sin datos para los filtros seleccionados.</p>;
  const values = data.map((item) => item.vehicle_count);
  const max = Math.max(...values, 1);
  const points = values.map((value, index) => `${(index / Math.max(values.length - 1, 1)) * 100},${48 - (value / max) * 42}`).join(" ");
  return <div className="chart-wrap"><svg viewBox="0 0 100 52" role="img" aria-label="Serie temporal de tráfico"><polyline points={points} /></svg><div className="chart-axis"><span>{data[0].period}</span><span>{data.at(-1)?.period}</span></div></div>;
}

function CategoryBars({ values }: { values: Record<string, number> }) {
  const entries = Object.entries(values).filter(([key]) => key !== "total");
  const max = Math.max(...entries.map(([, value]) => value), 1);
  if (!entries.length) return <p className="empty">Sin categorías disponibles.</p>;
  return <div className="bars">{entries.map(([name, value]) => <div key={name}><span>{name}</span><div><i style={{ width: `${(value / max) * 100}%` }} /></div><strong>{formatNumber.format(value)}</strong></div>)}</div>;
}

function PredictionChart({ data }: { data: DemoMlResult["prediction_series"] }) {
  if (!data.length) return <p className="empty">Sin resultados de predicción.</p>;
  const max = Math.max(...data.flatMap((item) => [item.actual, item.predicted]), 1);
  const points = (field: "actual" | "predicted") => data.map((item, index) => `${(index / Math.max(data.length - 1, 1)) * 100},${48 - (item[field] / max) * 42}`).join(" ");
  return <div className="chart-wrap prediction-chart"><svg viewBox="0 0 100 52" role="img" aria-label="Real histórico y predicción"><polyline className="actual" points={points("actual")} /><polyline className="predicted" points={points("predicted")} /></svg><div className="legend"><span>● Real histórico</span><span>● Predicción</span></div></div>;
}

export function DemoPeruPage() {
  const application = useApplication();
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [datasetId, setDatasetId] = useState("mtc_peru_toll_flow");
  const [locations, setLocations] = useState<TrafficLocation[]>([]);
  const [locationId, setLocationId] = useState("");
  const [region, setRegion] = useState("");
  const [startPeriod, setStartPeriod] = useState("");
  const [endPeriod, setEndPeriod] = useState("");
  const [speed, setSpeed] = useState(5);
  const [traffic, setTraffic] = useState<TrafficQueryResult | null>(null);
  const [state, setState] = useState<DemoState | null>(null);
  const [ml, setMl] = useState<DemoMlResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const trafficRequest = useRef(0);
  const selectedDataset = datasets.find((item) => item.dataset_id === datasetId);

  useEffect(() => {
    Promise.all([application.listDatasets(), application.listLocations(), application.getReplayState(), application.getMlExperiment().catch(() => null)])
      .then(([datasetRows, locationRows, demoState, mlResult]) => { setDatasets(datasetRows); setLocations(locationRows); setState(demoState); setMl(mlResult); })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo conectar con el API"));
  }, [application]);

  const loadTraffic = useCallback(() => {
    const requestId = ++trafficRequest.current;
    setError(null);
    application.queryTraffic({
      datasetId,
      locationId: locationId || undefined,
      region: region || undefined,
      startPeriod: startPeriod || undefined,
      endPeriod: endPeriod || undefined,
      limit: 500,
    }).then((result) => {
      if (requestId === trafficRequest.current) {
        setTraffic(result);
        setError(null);
      }
    }).catch((reason: unknown) => {
      if (requestId === trafficRequest.current) setError(reason instanceof Error ? reason.message : "Error al consultar datos");
    });
  }, [application, datasetId, locationId, region, startPeriod, endPeriod]);

  useEffect(() => { loadTraffic(); }, [loadTraffic]);
  useEffect(() => {
    const timer = window.setInterval(() => application.getReplayState().then(setState).catch(() => undefined), 1000);
    return () => window.clearInterval(timer);
  }, [application]);

  useEffect(() => {
    setLocationId(""); setStartPeriod(""); setEndPeriod("");
  }, [datasetId]);

  const visibleLocations = useMemo(() => region ? locations.filter((item) => item.region?.toLocaleUpperCase("es-PE") === region) : locations, [locations, region]);
  const periods = traffic?.series ?? [];
  const predominant = Object.entries(traffic?.category_totals ?? {}).filter(([key]) => key !== "total").sort((a, b) => b[1] - a[1])[0]?.[0] ?? "No disponible";

  const runAction = (name: string, operation: () => Promise<DemoState>) => {
    setBusyAction(name);
    setError(null);
    operation().then(setState).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "No se pudo completar la acción");
    }).finally(() => setBusyAction(null));
  };

  const startReplay = () => runAction("start", () => application.startReplay({
    datasetId,
    startPeriod: startPeriod || undefined,
    endPeriod: endPeriod || undefined,
    locationId: locationId || undefined,
    speedFactor: speed,
    limit: 60,
  }));

  return <div className="demo-page">
    <header className="demo-header"><div><p className="eyebrow">Datos oficiales históricos</p><h2>Modo Demo Perú</h2><p>Recorrido verificable desde el dataset oficial hasta el estado del gemelo digital.</p></div><span className="official-badge">DATOS OFICIALES DEL ESTADO PERUANO</span></header>
    <div className="notice">Demostración con datos históricos oficiales. La reproducción se acelera con fines de demostración y no representa tiempo real.</div>
    {error && <div className="error-box">{error}</div>}
    <section className="control-panel">
      <label>Fuente<select value={datasetId} onChange={(event) => setDatasetId(event.target.value)}>{datasets.filter((item) => sourceNames[item.dataset_id]).map((item) => <option key={item.dataset_id} value={item.dataset_id}>{sourceNames[item.dataset_id]}</option>)}</select></label>
      <label>Región<select value={region} onChange={(event) => setRegion(event.target.value)} disabled={datasetId !== "mtc_peru_toll_flow"}><option value="">Todas</option><option value="JUNIN">Junín</option></select></label>
      <label>Peaje / ubicación<select value={locationId} onChange={(event) => setLocationId(event.target.value)} disabled={datasetId === "ositran_peru_road_traffic"}><option value="">Todas</option>{datasetId === "huancayo_historical_counts_2013" ? ["P03", "P04", "P42"].map((point) => <option key={point} value={point}>{point}</option>) : visibleLocations.map((item) => <option key={item.source_location_id} value={item.source_location_id}>{item.name}</option>)}</select></label>
      <label>Desde<input type="month" value={startPeriod} min={selectedDataset?.period_min ?? undefined} max={selectedDataset?.period_max ?? undefined} onChange={(event) => setStartPeriod(event.target.value)} disabled={datasetId === "huancayo_historical_counts_2013"} /></label>
      <label>Hasta<input type="month" value={endPeriod} min={selectedDataset?.period_min ?? undefined} max={selectedDataset?.period_max ?? undefined} onChange={(event) => setEndPeriod(event.target.value)} disabled={datasetId === "huancayo_historical_counts_2013"} /></label>
      <label>Velocidad<select value={speed} onChange={(event) => setSpeed(Number(event.target.value))}>{[1, 5, 10, 60].map((value) => <option key={value} value={value}>{value}x</option>)}</select><small>Reproducción, no velocidad del tráfico.</small></label>
    </section>
    <div className="demo-actions"><button className="primary" onClick={startReplay} disabled={busyAction !== null}>{busyAction === "start" ? "Iniciando…" : "Iniciar demostración"}</button><button onClick={() => runAction("pause", () => application.pauseReplay())} disabled={busyAction !== null || state?.status !== "running"}>Pausar</button><button onClick={() => runAction("continue", () => application.continueReplay())} disabled={busyAction !== null || state?.status !== "paused"}>Continuar</button><button onClick={() => runAction("stop", () => application.stopReplay())} disabled={busyAction !== null || !["running", "paused"].includes(state?.status ?? "")}>Detener</button><button onClick={() => runAction("reset", () => application.resetReplay())} disabled={busyAction !== null}>Reiniciar</button></div>
    <section className="kpi-grid">
      <article><span>Total de vehículos</span><strong>{traffic ? formatNumber.format(traffic.total_vehicles) : "—"}</strong></article>
      <article><span>Periodo disponible</span><strong>{selectedDataset?.period_min ?? "—"} → {selectedDataset?.period_max ?? "—"}</strong></article>
      <article><span>Ubicación</span><strong>{locationId || "Selección nacional"}</strong></article>
      <article><span>Categoría predominante</span><strong>{predominant}</strong></article>
      <article><span>Fuente</span><strong>{selectedDataset?.provider ?? "—"}</strong></article>
      <article><span>Estado replay</span><strong>{state?.status ?? "idle"}</strong></article>
    </section>
    <div className="source-strip">{traffic?.source_label ?? "Fuente: sin seleccionar"}<span>{traffic?.record_count ?? 0} registros normalizados en la selección</span></div>
    <section className="dashboard-grid">
      <article className="panel wide"><h3>Serie temporal de tráfico</h3><LineChart data={periods} /></article>
      <article className="panel"><h3>Tráfico por categoría</h3><CategoryBars values={traffic?.category_totals ?? {}} /></article>
      <article className="panel map-card"><h3>Mapa de peajes oficiales MTC</h3><MapContainer center={[-9.19, -75.02]} zoom={5} scrollWheelZoom={false}>{<TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />}{visibleLocations.map((item) => <Marker key={item.source_location_id} position={[item.latitude, item.longitude]} icon={markerIcon}><Popup><strong>{item.name}</strong><br />{item.region}{item.status ? <><br />{item.status}</> : null}{item.operator ? <><br />{item.operator}</> : null}</Popup></Marker>)}</MapContainer><p className="source-note">Fuente: MTC · GeoJSON oficial. {region === "JUNIN" && visibleLocations.length === 0 ? "No se identificaron registros de Junín en esta fuente con los campos disponibles." : `${visibleLocations.length} ubicaciones vigentes mostradas.`}</p></article>
    </section>
    <section className="local-reference"><div><p className="eyebrow">Referencia local: Huancayo</p><h3>Aforos municipales históricos</h3><p>P03: 1 779 / 1 744 / 1 888 · P04: 1 593 / 1 501 / 1 730 · P42: 553 / 559 / 545</p></div><strong>Aforos históricos 2013. No representan tráfico actual de 2026.</strong></section>
    <section className="panel ml-panel"><div className="ml-heading"><div><p className="eyebrow">Experimento ML nacional</p><h3>Real histórico vs. predicción</h3></div>{ml && <div className="metric-row"><span>Modelo<strong>{ml.selected_model}</strong></span><span>MAE<strong>{formatNumber.format(Math.round(ml.metrics[ml.selected_model].mae))}</strong></span><span>RMSE<strong>{formatNumber.format(Math.round(ml.metrics[ml.selected_model].rmse))}</strong></span><span>R²<strong>{ml.metrics[ml.selected_model].r2.toFixed(4)}</strong></span><span>Test<strong>{ml.test_period.min} → {ml.test_period.max}</strong></span></div>}</div>{ml ? <PredictionChart data={ml.prediction_series} /> : <p className="empty">El experimento ML no se ha ejecutado o su metadata no está disponible.</p>}<p className="source-note">{ml?.warning ?? "Sin métricas publicadas."}</p></section>
    <section className="technical-grid"><article className="panel"><h3>Flujo del sistema</h3><div className="pipeline">{Object.entries(state?.technical_status ?? {}).map(([stage, status]) => <div key={stage}><span>{stage.replaceAll("_", " ")}</span><strong data-status={status}>{status}</strong></div>)}</div></article><article className="panel"><h3>Log en vivo</h3><div className="live-log">{state?.events.length ? state.events.slice().reverse().map((event, index) => <p key={`${event.timestamp}-${index}`}><time>{new Date(event.timestamp).toLocaleTimeString("es-PE")}</time><span>{event.stage}</span>{event.message}</p>) : <p className="empty">Sin eventos. Inicie una demostración.</p>}</div></article></section>
    <p className="scope-warning">Esta demostración verifica el funcionamiento técnico del software. No constituye una validación del modelo de movilidad de la Av. Ferrocarril.</p>
  </div>;
}
