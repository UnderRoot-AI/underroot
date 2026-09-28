import { useState } from "react";
import { assistantApi } from "../services/assistant.api";
import type { ChatMessage } from "../types/assistant";
import { getErrorMessage } from "../utils/errorHandler";

export function useAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hello! I can help you understand your soil report, crops, fertilizer, irrigation, and soil health."
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const ask = async (message: string, soilTestId?: number | string) => {
    if (!message.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setLoading(true);
    setError("");
    try {
      const result = await assistantApi.ask(message, soilTestId);
      setMessages((prev) => [...prev, { role: "assistant", content: result.answer }]);
      return result;
    } catch (e) {
      setError(getErrorMessage(e));
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "I could not reach the assistant service right now." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return { messages, loading, error, ask };
}
