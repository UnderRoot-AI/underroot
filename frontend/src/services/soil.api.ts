import { api } from "./api";
import type { SoilTest, SoilTestPayload } from "../types/soil";
export const soilApi = {
  async create(payload: SoilTestPayload) { const { data } = await api.post<SoilTest>("/soil/tests", payload); return data; },
  async list() { const { data } = await api.get<SoilTest[]>("/soil/tests"); return data; },
  async get(id: number | string) { const { data } = await api.get<SoilTest>(`/soil/tests/${id}`); return data; },
  async analyze(id: number | string) { const { data } = await api.get(`/soil/tests/${id}/analysis`); return data; },
};
