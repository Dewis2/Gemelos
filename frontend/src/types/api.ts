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

