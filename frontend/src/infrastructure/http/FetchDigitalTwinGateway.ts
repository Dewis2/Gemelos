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
} from "../../domain/models";
import type { DigitalTwinGateway } from "../../domain/ports/DigitalTwinGateway";

export class HttpRequestError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export class FetchDigitalTwinGateway implements DigitalTwinGateway {
  constructor(private readonly baseUrl: string) {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, init);
    if (!response.ok) {
      const raw = await response.text();
      let message = raw || `La API respondió con estado ${response.status}.`;
      try {
        const parsed = JSON.parse(raw) as { detail?: string };
        message = parsed.detail ?? message;
      } catch {
        // La API puede devolver texto plano; se conserva como mensaje.
      }
      throw new HttpRequestError(message, response.status);
    }
    return response.json() as Promise<T>;
  }

  private post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  }

  getHealth() { return this.request<HealthStatus>("/health"); }
  getTwinState() { return this.request<DigitalTwinState>("/api/v1/digital-twin/state"); }
  listRoadSegments() { return this.request<RoadSegment[]>("/api/v1/road-segments"); }
  listDatasets() { return this.request<DatasetMetadata[]>("/api/v1/datasets"); }
  getDataset(datasetId: string) { return this.request<DatasetMetadata>(`/api/v1/datasets/${encodeURIComponent(datasetId)}`); }

  listLocations(region?: string) {
    const query = region ? `?region=${encodeURIComponent(region)}` : "";
    return this.request<TrafficLocation[]>(`/api/v1/demo/peru/locations${query}`);
  }

  queryTraffic(filters: TrafficFilters) {
    const params = new URLSearchParams({ dataset_id: filters.datasetId, limit: String(filters.limit ?? 500) });
    if (filters.region) params.set("region", filters.region);
    if (filters.locationId) params.set("location_id", filters.locationId);
    if (filters.startPeriod) params.set("start_period", filters.startPeriod);
    if (filters.endPeriod) params.set("end_period", filters.endPeriod);
    if (filters.vehicleType) params.set("vehicle_type", filters.vehicleType);
    return this.request<TrafficQueryResult>(`/api/v1/demo/peru/traffic?${params}`);
  }

  getMlExperiment() { return this.request<DemoMlResult>("/api/v1/demo/peru/ml"); }
  getReplayState() { return this.request<DemoState>("/api/v1/demo/peru/state"); }
  startReplay(command: ReplayCommand) {
    return this.post<DemoState>("/api/v1/demo/peru/replay/start", {
      dataset_id: command.datasetId,
      start_period: command.startPeriod || null,
      end_period: command.endPeriod || null,
      location_id: command.locationId || null,
      speed_factor: command.speedFactor,
      limit: command.limit ?? 60,
    });
  }
  pauseReplay() { return this.post<DemoState>("/api/v1/demo/peru/replay/pause"); }
  continueReplay() { return this.post<DemoState>("/api/v1/demo/peru/replay/continue"); }
  stopReplay() { return this.post<DemoState>("/api/v1/demo/peru/replay/stop"); }
  resetReplay() { return this.post<DemoState>("/api/v1/demo/peru/replay/reset"); }

  predictTraffic(command: PredictionCommand) {
    return this.post<TrafficPrediction>("/api/v1/predictions/traffic-flow", {
      road_segment_id: command.roadSegmentId,
      target_timestamp: command.targetTimestamp,
      features: command.features,
    });
  }

  listScenarios() { return this.request<SimulationScenario[]>("/api/v1/scenarios"); }
  getScenarioResults(scenarioId: string) {
    return this.request<SimulationResult[]>(`/api/v1/scenarios/${encodeURIComponent(scenarioId)}/results`);
  }

  createScenario(command: ScenarioCommand) {
    return this.post<SimulationScenario>("/api/v1/scenarios", command);
  }

  runScenario(scenarioId: string) {
    return this.post<SimulationResult[]>(`/api/v1/scenarios/${encodeURIComponent(scenarioId)}/run`);
  }
}
