import { MODEL_FEATURES, type ModelFeature } from "../domain/corridor";
import { validateScenarioConfiguration } from "../domain/scenarios";
import type {
  DashboardOverview,
  DatasetMetadata,
  DemoMlResult,
  DemoState,
  PredictionCommand,
  ReplayCommand,
  RoadSegment,
  ScenarioCommand,
  ScenarioExecution,
  TrafficFilters,
  TrafficLocation,
  TrafficPrediction,
  TrafficQueryResult,
} from "../domain/models";
import type { DigitalTwinGateway } from "../domain/ports/DigitalTwinGateway";

export class ApplicationValidationError extends Error {}

export class DigitalTwinApplication {
  constructor(private readonly gateway: DigitalTwinGateway) {}

  async loadDashboard(): Promise<DashboardOverview> {
    const [health, twin, datasets, replay] = await Promise.all([
      this.gateway.getHealth(),
      this.gateway.getTwinState(),
      this.gateway.listDatasets(),
      this.gateway.getReplayState(),
    ]);
    return { health, twin, datasets, replay };
  }

  listDatasets(): Promise<DatasetMetadata[]> {
    return this.gateway.listDatasets();
  }

  listLocations(region?: string): Promise<TrafficLocation[]> {
    return this.gateway.listLocations(region);
  }

  queryTraffic(filters: TrafficFilters): Promise<TrafficQueryResult> {
    if (!filters.datasetId.trim()) {
      throw new ApplicationValidationError("Seleccione una fuente de datos.");
    }
    if (filters.startPeriod && filters.endPeriod && filters.startPeriod > filters.endPeriod) {
      throw new ApplicationValidationError("El periodo inicial no puede ser posterior al periodo final.");
    }
    return this.gateway.queryTraffic({ ...filters, limit: filters.limit ?? 500 });
  }

  getReplayState(): Promise<DemoState> {
    return this.gateway.getReplayState();
  }

  startReplay(command: ReplayCommand): Promise<DemoState> {
    if (command.speedFactor <= 0) {
      throw new ApplicationValidationError("La velocidad de reproducción debe ser mayor que cero.");
    }
    return this.gateway.startReplay({ ...command, limit: command.limit ?? 60 });
  }

  pauseReplay(): Promise<DemoState> {
    return this.gateway.pauseReplay();
  }

  continueReplay(): Promise<DemoState> {
    return this.gateway.continueReplay();
  }

  stopReplay(): Promise<DemoState> {
    return this.gateway.stopReplay();
  }

  resetReplay(): Promise<DemoState> {
    return this.gateway.resetReplay();
  }

  getMlExperiment(): Promise<DemoMlResult> {
    return this.gateway.getMlExperiment();
  }

  listRoadSegments(): Promise<RoadSegment[]> {
    return this.gateway.listRoadSegments();
  }

  predictTraffic(command: PredictionCommand): Promise<TrafficPrediction> {
    if (!command.roadSegmentId || !command.targetTimestamp) {
      throw new ApplicationValidationError("Seleccione un tramo y una fecha objetivo.");
    }
    const missing = MODEL_FEATURES.filter((feature) => !(feature in command.features));
    if (missing.length) {
      throw new ApplicationValidationError(`Faltan variables de entrada del modelo: ${missing.join(", ")}.`);
    }
    const extra = Object.keys(command.features).filter((key) => !MODEL_FEATURES.includes(key as ModelFeature));
    if (extra.length) {
      throw new ApplicationValidationError(`Variables no esperadas por el modelo: ${extra.join(", ")}.`);
    }
    const values = MODEL_FEATURES.map((feature) => [feature, command.features[feature]] as const);
    if (values.some(([, value]) => !Number.isFinite(value))) {
      throw new ApplicationValidationError("Todas las variables predictivas deben ser numéricas.");
    }
    const invalid = values.find(([feature, value]) => {
      switch (feature) {
        case "day_of_week": return value < 0 || value > 6;
        case "hour": return value < 0 || value > 23;
        case "is_weekend": return value !== 0 && value !== 1;
        case "month": return value < 1 || value > 12;
        default: return false;
      }
    });
    if (invalid) {
      throw new ApplicationValidationError(`El valor de ${invalid[0]} está fuera del rango admitido (${invalid[1]}).`);
    }
    return this.gateway.predictTraffic(command);
  }

  async createAndRunScenario(command: ScenarioCommand): Promise<ScenarioExecution> {
    if (command.name.trim().length < 3) {
      throw new ApplicationValidationError("El escenario debe tener un nombre de al menos tres caracteres.");
    }
    validateScenarioConfiguration(command.configuration);
    const scenario = await this.gateway.createScenario({ ...command, name: command.name.trim() });
    const results = await this.gateway.runScenario(scenario.id);
    return { scenario, results };
  }
}
