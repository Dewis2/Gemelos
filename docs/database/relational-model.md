# Modelo relacional

El diagrama representa las once tablas existentes. Las ocho líneas corresponden únicamente a FK reales. La cardinalidad del padre es uno obligatorio por fila hija; un padre puede tener cero o muchas filas hijas. Los identificadores externos de la demostración no se dibujan como FK.

```mermaid
erDiagram
    intersections {
        uuid id PK "NOT NULL"
        varchar name "NOT NULL"
        geometry geometry "NULL POINT SRID 4326"
    }
    road_segments {
        uuid id PK "NOT NULL"
        varchar name "NOT NULL"
        uuid start_intersection_id FK "NOT NULL"
        uuid end_intersection_id FK "NOT NULL"
        integer lane_count "NOT NULL"
        float reference_speed "NOT NULL"
        geometry geometry "NULL LINESTRING SRID 4326"
    }
    data_sources {
        uuid id PK "NOT NULL"
        varchar name "NOT NULL"
        varchar source_type "NOT NULL"
        varchar description "NULL"
        boolean active "NOT NULL"
    }
    traffic_measurements {
        uuid id PK "NOT NULL"
        uuid source_id FK "NOT NULL"
        uuid road_segment_id FK "NOT NULL"
        timestamp_with_time_zone timestamp "NOT NULL"
        integer traffic_volume "NOT NULL"
        float average_speed "NULL"
        float occupancy "NULL"
    }
    traffic_signal_plans {
        uuid id PK "NOT NULL"
        uuid intersection_id FK "NOT NULL"
        varchar name "NOT NULL"
        jsonb phases "NOT NULL"
    }
    traffic_predictions {
        uuid id PK "NOT NULL"
        uuid road_segment_id FK "NOT NULL"
        timestamp_with_time_zone prediction_timestamp "NOT NULL"
        timestamp_with_time_zone target_timestamp "NOT NULL"
        float predicted_volume "NOT NULL"
        varchar model_version "NOT NULL"
    }
    simulation_scenarios {
        uuid id PK "NOT NULL"
        varchar name "NOT NULL"
        varchar description "NOT NULL"
        jsonb configuration "NOT NULL"
        timestamp_with_time_zone created_at "NOT NULL"
    }
    simulation_results {
        uuid id PK "NOT NULL"
        uuid scenario_id FK "NOT NULL"
        uuid road_segment_id FK "NOT NULL"
        float travel_time "NOT NULL"
        float average_speed "NOT NULL"
        float delay "NOT NULL"
        float queue_length "NOT NULL"
        jsonb emissions "NOT NULL"
        timestamp_with_time_zone created_at "NOT NULL"
    }
    traffic_aggregates {
        uuid id PK "NOT NULL"
        varchar natural_key UK "NOT NULL"
        varchar dataset_id "NOT NULL"
        varchar source_record_id "NOT NULL"
        varchar source_provider "NOT NULL"
        varchar source_country "NOT NULL"
        varchar source_region "NULL"
        varchar source_location_id "NOT NULL"
        varchar source_location_name "NOT NULL"
        date period_start "NOT NULL"
        date period_end "NOT NULL"
        varchar temporal_granularity "NOT NULL"
        varchar vehicle_category "NOT NULL"
        integer vehicle_count "NOT NULL"
        varchar dataset_scope "NOT NULL"
        jsonb metadata_json "NOT NULL"
        varchar ingestion_run_id "NULL"
    }
    traffic_locations {
        uuid id PK "NOT NULL"
        varchar dataset_id "NOT NULL UQ dataset_id-source_location_id"
        varchar source_location_id "NOT NULL UQ dataset_id-source_location_id"
        varchar name "NOT NULL"
        varchar type "NOT NULL"
        varchar operator "NULL"
        varchar status "NULL"
        geometry geometry "NOT NULL POINT SRID 4326"
        jsonb properties_json "NOT NULL"
    }
    dataset_ingestion_runs {
        uuid id PK "NOT NULL"
        varchar dataset_id "NOT NULL"
        timestamp_with_time_zone started_at "NOT NULL"
        timestamp_with_time_zone finished_at "NULL"
        varchar status "NOT NULL"
        integer files_processed "NOT NULL"
        integer rows_read "NOT NULL"
        integer rows_valid "NOT NULL"
        integer rows_rejected "NOT NULL"
        integer rows_inserted "NOT NULL"
        integer rows_updated "NOT NULL"
        integer duplicates "NOT NULL"
        text error_message "NULL"
    }
    intersections ||--o{ road_segments : inicio
    intersections ||--o{ road_segments : fin
    data_sources ||--o{ traffic_measurements : origen
    road_segments ||--o{ traffic_measurements : observaciones
    intersections ||--o{ traffic_signal_plans : planes
    road_segments ||--o{ traffic_predictions : predicciones
    simulation_scenarios ||--o{ simulation_results : resultados
    road_segments ||--o{ simulation_results : tramo
```

Las tablas traffic_aggregates, traffic_locations y dataset_ingestion_runs aparecen independientes porque las migraciones no declaran FK entre ellas. En traffic_locations la unicidad es conjunta: dataset_id + source_location_id. No se presupone que los puntos externos equivalgan a tramos del corredor.

Fuente: migraciones 0001 y 0002, modelos ORM y modelo relacional aportado por el responsable de BD. El diagrama se conserva como texto editable y GitHub lo renderiza en Markdown.

[Diccionario completo](data-dictionary.md) · [Integridad e índices](physical-model.md)
