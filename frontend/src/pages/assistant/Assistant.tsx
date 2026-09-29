import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { Bot, Send, Sparkles, Leaf } from "lucide-react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import MessageBubble from "../../components/assistant/MessageBubble";
import { useAssistant } from "../../hooks/useAssistant";
import { useSoil } from "../../hooks/useSoil";
import { useT } from "../../i18n/useT";
import { useLanguageStore } from "../../store/languageStore";

// ── Suggested prompts (context-unaware defaults; context-aware ones added below)
const BASE_SUGGESTIONS: Record<string, string[]> = {
  en: [
    "Explain my latest soil report",
    "What nutrients are low in my soil?",
    "What should I grow?",
    "How can I improve my soil?",
    "What does my pH mean?",
    "Explain my soil health score",
  ],
  hi: [
    "मेरी नवीनतम मिट्टी रिपोर्ट समझाएं",
    "मेरी मिट्टी में कौन से पोषक तत्व कम हैं?",
    "मुझे क्या उगाना चाहिए?",
    "मेरी मिट्टी कैसे सुधारें?",
    "pH का क्या मतलब है?",
  ],
  gu: [
    "મારો તાજો માટી અહેવાલ સમજાવો",
    "મારી માટીમાં કયા પોષક તત્ત્વો ઓછા છે?",
    "શું ઉગાડવું જોઈએ?",
    "માટી કેવી રીતે સુધારવી?",
    "pH નો અર્થ શો?",
  ],
  mr: [
    "माझा ताजा माती अहवाल सांगा",
    "माझ्या मातीत कोणते पोषक कमी आहेत?",
    "काय पिकवायला हवे?",
    "माती कशी सुधारायची?",
    "pH म्हणजे काय?",
  ],
};

function formatDate(dateStr?: string): string {
  if (!dateStr) return "";
  try {
    return new Date(dateStr).toLocaleDateString(undefined, {
      day: "numeric", month: "short", year: "numeric"
    });
  } catch {
    return dateStr;
  }
}

export default function Assistant() {
  const { messages, ask, loading } = useAssistant();
  const [message, setMessage] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  const { currentTest } = useSoil();
  const t = useT();
  const { language } = useLanguageStore();

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;
    const x = message;
    setMessage("");
    await ask(x, currentTest?.id);
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }

  async function sendSuggestion(suggestion: string) {
    setMessage("");
    await ask(suggestion, currentTest?.id);
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }

  const suggestions = BASE_SUGGESTIONS[language] ?? BASE_SUGGESTIONS.en;

  // Context-aware suggestions when soil test is available
  const contextSuggestions = currentTest
    ? suggestions
    : suggestions.filter((_, i) => i >= 3); // When no test, keep general questions

  return (
    <>
      <PageHeader title={t("assistantTitle")} subtitle={t("assistantSubtitle")} />

      {/* Context card */}
      <div className="assistant-context-card">
        <Leaf size={14} />
        {currentTest ? (
          <span>
            Using your latest soil test
            {currentTest.created_at && (
              <span className="context-date"> • {formatDate(currentTest.created_at.toString())}</span>
            )}
            {currentTest.health_status && (
              <span className={`context-status context-status-${currentTest.health_status.toLowerCase().replace(" ", "-")}`}>
                {" "}• {currentTest.health_status}
                {currentTest.health_score != null && ` (${Math.round(currentTest.health_score)}/100)`}
              </span>
            )}
          </span>
        ) : (
          <span className="context-no-data">No soil test available yet — run a soil test for personalised advice</span>
        )}
      </div>

      <Card className="assistant-card">
        <div className="assistant-head">
          <div className="assistant-bot"><Bot /></div>
          <div>
            <h2>{t("assistantTitle")}</h2>
            <span><span className="online-dot" /> UnderRoot Agricultural Intelligence</span>
          </div>
        </div>

        {/* Suggested prompts */}
        <div className="suggestions">
          {contextSuggestions.slice(0, 5).map(x => (
            <button key={x} onClick={() => sendSuggestion(x)} disabled={loading}>
              <Sparkles size={14} />{x}
            </button>
          ))}
        </div>

        {/* Chat window */}
        <div className="chat-window">
          {messages.map((m, i) => <MessageBubble key={m.id || i} message={m} />)}
          {loading && (
            <div className="message-row assistant">
              <div className="message-bubble typing">{t("thinking")}</div>
            </div>
          )}
          <div ref={bottom} />
        </div>

        {/* Input form */}
        <form className="chat-form" onSubmit={submit}>
          <input
            value={message}
            onChange={e => setMessage(e.target.value)}
            placeholder={t("typeMessage")}
            disabled={loading}
          />
          <button disabled={loading || !message.trim()}>
            <Send size={18} />
          </button>
        </form>
      </Card>
    </>
  );
}
