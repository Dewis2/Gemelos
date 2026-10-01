import { useEffect, useMemo, useState } from "react";
import type { TrafficQueryResult } from "../../domain/models";
import {
  COUNT_POINTS,
  DAY_PERIODS,
  HISTORICAL_SOURCE,
  HISTORICAL_YEAR,
} from "../../domain/corridor";
import { useApplication } from "../ApplicationContext";
import { GroupedBarChart, type GroupedBarGroup } from "../components/BarChart";
import { DataProvenanceNotice } from "../components/DataProvenanceNotice";

const formatNumber = new Intl.NumberFormat("es-PE");

function buildValuesByPoint(result: TrafficQueryResult | null) {
  const byPoint = new Map<string, Map<string, number>>();
  for (const record of result?.records ?? []) {
    const period = String(record.metadata?.day_period ?? "");
    if (!period) continue;
    const periods = byPoint.get(record.source_location_id) ?? new Map<string, number>();
    periods.set(period, record.vehicle_count);
    byPoint.set(record.source_location_id, periods);
  }
  return byPoint;
}

export function HistoricalPage() {
  const application = useApplication();
  const [result, setResult] = useState<TrafficQueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    application
      .queryTraffic({ datasetId: HISTORICAL_SOURCE.datasetId, limit: 500 })
      .then(setResult)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "No se pudieron cargar los aforos históricos."));
  }, [application]);

  const byPoint = useMemo(() => buildValuesByPoint(result), [result]);

  const groups: GroupedBarGroup[] = COUNT_POINTS.map((point) => ({
    label: point.id,
    values: DAY_PERIODS.map((period) => ({
      name: period.label,
      value: byPoint.get(point.id)?.get(period.id) ?? 0,
    })),
  }));

  const discrepancies = COUNT_POINTS.flatMap((point) =>
    DAY_PERIODS.flatMap((period) => {
      const apiValue = byPoint.get(point.id)?.get(period.id);
      if (apiValue === undefined) return [`${point.id} · ${period.label}: el backend no devolvió el registro.`];
      if (apiValue !== point.values[period.id]) {
        return [`${point.id} · ${period.label}: API ${apiValue} frente a la referencia documentada ${point.values[period.id]}.`];
      }
      return [];
    }),
  );

  return (
    <div className="feature-page">
      <header className="page-heading">
        <p className="eyebrow">Referencia local</p>
        <h2>Datos históricos</h2>
        <p>
          Aforos vehiculares del corredor {HISTORICAL_SOURCE.year} en los puntos P03, P04 y P42, por franja horaria.
        </p>
      </header>

      {error && <div className="error-box" role="alert">{error}</div>}

      <DataProvenanceNotice category="local_historical">{HISTORICAL_SOURCE.label}</DataProvenanceNotice>

      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Comparación por punto y franja horaria</h3>
            <p className="muted">Valores obtenidos de la API a través del adaptador del conjunto de datos local.</p>
          </div>
          <div className="metric-row">
            <span>Fuente<strong>{result?.dataset.provider ?? HISTORICAL_SOURCE.provider}</strong></span>
            <span>Periodo<strong>{result?.dataset.period_min ?? HISTORICAL_SOURCE.period} → {result?.dataset.period_max ?? HISTORICAL_SOURCE.period}</strong></span>
            <span>Registros<strong>{result ? formatNumber.format(result.record_count) : "—"}</strong></span>
          </div>
        </div>
        <GroupedBarChart data={groups} unit="veh" />
        <p className="source-note">{result?.warning ?? "Aforos históricos municipales."}</p>
      </section>

      <section className="panel">
        <h3>Detalle por punto</h3>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Punto</th>
                <th>Ubicación descrita</th>
                {DAY_PERIODS.map((period) => <th key={period.id}>{period.label}</th>)}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {COUNT_POINTS.map((point) => {
                const values = DAY_PERIODS.map((period) => byPoint.get(point.id)?.get(period.id) ?? 0);
                const total = values.reduce((accumulator, value) => accumulator + value, 0);
                return (
                  <tr key={point.id}>
                    <td><strong>{point.id}</strong></td>
                    <td>{point.description}</td>
                    {values.map((value, index) => <td key={DAY_PERIODS[index].id}>{formatNumber.format(value)}</td>)}
                    <td>{formatNumber.format(total)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="source-note">
          Unidad: vehículos aforados por franja horaria. {HISTORICAL_SOURCE.provider} — {HISTORICAL_SOURCE.title} ({HISTORICAL_YEAR}).
        </p>
      </section>

      <section className="panel">
        <h3>Trazabilidad de la lectura</h3>
        {discrepancies.length ? (
          <ul className="warning-list">
            {discrepancies.map((item) => <li key={item}>{item}</li>)}
          </ul>
        ) : (
          <p className="empty">Los {COUNT_POINTS.length * DAY_PERIODS.length} registros devueltos por la API coinciden con la referencia documentada del proyecto.</p>
        )}
        <p className="source-note">
          Conjunto de datos: <code>{result?.dataset.dataset_id ?? HISTORICAL_SOURCE.datasetId}</code> · {result?.source_label ?? ""}
        </p>
      </section>
    </div>
  );
}
