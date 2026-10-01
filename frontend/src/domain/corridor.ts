export const PROJECT_TITLE =
  "Gemelo Digital Inteligente para el análisis predictivo y simulación de la movilidad urbana en la Av. Ferrocarril, Huancayo";

export const CORRIDOR_NAME = "Av. Ferrocarril";
export const CORRIDOR_FROM = "Av. Giráldez";
export const CORRIDOR_TO = "Av. Huancavelica";
export const CORRIDOR_LABEL = `${CORRIDOR_NAME} · Huancayo`;
export const CORRIDOR_SCOPE = `${CORRIDOR_FROM} → ${CORRIDOR_TO}`;

export const CORRIDOR_SEQUENCE: readonly string[] = [CORRIDOR_FROM, CORRIDOR_NAME, CORRIDOR_TO];

export const CORRIDOR_GEOMETRY_NOTICE =
  "Representación esquemática del corredor. Geometría exacta pendiente de validación cartográfica.";

/**
 * Segmentación técnica del PMV, sembrada por el backend en `infrastructure/corridor_reference.py`.
 * Los UUID son estables y se derivan de esos nombres; se usan para enlazar el esquema.
 */
export const CORRIDOR_TECHNICAL_SEGMENTS: readonly { key: string; label: string; referencePoints: string[] }[] = [
  { key: "segment:giraldez-limite-norte", label: "tramo norte", referencePoints: ["P03", "P04"] },
  { key: "segment:limite-norte-limite-sur", label: "tramo centro", referencePoints: [] },
  { key: "segment:limite-sur-huancavelica", label: "tramo sur", referencePoints: ["P42"] },
];

export const SEGMENTATION_NOTICE =
  "Segmentación técnica del PMV. No es una división oficial del municipio y no implica cruces, semáforos ni longitudes verificadas.";

export type DayPeriodId = "morning" | "midday" | "night";

export const DAY_PERIODS: readonly { id: DayPeriodId; label: string }[] = [
  { id: "morning", label: "Mañana" },
  { id: "midday", label: "Mediodía" },
  { id: "night", label: "Noche" },
];

export const HISTORICAL_YEAR = 2013;

export interface CountPoint {
  id: string;
  description: string;
  /** El repositorio no contiene coordenadas verificadas para los puntos de aforo. */
  coordinates: { latitude: number; longitude: number } | null;
  values: Record<DayPeriodId, number>;
}

export const COUNT_POINTS: readonly CountPoint[] = [
  {
    id: "P03",
    description: `${CORRIDOR_FROM}, tramo próximo a ${CORRIDOR_NAME}`,
    coordinates: null,
    values: { morning: 1779, midday: 1744, night: 1888 },
  },
  {
    id: "P04",
    description: `${CORRIDOR_NAME}, tramo próximo a ${CORRIDOR_FROM}`,
    coordinates: null,
    values: { morning: 1593, midday: 1501, night: 1730 },
  },
  {
    id: "P42",
    description: `${CORRIDOR_NAME}, tramo próximo a ${CORRIDOR_TO}`,
    coordinates: null,
    values: { morning: 553, midday: 559, night: 545 },
  },
];

export const HISTORICAL_SOURCE = {
  datasetId: "huancayo_historical_counts_2013",
  provider: "Municipalidad Provincial de Huancayo",
  title: "Plan Regulador de Rutas de Transporte Urbano",
  year: HISTORICAL_YEAR,
  label: "Datos históricos de referencia — Municipalidad Provincial de Huancayo. No representan tráfico actual de 2026.",
  period: `${HISTORICAL_YEAR}`,
} as const;

export type SourceCategory =
  | "local_historical"
  | "ml_experiment"
  | "regional_demo"
  | "simulated";

export const SOURCE_CATEGORY_LABELS: Record<SourceCategory, string> = {
  local_historical: `Histórico local · Huancayo ${HISTORICAL_YEAR}`,
  ml_experiment: "Experimental IA · MITV-UCI",
  regional_demo: "Regional / demostración",
  simulated: "Simulado · no observado",
};

export const REGIONAL_DATASETS = {
  mtcTollFlow: "mtc_peru_toll_flow",
  mtcTollLocations: "mtc_peru_toll_locations",
  ositranRoadTraffic: "ositran_peru_road_traffic",
} as const;

export const REGIONAL_DATASET_NOTICE =
  "Datos regionales del Estado peruano. Corresponden a peajes y carreteras fuera del corredor urbano de la Av. Ferrocarril y no deben interpretarse como tráfico de Huancayo.";

/**
 * Dataset académico documentado para la PoC de Machine Learning, según `data/README.md`.
 * Se declara como documentado y no publicado: el repositorio no lo contiene, por lo que
 * todavía no respalda ninguna métrica ni ningún modelo entrenado.
 */
export const DOCUMENTED_ACADEMIC_DATASET = {
  name: "Metro Interstate Traffic Volume (MITV-UCI)",
  geography: "Minnesota, EE. UU.",
  status: "documentado, no disponible en el repositorio",
  notice:
    "Dataset académico externo documentado para la experimentación técnica del pipeline. Sus observaciones pertenecen a Minnesota, EE. UU.: no constituyen evidencia sobre Huancayo ni deben mezclarse con una evaluación local. El repositorio no contiene el archivo, así que todavía no sustenta métricas ni modelo propio.",
} as const;

/**
 * Contrato de entrada del modelo servido por `POST /api/v1/predictions/traffic-flow`.
 *
 * El orden es el alfabético de los nombres a propósito: el adaptador del backend
 * construye su vector con `sorted(features)`, de modo que entrenamiento,
 * inferencia y servicio solo coinciden si el orden se mantiene.
 */
export const MODEL_FEATURES = ["day_of_week", "hour", "is_weekend", "month"] as const;
export type ModelFeature = (typeof MODEL_FEATURES)[number];

export type ModelFeatureValues = Record<ModelFeature, number>;

export const ML_INFERENCE_CONTRACT = {
  endpoint: "POST /api/v1/predictions/traffic-flow",
  unit: "veh/h",
  notValidatedNotice:
    "El modelo todavía no ha sido validado con datos locales actuales de la Av. Ferrocarril. Su predicción no representa tráfico de Huancayo.",
  datasetUnresolvedNotice:
    "El conjunto de datos con el que se entrenará este modelo aún no está disponible en el repositorio, por lo que el origen del modelo no puede declararse aquí.",
  segmentAgnosticNotice:
    "El modelo utiliza únicamente variables temporales y no diferencia los segmentos del corredor.",
} as const;

/** Piezas que producen o intentan producir indicadores sin observación real. */
export const SIMULATION_COMPONENTS = {
  fakeSimulator: {
    name: "FakeTrafficSimulator",
    role: "Adaptador de prueba determinista",
    notice:
      "Devuelve indicadores constantes: travel_time y delay se fijan a 0 y emissions a vacío en el caso de uso, y el adaptador no calcula velocidad ni cola. No es un motor de simulación.",
  },
  sumo: {
    name: "SUMO / TraCI",
    role: "Simulador previsto para escenarios",
    notice:
      "Implementado como adaptador pero no operativo: requiere un archivo .sumocfg validado y una topología del corredor, y no se incluye en el contenedor.",
  },
} as const;

/** Nombres de las franjas, para mostrar la convención de día de semana al usuario. */
export const WEEKDAY_NAMES = [
  "lunes",
  "martes",
  "miércoles",
  "jueves",
  "viernes",
  "sábado",
  "domingo",
] as const;

export function classifyDataset(datasetId: string): SourceCategory {
  if (datasetId === HISTORICAL_SOURCE.datasetId) return "local_historical";
  return "regional_demo";
}

/**
 * Deriva las cuatro variables de entrada del modelo a partir de la fecha y hora objetivo.
 *
 * La convención de día de semana debe coincidir con `pandas.Timestamp.dayofweek`
 * (usada en `ml/src/features/features.py`), donde lunes = 0 y domingo = 6.
 * `Date.getDay()` de JavaScript devuelve domingo = 0 y sábado = 6, por lo que se
 * rota con `(getDay() + 6) % 7`.
 */
export function buildModelFeatures(targetTimestamp: string): ModelFeatureValues {
  const date = new Date(targetTimestamp);
  if (!targetTimestamp || Number.isNaN(date.getTime())) {
    throw new RangeError("La fecha y hora objetivo no son válidas.");
  }
  const javascriptDay = date.getDay();
  return {
    day_of_week: (javascriptDay + 6) % 7,
    hour: date.getHours(),
    is_weekend: javascriptDay === 0 || javascriptDay === 6 ? 1 : 0,
    month: date.getMonth() + 1,
  };
}

export function getCountPoint(pointId: string): CountPoint | undefined {
  return COUNT_POINTS.find((point) => point.id === pointId);
}
