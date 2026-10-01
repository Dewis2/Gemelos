import { type FormEvent, useEffect, useMemo, useState } from "react";
import type { DemoMlResult, RoadSegment, TrafficPrediction } from "../../domain/models";
import {
  COUNT_POINTS,
  DAY_PERIODS,
  HISTORICAL_SOURCE,
  ML_INFERENCE_CONTRACT,
  MODEL_FEATURES,
  SEGMENTATION_NOTICE,
  WEEKDAY_NAMES,
  buildModelFeatures,
  type ModelFeatureValues,
} from "../../domain/corridor";
import { useApplication } from "../ApplicationContext";
import { DataProvenanceNotice } from "../components/DataProvenanceNotice";
import { PredictionChart } from "../components/PredictionChart";
import { SourceTag } from "../components/SourceTag";

const formatNumber = new Intl.NumberFormat("es-PE", { maximumFractionDigits: 2 });

const MONTH_NAMES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre",
] as const;

const FEATURE_LABELS: Record<keyof ModelFeatureValues, string> = {
  day_of_week: "Día de semana",
  hour: "Hora del día",
  is_weekend: "Fin de semana",
  month: "Mes",
};

const FEATURE_SUFFIX: Record<keyof ModelFeatureValues, string> = {
  day_of_week: "(lunes = 0 … domingo = 6)",
  hour: "(0–23)",
  is_weekend: "(1 = sábado o domingo)",
  month: "(1–12)",
};

const FEATURE_RENDER: Record<keyof ModelFeatureValues, (value: number) => string> = {
  day_of_week: (value) => `${value} · ${WEEKDAY_NAMES[value] ?? "—"}`,
  hour: (value) => `${String(value).padStart(2, "0")}:00`,
  is_weekend: (value) => (value === 1 ? "1 · sábado o domingo" : "0 · día laborable"),
  month: (value) => `${value} · ${MONTH_NAMES[value - 1] ?? "—"}`,
};

function todayIso(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

export function PredictionPage() {
  const application = useApplication();
  const [segments, setSegments] = useState<RoadSegment[]>([]);
  const [ml, setMl] = useState<DemoMlResult | null>(null);
  const [modelNotPublished, setModelNotPublished] = useState(false);
  const [pointId, setPointId] = useState<string>(COUNT_POINTS[1]?.id ?? "P04");
  const [date, setDate] = useState<string>(todayIso());
  const [time, setTime] = useState<string>("08:00");
  const [segmentId, setSegmentId] = useState<string>("");
  const [prediction, setPrediction] = useState<TrafficPrediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    application
      .listRoadSegments()
      .then((rows) => {
        setSegments(rows);
        setSegmentId(rows[0]?.id ?? "");
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudieron consultar los tramos."));

    application
      .getMlExperiment()
      .then(setMl)
      .catch(() => setModelNotPublished(true));
  }, [application]);

  const targetTimestamp = `${date}T${time}`;
  const features = useMemo<ModelFeatureValues | null>(() => {
    try {
      return buildModelFeatures(targetTimestamp);
    } catch {
      return null;
    }
  }, [targetTimestamp]);

  const referencePoint = COUNT_POINTS.find((point) => point.id === pointId);
  const selectedSegment = segments.find((segment) => segment.id === segmentId);
  const selectedMetrics = ml ? ml.metrics[ml.selected_model] : null;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!features) {
      setError("Seleccione una fecha y hora válidas.");
      return;
    }
    setBusy(true);
    setError(null);
    setPrediction(null);
    application
      .predictTraffic({ roadSegmentId: segmentId, targetTimestamp, features })
      .then(setPrediction)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudo generar la predicción."))
      .finally(() => setBusy(false));
  };

  return (
    <div className="feature-page">
      <header className="page-heading">
        <p className="eyebrow">Analítica predictiva</p>
        <h2>Predicción de flujo vehicular</h2>
        <p>
          Predicción experimental del volumen vehicular a corto plazo en veh/h, asociada al contexto seleccionado,
          para apoyar la actualización del gemelo digital y la generación de escenarios de movilidad.
        </p>
      </header>

      <DataProvenanceNotice category="ml_experiment">
        {ML_INFERENCE_CONTRACT.notValidatedNotice} {ML_INFERENCE_CONTRACT.datasetUnresolvedNotice}
      </DataProvenanceNotice>

      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Experimento publicado por el backend</h3>
            <p className="muted">
              {ml
                ? `Conjunto ${ml.training_dataset}${ml.provider ? ` · ${ml.provider}` : ""}${ml.target ? ` · objetivo ${ml.target}` : ""}${ml.features?.length ? ` · ${ml.features.length} variables` : ""}`
                : "El backend todavía no tiene un experimento publicado."}
            </p>
          </div>
          <div className="dataset-badges">
            <SourceTag category="ml_experiment" />
            <span className="source-tag" data-category="neutral">Validación local: no realizada</span>
          </div>
        </div>

        {ml && selectedMetrics ? (
          <>
            <div className="metric-row">
              <span>Modelo<strong>{ml.selected_model}</strong></span>
              <span>MAE<strong>{formatNumber.format(selectedMetrics.mae)}</strong></span>
              <span>RMSE<strong>{formatNumber.format(selectedMetrics.rmse)}</strong></span>
              <span>R²<strong>{selectedMetrics.r2.toFixed(4)}</strong></span>
              <span>Entrenamiento<strong>{ml.training_period.min} → {ml.training_period.max}</strong></span>
              <span>Prueba<strong>{ml.test_period.min} → {ml.test_period.max}</strong></span>
              {ml.train_rows !== undefined && <span>Filas train<strong>{formatNumber.format(ml.train_rows)}</strong></span>}
              {ml.test_rows !== undefined && <span>Filas test<strong>{formatNumber.format(ml.test_rows)}</strong></span>}
            </div>
            <PredictionChart data={ml.prediction_series} />
            <p className="source-note">{ml.warning}</p>
            <p className="source-note">
              El experimento publicado y el modelo de inferencia de este formulario son artefactos distintos:
              este panel describe <code>metadata.json</code>, mientras que el formulario usa el modelo cargado desde{" "}
              <code>{ML_INFERENCE_CONTRACT.endpoint}</code>.
            </p>
          </>
        ) : (
          <p className="empty">
            {modelNotPublished
              ? "El backend responde 404: no hay experimento publicado en la ruta de metadata."
              : "Cargando el experimento…"}
          </p>
        )}
      </section>

      {error && <div className="error-box" role="alert">{error}</div>}

      <section className="panel form-panel">
        <div>
          <h3>Solicitar predicción</h3>
          <p className="muted">
            Las cuatro variables de entrada se derivan automáticamente de la fecha y la hora objetivo, con la misma convención de día de semana que usa el entrenamiento.
          </p>
        </div>
        <form onSubmit={submit}>
          <label>
            Punto de referencia
            <select value={pointId} onChange={(event) => setPointId(event.target.value)}>
              {COUNT_POINTS.map((point) => <option key={point.id} value={point.id}>{point.id}</option>)}
            </select>
            <small>Contexto del corredor. No es una variable de entrada del modelo.</small>
          </label>
          <label>
            Fecha
            <input type="date" value={date} onChange={(event) => setDate(event.target.value)} required />
          </label>
          <label>
            Hora
            <input type="time" value={time} onChange={(event) => setTime(event.target.value)} required />
          </label>
          <label>
            Segmento del corredor
            <select value={segmentId} onChange={(event) => setSegmentId(event.target.value)} disabled={!segments.length}>
              <option value="">{segments.length ? "Seleccione" : "Sin tramos registrados"}</option>
              {segments.map((segment) => <option key={segment.id} value={segment.id}>{segment.name}</option>)}
            </select>
            <small>Identificador que exige el endpoint de predicción.</small>
          </label>

          {selectedSegment && (
            <div className="feature-preview">
              <h4>Tramo seleccionado</h4>
              <dl>
                <div><dt>Nombre</dt><dd>{selectedSegment.name}</dd></div>
                <div><dt>Geometría</dt><dd>{selectedSegment.geometry ?? "no verificada"}</dd></div>
              </dl>
              <p className="source-note">{SEGMENTATION_NOTICE}</p>
              <p className="source-note">
                El carril y la velocidad de referencia del modelo de dominio son valores de relleno exigidos por su contrato, no atributos levantados en campo; por eso no se muestran.
              </p>
            </div>
          )}

          <div className="feature-preview">
            <h4>Variables de entrada derivadas</h4>
            <dl>
              {MODEL_FEATURES.map((feature) => (
                <div key={feature}>
                  <dt>{FEATURE_LABELS[feature]} {FEATURE_SUFFIX[feature]}</dt>
                  <dd>{features ? FEATURE_RENDER[feature](features[feature]) : "—"}</dd>
                </div>
              ))}
            </dl>
          </div>

          <button className="primary" disabled={busy || !segments.length || !features}>
            {busy ? "Calculando…" : "Ejecutar predicción"}
          </button>
        </form>
      </section>

      {!segments.length && (
        <p className="scope-warning">
          El backend todavía no expone tramos del corredor, por lo que el endpoint de predicción no puede invocarse. Esta dependencia se resuelve al registrar la red del corredor; no afecta al contrato de las variables de entrada.
        </p>
      )}

      {referencePoint && (
        <section className="panel">
          <div className="section-heading">
            <div>
              <h3>Contexto: {referencePoint.id}</h3>
              <p className="muted">{referencePoint.description}</p>
            </div>
            <div className="dataset-badges"><SourceTag category="local_historical" /></div>
          </div>
          <div className="metric-row">
            {DAY_PERIODS.map((period) => (
              <span key={period.id}>{period.label}<strong>{formatNumber.format(referencePoint.values[period.id])} veh</strong></span>
            ))}
          </div>
          <p className="source-note">
            Aforos históricos de referencia de {HISTORICAL_SOURCE.year}. Se muestran como contexto del corredor y no intervienen en el cálculo de la predicción.
          </p>
        </section>
      )}

      {prediction && (
        <section className="result-banner">
          <span>Volumen vehicular estimado</span>
          <strong>{formatNumber.format(prediction.predicted_volume)} veh/h</strong>
          <small>
            Modelo {prediction.model_version} · contexto {selectedSegment?.name ?? "sin segmento"} ·{" "}
            objetivo {new Date(prediction.target_timestamp).toLocaleString("es-PE")} · experimental, sin validación local
          </small>
        </section>
      )}

      {prediction && (
        <p className="scope-warning">
          El modelo utiliza únicamente variables temporales y{" "}
          <strong>no diferencia los segmentos del corredor</strong>: el segmento se envía porque el endpoint lo exige, pero no
          forma parte de las variables de entrada. El resultado es por eso idéntico para cualquier tramo y describe la demanda
          esperada en el contexto del dataset de entrenamiento, no una medición ni una predicción específica de la Av. Ferrocarril.
        </p>
      )}

      {features && (
        <section className="panel">
          <h3>Solicitud enviada a POST /api/v1/predictions/traffic-flow</h3>
          <pre className="payload">{JSON.stringify({
            ...(segmentId ? { road_segment_id: segmentId } : {}),
            target_timestamp: targetTimestamp,
            features,
          }, null, 2)}</pre>
          <p className="source-note">
            Contrato exacto esperado por el adaptador de inferencia: las cuatro variables se nombran con las claves que usa el entrenamiento, y el punto de referencia P03/P04/P42 no forma parte del vector.
          </p>
          {!segmentId && (
            <p className="source-note">
              <code>road_segment_id</code> se omite porque todavía no hay un tramo seleccionado; el endpoint exige ese identificador.
            </p>
          )}
        </section>
      )}
    </div>
  );
}
