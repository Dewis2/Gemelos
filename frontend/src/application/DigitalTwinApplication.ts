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
    if (Object.values(command.features).some((value) => !Number.isFinite(value))) {
      throw new ApplicationValidationError("Todas las variables predictivas deben ser numéricas.");
    }
    return this.gateway.predictTraffic(command);
  }

  async createAndRunScenario(command: ScenarioCommand): Promise<ScenarioExecution> {
    if (command.name.trim().length < 3) {
      throw new ApplicationValidationError("El escenario debe tener un nombre de al menos tres caracteres.");
    }
    const scenario = await this.gateway.createScenario({ ...command, name: command.name.trim() });
    const results = await this.gateway.runScenario(scenario.id);
    return { scenario, results };
  }
}
