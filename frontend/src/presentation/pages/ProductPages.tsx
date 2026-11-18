import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
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
  const application = useApplication();
  const navigate = useNavigate();
  const [username, setUsername] = useState("editor");
  const [password, setPassword] = useState("");
  const [active, setActive] = useState(application.hasEditorSession());
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await application.loginEditor(username, password);
      setActive(true);
      setPassword("");
      navigate("/escenarios");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo iniciar sesión.");
    } finally {
      setPending(false);
    }
  };

  return <div className="login">
    <p className="eyebrow">Edición del prototipo</p>
    <h2>Acceso de editor</h2>
    <p>Las consultas son públicas. Para ejecutar SUMO o modificar datos, inicia sesión con la cuenta de editor.</p>
    {active ? <button type="button" onClick={() => { application.logoutEditor(); setActive(false); }}>Cerrar sesión</button> :
      <form onSubmit={(event) => void submit(event)}>
        <label>Usuario<input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
        <label>Contraseña<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        <button type="submit" disabled={pending}>{pending ? "Ingresando…" : "Ingresar"}</button>
      </form>}
    {error && <div className="error-box" role="alert">{error}</div>}
    <Link to="/">Volver al panel</Link>
  </div>;
}
