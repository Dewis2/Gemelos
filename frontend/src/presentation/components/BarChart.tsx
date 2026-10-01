const formatNumber = new Intl.NumberFormat("es-PE");

export interface GroupedBarGroup {
  label: string;
  values: { name: string; value: number }[];
}

export function GroupedBarChart({ data, unit }: { data: GroupedBarGroup[]; unit: string }) {
  if (!data.length) return <p className="empty">Sin datos para los filtros seleccionados.</p>;
  const max = Math.max(...data.flatMap((group) => group.values.map((item) => item.value)), 1);
  const seriesCount = Math.max(...data.map((group) => group.values.length), 1);
  const base = 46;
  const plotHeight = 38;
  const groupWidth = 100 / data.length;
  const barWidth = (groupWidth * 0.7) / seriesCount;

  return (
    <div className="grouped-chart">
      <svg viewBox="0 0 100 52" role="img" aria-label={`Comparación por punto y franja horaria, en ${unit}`}>
        <line x1="0" y1={base} x2="100" y2={base} className="chart-baseline" />
        {data.map((group, groupIndex) => {
          const groupStart = groupIndex * groupWidth + (groupWidth - barWidth * seriesCount) / 2;
          return (
            <g key={group.label}>
              {group.values.map((item, seriesIndex) => {
                const height = Math.max((item.value / max) * plotHeight, 0.4);
                return (
                  <rect
                    key={item.name}
                    x={groupStart + seriesIndex * barWidth}
                    y={base - height}
                    width={barWidth * 0.82}
                    height={height}
                    className="column"
                    data-series={seriesIndex}
                  >
                    <title>{`${group.label} · ${item.name}: ${formatNumber.format(item.value)} ${unit}`}</title>
                  </rect>
                );
              })}
            </g>
          );
        })}
      </svg>
      <div className="chart-axis">
        {data.map((group) => <span key={group.label}>{group.label}</span>)}
      </div>
      <div className="legend legend-series">
        {(data[0].values).map((item, index) => (
          <span key={item.name} data-series={index}>{item.name}</span>
        ))}
      </div>
    </div>
  );
}
