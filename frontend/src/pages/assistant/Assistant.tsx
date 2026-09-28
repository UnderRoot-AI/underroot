import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { Bot, Send, Sparkles } from "lucide-react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import MessageBubble from "../../components/assistant/MessageBubble";
import { useAssistant } from "../../hooks/useAssistant";
import { useSoil } from "../../hooks/useSoil";
import { useT } from "../../i18n/useT";
import { useLanguageStore } from "../../store/languageStore";

const SUGGESTIONS: Record<string, string[]> = {
  en: [
    "What is a good pH for wheat?",
    "Which crop is best for my soil?",
    "How much Urea should I apply?",
    "How do I improve low nitrogen in my soil?",
  ],
  hi: [
    "गेहूं के लिए अच्छा pH क्या है?",
    "मेरी मिट्टी के लिए कौन सी फसल सबसे अच्छी है?",
    "मुझे कितना यूरिया डालना चाहिए?",
    "मिट्टी में नाइट्रोजन कम हो तो क्या करें?",
  ],
  gu: [
    "ઘઉં માટે સારો pH કેટલો?",
    "મારી જમીન માટે કઈ ફસલ સૌથી સારી?",
    "કેટલો યુરિયા નાખવો?",
    "જમીનમાં નાઇટ્રોજન ઓછું હોય તો શું કરવું?",
  ],
  mr: [
    "गहूसाठी चांगला pH किती असतो?",
    "माझ्या मातीसाठी कोणते पीक सर्वोत्तम आहे?",
    "किती युरिया टाकायला हवा?",
    "मातीत नायट्रोजन कमी असल्यास काय करावे?",
  ],
};

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

  const suggestions = SUGGESTIONS[language] ?? SUGGESTIONS.en;

  return (
    <>
      <PageHeader title={t("assistantTitle")} subtitle={t("assistantSubtitle")} />
      <Card className="assistant-card">
        <div className="assistant-head">
          <div className="assistant-bot"><Bot /></div>
          <div>
            <h2>{t("assistantTitle")}</h2>
            <span><span className="online-dot" /> {t("noData")}</span>
          </div>
        </div>
        <div className="suggestions">
          {suggestions.map(x => (
            <button key={x} onClick={() => setMessage(x)}><Sparkles size={14} />{x}</button>
          ))}
        </div>
        <div className="chat-window">
          {messages.map((m, i) => <MessageBubble key={m.id || i} message={m} />)}
          {loading && (
            <div className="message-row assistant">
              <div className="message-bubble typing">{t("thinking")}</div>
            </div>
          )}
          <div ref={bottom} />
        </div>
        <form className="chat-form" onSubmit={submit}>
          <input value={message} onChange={e => setMessage(e.target.value)} placeholder={t("typeMessage")} />
          <button disabled={loading}><Send size={18} /></button>
        </form>
      </Card>
    </>
  );
}
