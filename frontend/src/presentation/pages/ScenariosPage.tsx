import { type FormEvent, useMemo, useState } from "react";
import type { SimulationResult, SimulationScenario } from "../../domain/models";
import {
  DEFAULT_SIMULATION_STEPS,
  DEMAND_LEVELS,
  DEMAND_LEVEL_LABELS,
  DEMAND_NOT_INTERPRETED_NOTICE,
  PLANNED_CAPABILITIES,
  SCENARIO_PRESETS,
  STEPS_NOTE,
  resultsArePlaceholders,
  type DemandLevel,
  type ScenarioConfiguration,
} from "../../domain/scenarios";
import { useApplication } from "../ApplicationContext";
import { DataProvenanceNotice } from "../components/DataProvenanceNotice";
import { SourceTag } from "../components/SourceTag";

const formatNumber = new Intl.NumberFormat("es-PE", { maximumFractionDigits: 2 });

type RunPhase = "idle" | "running" | "completed" | "failed";

const PHASE_LABELS: Record<RunPhase, string> = {
  idle: "Sin ejecutar",
  running: "Ejecutando",
  completed: "Ejecución completada",
  failed: "Ejecución fallida",
};

export function ScenariosPage() {
  const application = useApplication();
  const [presetId, setPresetId] = useState<string>(SCENARIO_PRESETS[0].id);
  const [name, setName] = useState<string>(SCENARIO_PRESETS[0].label);
  const [description, setDescription] = useState<string>(SCENARIO_PRESETS[0].description);
  const [demandLevel, setDemandLevel] = useState<DemandLevel>(SCENARIO_PRESETS[0].configuration.demand.level);
  const [steps, setSteps] = useState<string>(String(DEFAULT_SIMULATION_STEPS));
  const [scenario, setScenario] = useState<SimulationScenario | null>(null);
  const [results, setResults] = useState<SimulationResult[] | null>(null);
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [error, setError] = useState<string | null>(null);

  const configuration = useMemo<ScenarioConfiguration>(
    () => ({ demand: { level: demandLevel }, steps: Number(steps) }),
    [demandLevel, steps],
  );

  const createPayload = useMemo(
    () => ({ name: name.trim(), description: description.trim(), configuration }),
    [name, description, configuration],
  );

  const placeholders = results === null ? false : resultsArePlaceholders(results);

  const applyPreset = (id: string) => {
    const preset = SCENARIO_PRESETS.find((item) => item.id === id);
    if (!preset) return;
    setPresetId(id);
    setName(preset.label);
    setDescription(preset.description);
    setDemandLevel(preset.configuration.demand.level);
    setSteps(String(preset.configuration.steps));
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setPhase("running");
    setError(null);
    setScenario(null);
    setResults(null);
    application
      .createAndRunScenario({ name, description, configuration })
      .then((execution) => {
        setScenario(execution.scenario);
        setResults(execution.results);
        setPhase("completed");
      })
      .catch((reason: unknown) => {
        setPhase("failed");
        setError(reason instanceof Error ? reason.message : "No se pudo ejecutar el escenario.");
      });
  };

  return (
    <div className="feature-page">
      <header className="page-heading">
        <p className="eyebrow">Simulación</p>
        <h2>Escenarios what-if</h2>
        <p>
          Registra la configuración de un escenario en el backend y solicita su ejecución. Solo se envían los parámetros que el simulador actual admite.
        </p>
      </header>

      <DataProvenanceNotice category="simulated">
        Fuente: simulación. Los resultados no son mediciones del corredor Av. Ferrocarril ni observación de campo.
      </DataProvenanceNotice>

      {error && <div className="error-box" role="alert">{error}</div>}

      <section className="panel">
        <h3>Tipos de escenario disponibles</h3>
        <div className="preset-grid">
          {SCENARIO_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              className={preset.id === presetId ? "preset active" : "preset"}
              onClick={() => applyPreset(preset.id)}
            >
              <strong>{preset.label}</strong>
              <small>{preset.description}</small>
            </button>
          ))}
        </div>
        <h4>Funcionalidad planificada, no implementada en el simulador actual</h4>
        <ul className="planned-list">
          {PLANNED_CAPABILITIES.map((item) => (
            <li key={item.label}>
              <strong>{item.label}</strong>
              <span>{item.reason}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel form-panel">
        <div>
          <h3>Configuración del escenario</h3>
          <p className="muted">
            Contrato real del backend: <code>configuration.demand</code> es un objeto y <code>configuration.steps</code> es un entero.
          </p>
        </div>
        <form onSubmit={submit}>
          <label>
            Nombre
            <input value={name} onChange={(event) => setName(event.target.value)} required minLength={3} />
          </label>
          <label>
            Nivel de demanda
            <select value={demandLevel} onChange={(event) => setDemandLevel(event.target.value as DemandLevel)}>
              {DEMAND_LEVELS.map((level) => <option key={level} value={level}>{DEMAND_LEVEL_LABELS[level]}</option>)}
            </select>
            <small>{DEMAND_NOT_INTERPRETED_NOTICE}</small>
          </label>
          <label>
            Pasos de simulación
            <input type="number" min={1} step={1} value={steps} onChange={(event) => setSteps(event.target.value)} />
            <small>{STEPS_NOTE}</small>
          </label>
          <label className="field-blocked">
            Incidente
            <input type="text" value="No implementado" disabled readOnly />
            <small>No se envía al backend.</small>
          </label>
          <button className="primary" disabled={phase === "running"}>
            {phase === "running" ? "Ejecutando…" : "Crear y ejecutar"}
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <h3>Estado de ejecución</h3>
            <p className="muted">
              {scenario ? `Escenario ${scenario.id}` : "Todavía no se ha creado ningún escenario en esta sesión."}
            </p>
          </div>
          <div className="dataset-badges">
            <span className="source-tag" data-category="neutral" data-phase={phase}>{PHASE_LABELS[phase]}</span>
            <SourceTag category="simulated" />
          </div>
        </div>

        {results !== null && (
          <>
            <div className="metric-row">
              <span>Filas devueltas<strong>{results.length}</strong></span>
              <span>Tipo de resultado<strong>{placeholders ? "Marcador de posición" : "Métricas del simulador"}</strong></span>
            </div>

            {placeholders ? (
              <div className="placeholder-note">
                <strong>Simulador técnico aún no produce métricas físicas para este escenario.</strong>
                <p>
                  El caso de uso fija <code>travel_time</code> y <code>delay</code> en 0 y <code>emissions</code> vacío de forma literal, y el adaptador
                  de simulación conectado no calcula velocidad ni cola. Por eso no se muestran valores: presentarlos como indicadores sería engañoso.
                </p>
                <p className="source-note">
                  Filas recibidas: {results.length === 0
                    ? "ninguna, porque la red del corredor todavía no tiene tramos registrados."
                    : results.map((result) => result.road_segment_id).join(", ")}
                </p>
              </div>
            ) : (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Tramo</th>
                      <th>Tiempo de viaje (s)</th>
                      <th>Velocidad (km/h)</th>
                      <th>Demora (s)</th>
                      <th>Cola (veh)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((result) => (
                      <tr key={result.id}>
                        <td>{result.road_segment_id}</td>
                        <td>{formatNumber.format(result.travel_time)}</td>
                        <td>{formatNumber.format(result.average_speed)}</td>
                        <td>{formatNumber.format(result.delay)}</td>
                        <td>{formatNumber.format(result.queue_length)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </section>

      <section className="panel">
        <h3>Solicitud enviada</h3>
        <pre className="payload">{JSON.stringify(
          {
            create: { method: "POST", path: "/api/v1/scenarios", body: createPayload },
            run: { method: "POST", path: scenario ? `/api/v1/scenarios/${scenario.id}/run` : "/api/v1/scenarios/{id}/run" },
          },
          null,
          2,
        )}</pre>
        <p className="source-note">
          El cuerpo solo contiene <code>name</code>, <code>description</code> y <code>configuration</code> con las claves <code>demand</code> y <code>steps</code>. No se envía ningún otro parámetro.
        </p>
      </section>
    </div>
  );
}
