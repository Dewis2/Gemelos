import { NavLink, Outlet } from "react-router-dom";

const links = [
  ["/", "Dashboard Huancayo"],
  ["/demo-peru", "Demo Perú"],
  ["/mapa", "Mapa"],
  ["/prediccion", "Predicción"],
  ["/escenarios", "Escenarios"],
  ["/fuentes", "Fuentes de datos"],
  ["/estado", "Sistema"],
];

export function Layout() {
  return (
    <div className="shell">
      <aside>
        <p className="eyebrow">Taller de Proyectos 1 · PMV</p>
        <h1>Gemelo Digital</h1>
        <p className="muted">Av. Ferrocarril · Huancayo</p>
        <nav>{links.map(([to, label]) => <NavLink key={to} to={to}>{label}</NavLink>)}</nav>
        <div className="architecture-note"><span>Arquitectura</span><strong>Hexagonal</strong><small>Dominio · Aplicación · Adaptadores</small></div>
      </aside>
      <main><Outlet /></main>
    </div>
  );
}
