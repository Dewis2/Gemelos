import { NavLink, Outlet } from "react-router-dom";

const links = [
  ["/", "Dashboard"],
  ["/mapa", "Mapa"],
  ["/prediccion", "Predicción"],
  ["/escenarios", "Escenarios"],
  ["/comparacion", "Comparación"],
  ["/fuentes", "Fuentes de datos"],
  ["/estado", "Estado"],
];

export function Layout() {
  return (
    <div className="shell">
      <aside>
        <p className="eyebrow">UNCP · PoC</p>
        <h1>Gemelo Digital</h1>
        <p className="muted">Av. Ferrocarril · Huancayo</p>
        <nav>{links.map(([to, label]) => <NavLink key={to} to={to}>{label}</NavLink>)}</nav>
      </aside>
      <main><Outlet /></main>
    </div>
  );
}

