// Types for hardware device integration
export interface Device {
  id: number;
  device_id: string;
  manufacturer?: string;
  model?: string;
  name: string;
  connection_type: string;
  status: "online" | "offline" | "unknown";
  is_active: boolean;
  last_seen_at?: string;
  created_at: string;
}

export interface MeasurementValue {
  value: number;
  unit: string;
}

export interface HardwareReading {
  id: number;
  device_id: number;
  user_id: number;
  reading_timestamp?: string;
  source: string;
  manufacturer?: string;
  model?: string;
  measurements: Record<string, MeasurementValue>;
  soil_test_id?: number;
  created_at: string;
}

export interface ReadingIngestionPayload {
  timestamp?: string;
  measurements: Record<string, MeasurementValue>;
}

export interface DeviceCreatePayload {
  device_id: string;
  manufacturer?: string;
  model?: string;
  name: string;
  connection_type: string;
}

export interface DeviceProfile {
  manufacturer: string;
  model: string;
  connection_type: string;
  integration_status: string;
  notes: string;
}
