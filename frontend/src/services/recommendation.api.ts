import { api } from "./api";
import type { CropRecommendation, FertilizerRecommendation } from "../types/recommendation";

export const recommendationApi = {
  async crops(soilTestId?: number | string) {
    const { data } = await api.get<CropRecommendation[]>("/recommendations/crops", {
      params: soilTestId ? { soil_test_id: soilTestId } : undefined
    });
    return data;
  },
  async fertilizer(soilTestId?: number | string) {
    const { data } = await api.get<FertilizerRecommendation[]>("/recommendations/fertilizer", {
      params: soilTestId ? { soil_test_id: soilTestId } : undefined
    });
    return data;
  }
};
