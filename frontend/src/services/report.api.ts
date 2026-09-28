import { api } from "./api";
import type { SoilReport } from "../types/report";

export const reportApi = {
  async get(id: number | string) {
    const { data } = await api.get<SoilReport>(`/reports/${id}`);
    return data;
  },
  async generate(soilTestId: number | string) {
    const { data } = await api.post<SoilReport>("/reports/generate", {
      soil_test_id: soilTestId
    });
    return data;
  }
};


export interface VerifyReportPayload {
  parameters: Record<string, number | undefined>;
  location?: string;
  latitude?: number;
  longitude?: number;
  notes?: string;
}

export const verifyReport = async (id: number | string, payload: VerifyReportPayload) => {
  const { data } = await api.post<SoilReport>(`/reports/${id}/verify`, payload);
  return data;
};
