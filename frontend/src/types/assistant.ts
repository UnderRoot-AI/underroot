export interface ChatMessage {
  id?: string | number;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  created_at?: string;
}

export interface AssistantResponse {
  answer: string;
  sources?: string[];
}
