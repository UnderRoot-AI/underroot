import type { ChatMessage } from "../../types/assistant";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const lines = message.content.split("\n");
  const hasSources = message.role === "assistant" && message.sources && message.sources.length > 0;

  return (
    <div className={`message-row ${message.role}`}>
      <div className="message-bubble">
        {lines.map((line, i) => {
          // Render lines starting with ✅ ⚠️ 💡 as styled list items
          const isEmoji = /^[✅⚠️💡•]/.test(line.trim());
          return (
            <span key={i} className={isEmoji ? "bubble-line-hint" : undefined}>
              {line}
              {i < lines.length - 1 && <br />}
            </span>
          );
        })}
        {hasSources && (
          <div className="message-sources">
            {message.sources!.map((src, i) => (
              <span key={i} className="source-chip">{src.replace(".txt", "")}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
