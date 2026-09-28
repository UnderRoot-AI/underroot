import type { ChatMessage } from "../../types/assistant";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const lines = message.content.split("\n");
  return (
    <div className={`message-row ${message.role}`}>
      <div className="message-bubble">
        {lines.map((line, i) => (
          <span key={i}>
            {line}
            {i < lines.length - 1 && <br />}
          </span>
        ))}
      </div>
    </div>
  );
}
