import type { SoilParameters } from "./soil";

export interface SoilReport {
  id: number | string;
  soil_test_id?: number | string;
  file_name?: string;
  file_url?: string;
  status?: string;
  extracted_text?: string;
  extracted_parameters?: SoilParameters;
  created_at?: string;
}
