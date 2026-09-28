import { api } from "./api";
import type { AssistantResponse } from "../types/assistant";

export const assistantApi = {
  async ask(message: string, soilTestId?: number | string) {
    const { data } = await api.post<AssistantResponse>("/assistant/chat", {
      message,
      soil_test_id: soilTestId
    });
    return data;
  }
};
