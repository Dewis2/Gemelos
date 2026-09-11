import { useTwinState } from "../hooks/useTwinState";
import { CorridorMap } from "../maps/CorridorMap";

function Placeholder({ title, text }: { title: string; text: string }) {
  return <><header><p className="eyebrow">Módulo en preparación</p><h2>{title}</h2></header><section className="panel"><p>{text}</p><p className="muted">Pendiente de datos locales y validación del PMV.</p></section></>;
}

export function Dashboard() {
  const { data, error } = useTwinState();
  return <><header><p className="eyebrow">Estado del prototipo</p><h2>Movilidad urbana, observable y extensible</h2><p>Base tecnológica para integrar mediciones, predicción y simulación sin presentar supuestos como evidencia.</p></header><div className="cards"><article><span>Corredor</span><strong>Av. Giráldez — Av. Huancavelica</strong></article><article><span>Etapa</span><strong>{data?.status ?? "PoC"}</strong></article><article><span>API</span><strong>{error ? "No disponible" : data ? "Conectada" : "Consultando…"}</strong></article></div><CorridorMap /></>;
}

export function MapPage() { return <><header><p className="eyebrow">Representación espacial</p><h2>Mapa del corredor</h2></header><CorridorMap /></>; }
export function PredictionPage() { return <Placeholder title="Predicción de flujo" text="Aquí se compararán el baseline lineal y Random Forest tras entrenarlos con una división temporal válida." />; }
export function ScenariosPage() { return <Placeholder title="Escenarios what-if" text="Creación y ejecución de configuraciones de simulación sobre una red SUMO validada." />; }
export function ComparisonPage() { return <Placeholder title="Comparación de escenarios" text="Vista preparada para contrastar tiempos, velocidades, demoras y colas obtenidos por el simulador." />; }
export function SourcesPage() { return <Placeholder title="Fuentes de datos" text="Distingue benchmark externo, aforos históricos 2013 y datos locales actuales aún pendientes." />; }
export function StatusPage() { return <Placeholder title="Estado del sistema" text="Supervisión futura de API, base de datos, MQTT, modelo ML y SUMO." />; }
export function LoginPage() { return <div className="login"><p className="eyebrow">Acceso futuro</p><h2>Login placeholder</h2><p>JWT se incorporará en una fase posterior. No existen usuarios ni credenciales reales.</p></div>; }

