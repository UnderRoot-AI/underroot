import { api } from "./api";

export const ocrApi = {
  async process(reportId: number | string) {
    const { data } = await api.post(`/ocr/${reportId}/process`);
    return data;
  }
};
