import { lazy, Suspense } from "react";
import { DataProvenanceNotice } from "../components/DataProvenanceNotice";

const ExploratorySumoPanel = lazy(() =>
  import("../components/ExploratorySumoPanel").then((module) => ({ default: module.ExploratorySumoPanel })),
);

export function ScenariosPage() {
  return (
    <div className="feature-page">
      <header className="page-heading">
        <p className="eyebrow">Simulación</p>
        <h2>Escenarios what-if</h2>
        <p>Ejecuta en el backend tres niveles de demanda sintética sobre la red exploratoria de OpenStreetMap.</p>
      </header>
      <DataProvenanceNotice category="simulated">
        Estos viajes no proceden de aforos. La geometría es colaborativa y el modelo no está calibrado para el tráfico real de la Av. Ferrocarril.
      </DataProvenanceNotice>
      <Suspense fallback={<section className="panel">Cargando simulación exploratoria…</section>}>
        <ExploratorySumoPanel />
      </Suspense>
      <section className="panel">
        <h3>Alcance de los resultados</h3>
        <p>Las métricas son promedios de viajes completos de toda la red OSM utilizada. No se atribuyen a los tres tramos de referencia del corredor. Incidentes y cambios semafóricos no forman parte de estos tres escenarios.</p>
      </section>
    </div>
  );
}
