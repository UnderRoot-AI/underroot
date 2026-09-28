export interface SoilParameters {
  ph?: number;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ec?: number;
  moisture?: number;
  temperature?: number;
  organic_carbon?: number;
}

export interface SoilTest {
  id: number | string;
  field_id?: number | string;
  field_name?: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  tested_at?: string;
  created_at?: string;
  parameters: SoilParameters;
  health_score?: number;
  health_status?: string;
  notes?: string;
}

export interface SoilTestPayload {
  field_id?: number | string;
  location?: string;
  latitude?: number;
  longitude?: number;
  parameters: SoilParameters;
  notes?: string;
}
