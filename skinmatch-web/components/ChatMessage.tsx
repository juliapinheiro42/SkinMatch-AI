type ChatMessageProps = {
  role: "user" | "assistant";
  content: string;
};

export function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[82%] rounded-lg px-4 py-3 text-sm leading-6 shadow-soft ${
          isUser ? "bg-ink text-white" : "border border-ink/10 bg-white text-moss"
        }`}
      >
        <p className={isUser ? "text-white" : "text-ink"}>{isUser ? "Voce" : "SkinMatch AI"}</p>
        <p className="mt-1 whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
}
