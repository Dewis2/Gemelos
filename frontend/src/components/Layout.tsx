import { NavLink, Outlet } from "react-router-dom";
import { CORRIDOR_LABEL, CORRIDOR_SCOPE } from "../domain/corridor";

const primaryLinks = [
  ["/", "Dashboard · Av. Ferrocarril"],
  ["/mapa", "Mapa del corredor"],
  ["/historico", "Datos históricos"],
  ["/prediccion", "Predicción IA"],
  ["/escenarios", "Escenarios"],
  ["/fuentes", "Fuentes de datos"],
  ["/sistema", "Sistema"],
] as const;

const secondaryLinks = [["/demo-peru", "Demostración técnica · datos regionales"]] as const;

export function Layout() {
  return (
    <div className="shell">
      <aside>
        <p className="eyebrow">Taller de Proyectos 1 · PMV</p>
        <h1>Gemelo Digital</h1>
        <p className="muted">{CORRIDOR_LABEL}</p>
        <p className="muted scope-line">{CORRIDOR_SCOPE}</p>
        <nav>{primaryLinks.map(([to, label]) => <NavLink key={to} to={to} end={to === "/"}>{label}</NavLink>)}</nav>
        <div className="nav-secondary">
          <p className="eyebrow">Evidencia técnica</p>
          <nav>{secondaryLinks.map(([to, label]) => <NavLink key={to} to={to}>{label}</NavLink>)}</nav>
        </div>
        <div className="architecture-note"><span>Arquitectura</span><strong>Hexagonal</strong><small>Dominio · Aplicación · Adaptadores</small></div>
      </aside>
      <main><Outlet /></main>
    </div>
  );
}
