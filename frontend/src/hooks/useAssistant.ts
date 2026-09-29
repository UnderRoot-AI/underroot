import { useState, useEffect } from "react";
import { assistantApi } from "../services/assistant.api";
import type { ChatMessage } from "../types/assistant";
import { getErrorMessage } from "../utils/errorHandler";

const WELCOME_EN = "Namaste! I'm your UnderRoot soil intelligence assistant. I can explain your soil test results, recommend crops and fertilizers, and answer general agricultural questions. What would you like to know?";

export function useAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: WELCOME_EN,
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyLoaded, setHistoryLoaded] = useState(false);

  // Load conversation history on mount
  useEffect(() => {
    if (historyLoaded) return;
    assistantApi.getHistory().then((history) => {
      if (history && history.length > 0) {
        setMessages(history.map((h, i) => ({
          id: h.id ?? i,
          role: h.role,
          content: h.content,
          created_at: h.created_at,
        })));
      }
      setHistoryLoaded(true);
    }).catch(() => {
      // History unavailable — keep welcome message
      setHistoryLoaded(true);
    });
  }, [historyLoaded]);

  const ask = async (message: string, soilTestId?: number | string) => {
    if (!message.trim()) return;
    const userMsg: ChatMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError("");
    try {
      const result = await assistantApi.ask(message, soilTestId);
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: result.answer,
        sources: result.sources,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      return result;
    } catch (e) {
      setError(getErrorMessage(e));
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I'm unable to reach the agricultural knowledge service right now. Your stored soil data is still available from the Soil Analysis page.",
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return { messages, loading, error, ask };
}
