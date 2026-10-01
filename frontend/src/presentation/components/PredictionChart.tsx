import type { DemoMlResult } from "../../domain/models";

const formatPeriod = (value: string): string => {
  const date = new Date(value.length === 7 ? `${value}-01T00:00:00` : value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString("es-PE", { month: "short", year: "numeric" });
};

export function PredictionChart({ data }: { data: DemoMlResult["prediction_series"] }) {
  if (!data.length) return <p className="empty">Sin resultados de predicción.</p>;
  const max = Math.max(...data.flatMap((item) => [item.actual, item.predicted]), 1);
  const points = (key: "actual" | "predicted") =>
    data.map((item, index) => `${(index / Math.max(data.length - 1, 1)) * 100},${48 - (item[key] / max) * 42}`).join(" ");

  return (
    <div className="chart-wrap prediction-chart">
      <svg viewBox="0 0 100 52" role="img" aria-label="Valor observado y valor predicho">
        <polyline className="actual" points={points("actual")} />
        <polyline className="predicted" points={points("predicted")} />
      </svg>
      <div className="chart-axis">
        <span>{formatPeriod(data[0].period)}</span>
        <span>{formatPeriod(data.at(-1)?.period ?? "")}</span>
      </div>
      <div className="legend"><span>● Real histórico</span><span>● Predicción</span></div>
    </div>
  );
}
