export function PendingKpi({ label, reason }: { label: string; reason: string }) {
  return (
    <article className="kpi kpi-pending">
      <span>{label}</span>
      <strong>Pendiente (backend)</strong>
      <small>{reason}</small>
    </article>
  );
}
