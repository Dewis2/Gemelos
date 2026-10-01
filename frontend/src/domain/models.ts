import type { ModelFeatureValues } from "./corridor";
import type { ScenarioConfiguration } from "./scenarios";

export interface HealthStatus {
  status: string;
  stage: string;
}

export interface DigitalTwinState {
  status: string;
  corridor: string;
  road_segment_count: number;
  intersection_count: number;
  geometry_status: string;
  latest_measurements: unknown[];
}

export interface DatasetMetadata {
  dataset_id: string;
  title: string;
  provider: string;
  country: string;
  source_type: string;
  temporal_granularity: string;
  spatial_granularity: string;
  period_min: string | null;
  period_max: string | null;
  license: string;
  source_page: string;
  local_validation: boolean;
  allowed_uses: Record<string, boolean>;
  limitations: string[];
}

export interface TrafficLocation {
  source_location_id: string;
  name: string;
  region: string | null;
  province: string | null;
  district: string | null;
  longitude: number;
  latitude: number;
  operator: string | null;
  status: string | null;
  location_type: string;
}

export interface TrafficRecord {
  dataset_id: string;
  source_location_id: string;
  source_location_name: string;
  source_region: string | null;
  period_start: string;
  vehicle_category: string;
  vehicle_count: number;
  dataset_scope: string;
  metadata: Record<string, unknown>;
}

export interface TrafficQueryFilters {
  region: string | null;
  location_id: string | null;
  start_period: string | null;
  end_period: string | null;
  vehicle_category: string | null;
}

export interface TrafficQueryResult {
  dataset: DatasetMetadata;
  filters: TrafficQueryFilters;
  record_count: number;
  records_returned: number;
  total_vehicles: number;
  category_totals: Record<string, number>;
  series: { period: string; vehicle_count: number }[];
  records: TrafficRecord[];
  source_label: string;
  warning: string;
}

export interface TrafficFilters {
  datasetId: string;
  region?: string;
  locationId?: string;
  startPeriod?: string;
  endPeriod?: string;
  vehicleType?: string;
  limit?: number;
}

export interface DemoState {
  mode: string;
  status: string;
  current_dataset: string | null;
  current_location: string | null;
  current_historical_period: string | null;
  vehicle_count: number | null;
  vehicle_categories: Record<string, number>;
  last_update: string | null;
  source_provider: string | null;
  replay_speed: number | null;
  replay_position: number;
  replay_total: number;
  technical_status: Record<string, string>;
  events: { timestamp: string; stage: string; message: string }[];
}

export interface ReplayCommand {
  datasetId: string;
  startPeriod?: string;
  endPeriod?: string;
  locationId?: string;
  speedFactor: number;
  limit?: number;
}

export interface DemoMlResult {
  warning: string;
  training_dataset: string;
  provider?: string;
  experiment?: string;
  scope?: string;
  target?: string;
  features?: string[];
  created_at?: string;
  temporal_split?: boolean;
  train_rows?: number;
  test_rows?: number;
  model_artifact?: string;
  selected_model: string;
  model_version?: string;
  rows_total?: number;
  geography?: string;
  training_period: { min: string; max: string };
  test_period: { min: string; max: string };
  metrics: Record<string, { mae: number; rmse: number; r2: number; mape: number | null }>;
  prediction_series: { period: string; actual: number; predicted: number }[];
}

export interface RoadSegment {
  id: string;
  name: string;
  start_intersection_id: string;
  end_intersection_id: string;
  lane_count: number;
  reference_speed: number;
  geometry: string | null;
}

export interface PredictionCommand {
  roadSegmentId: string;
  targetTimestamp: string;
  features: ModelFeatureValues;
}

export interface TrafficPrediction {
  id: string;
  road_segment_id: string;
  prediction_timestamp: string;
  target_timestamp: string;
  predicted_volume: number;
  model_version: string;
}

export interface ScenarioCommand {
  name: string;
  description: string;
  configuration: ScenarioConfiguration;
}

export interface SimulationScenario extends ScenarioCommand {
  id: string;
  created_at: string;
}

export interface SimulationResult {
  id: string;
  scenario_id: string;
  road_segment_id: string;
  travel_time: number;
  average_speed: number;
  delay: number;
  queue_length: number;
  emissions: Record<string, number>;
  created_at: string;
}

export interface DashboardOverview {
  health: HealthStatus;
  twin: DigitalTwinState;
  datasets: DatasetMetadata[];
  replay: DemoState;
}

export interface ScenarioExecution {
  scenario: SimulationScenario;
  results: SimulationResult[];
}
