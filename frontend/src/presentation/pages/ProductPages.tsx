import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { DashboardOverview } from "../../domain/models";
import { useApplication } from "../ApplicationContext";

function PageError({ message }: { message: string }) {
  return <div className="error-box" role="alert">{message}</div>;
}

function LoadingPanel({ label = "Consultando el sistema…" }: { label?: string }) {
  return <section className="panel loading-panel"><span className="spinner" />{label}</section>;
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
