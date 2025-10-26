export interface Airport {
  airport_id: number;
  name: string;
  city: string;
  country: string;
  iata_code: string;
  icao_code: string;
  latitude: number;
  longitude: number;
  altitude: number;
  timezone: number;
  dst: string;
  tz_database: string;
  type: string;
  source: string;
}

export interface TableInfo {
  name: string;
  current_count: number;
  recent_changes: number;
  last_change: string | null;
  primary_key: string;
}

export interface TimelineEntry {
  timestamp: string;
  change_count: number;
  changes: any[];
  has_mass_changes: boolean;
}

export interface DiffResult {
  added: any[];
  deleted: any[];
  modified: any[];
  summary: {
    total_added: number;
    total_deleted: number;
    total_modified: number;
  };
}

export interface RestoreSuggestion {
  suggested_timestamp: string;
  confidence_percentage: number;
  health_score: number;
  reason: string;
  warnings: string[];
}

export interface RestoreResult {
  success: boolean;
  records_restored?: number;
  final_count?: number;
  execution_time?: string;
  error?: string;
}