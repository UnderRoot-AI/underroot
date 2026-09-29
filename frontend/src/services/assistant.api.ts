import { api } from "./api";
import type { AssistantResponse, ChatMessage } from "../types/assistant";

export const assistantApi = {
  async ask(message: string, soilTestId?: number | string): Promise<AssistantResponse> {
    const { data } = await api.post<AssistantResponse>("/assistant/chat", {
      message,
      soil_test_id: soilTestId,
    });
    return data;
  },

  async getHistory(limit = 40): Promise<ChatMessage[]> {
    const { data } = await api.get<ChatMessage[]>(`/assistant/history?limit=${limit}`);
    return data;
  },
};
