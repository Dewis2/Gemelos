import type { SimulationResult } from "./models";

export const DEMAND_LEVELS = ["baja", "normal", "alta"] as const;
export type DemandLevel = (typeof DEMAND_LEVELS)[number];

export const DEMAND_LEVEL_LABELS: Record<DemandLevel, string> = {
  baja: "Baja",
  normal: "Normal",
  alta: "Alta",
};

/**
 * Estructura de `configuration.demand`.
 *
 * El puerto `TrafficSimulatorPort.set_traffic_demand` recibe un objeto
 * (`dict[str, Any]`), por lo que `demand` no puede enviarse como número.
 * Ninguna clave es interpretada todavía: `FakeTrafficSimulator` descarta el
 * argumento y `SumoTrafficSimulator` mantiene el mapeo como tarea pendiente.
 * Se envía únicamente el nivel elegido por el usuario, sin magnitudes inventadas.
 */
export interface ScenarioDemand {
  level: DemandLevel;
}

export interface ScenarioConfiguration {
  demand: ScenarioDemand;
  steps: number;
}

/** `int(configuration["steps"])`. En el adaptador SUMO equivale a pasos de simulación. */
export const DEFAULT_SIMULATION_STEPS = 300;
export const MIN_SIMULATION_STEPS = 1;

export const DEMAND_NOT_INTERPRETED_NOTICE =
  "El simulador conectado todavía no interpreta la demanda: FakeTrafficSimulator descarta el argumento y el mapeo a rutas de SUMO sigue pendiente. El nivel se registra como configuración trazable, no altera el resultado.";

export const STEPS_NOTE =
  "steps es el número de pasos de simulación (1 segundo por paso con la longitud de paso por defecto de SUMO). El simulador actual valida el valor pero no lo aplica a ningún indicador.";

export interface ScenarioPreset {
  id: string;
  label: string;
  description: string;
  configuration: ScenarioConfiguration;
}

export const SCENARIO_PRESETS: readonly ScenarioPreset[] = [
  {
    id: "base",
    label: "Situación base",
    description: "Demanda de referencia para el corredor, sin variación.",
    configuration: { demand: { level: "normal" }, steps: DEFAULT_SIMULATION_STEPS },
  },
  {
    id: "incremento",
    label: "Incremento de demanda",
    description: "Demanda alta frente a la situación de referencia.",
    configuration: { demand: { level: "alta" }, steps: DEFAULT_SIMULATION_STEPS },
  },
  {
    id: "reduccion",
    label: "Demanda reducida",
    description: "Demanda baja frente a la situación de referencia.",
    configuration: { demand: { level: "baja" }, steps: DEFAULT_SIMULATION_STEPS },
  },
];

/** Capacidades de escenario que no tienen soporte en el adaptador actual y no se envían. */
export const PLANNED_CAPABILITIES: readonly { label: string; reason: string }[] = [
  {
    label: "Cierre o incidente",
    reason: "No implementado: ningún adaptador del proyecto acepta este parámetro. El campo se eliminó del contrato enviado.",
  },
  {
    label: "Cambio semafórico",
    reason: "No implementado: ningún adaptador del proyecto acepta un offset de señal. El campo se eliminó del contrato enviado.",
  },
];

/**
 * Un resultado es marcador de posición cuando todos sus indicadores están en cero
 * y no trae emisiones. En el estado actual del caso de uso esos ceros son literales
 * (`travel_time` y `delay` se fijan a 0.0 y `emissions` a {}), no una medición.
 */
export function isPlaceholderResult(result: SimulationResult): boolean {
  return (
    result.travel_time === 0 &&
    result.average_speed === 0 &&
    result.delay === 0 &&
    result.queue_length === 0 &&
    Object.keys(result.emissions ?? {}).length === 0
  );
}

export function resultsArePlaceholders(results: readonly SimulationResult[]): boolean {
  return results.length === 0 || results.every(isPlaceholderResult);
}

export function validateScenarioConfiguration(configuration: ScenarioConfiguration): void {
  if (!DEMAND_LEVELS.includes(configuration.demand.level)) {
    throw new RangeError(`Nivel de demanda no admitido: ${configuration.demand.level}.`);
  }
  if (!Number.isInteger(configuration.steps) || configuration.steps < MIN_SIMULATION_STEPS) {
    throw new RangeError(`steps debe ser un entero mayor o igual que ${MIN_SIMULATION_STEPS}.`);
  }
}
