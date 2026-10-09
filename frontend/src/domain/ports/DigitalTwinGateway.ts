import type {
  DatasetMetadata,
  DemoMlResult,
  DemoState,
  DigitalTwinState,
  HealthStatus,
  PredictionCommand,
  ReplayCommand,
  RoadSegment,
  ScenarioCommand,
  SimulationResult,
  SimulationScenario,
  TrafficFilters,
  TrafficLocation,
  TrafficPrediction,
  TrafficQueryResult,
} from "../models";

export interface DigitalTwinGateway {
  getHealth(): Promise<HealthStatus>;
  getTwinState(): Promise<DigitalTwinState>;
  listRoadSegments(): Promise<RoadSegment[]>;
  listDatasets(): Promise<DatasetMetadata[]>;
  getDataset(datasetId: string): Promise<DatasetMetadata>;
  listLocations(region?: string): Promise<TrafficLocation[]>;
  queryTraffic(filters: TrafficFilters): Promise<TrafficQueryResult>;
  getMlExperiment(): Promise<DemoMlResult>;
  getReplayState(): Promise<DemoState>;
  startReplay(command: ReplayCommand): Promise<DemoState>;
  pauseReplay(): Promise<DemoState>;
  continueReplay(): Promise<DemoState>;
  stopReplay(): Promise<DemoState>;
  resetReplay(): Promise<DemoState>;
  predictTraffic(command: PredictionCommand): Promise<TrafficPrediction>;
  listScenarios(): Promise<SimulationScenario[]>;
  getScenarioResults(scenarioId: string): Promise<SimulationResult[]>;
  createScenario(command: ScenarioCommand): Promise<SimulationScenario>;
  runScenario(scenarioId: string): Promise<SimulationResult[]>;
}
