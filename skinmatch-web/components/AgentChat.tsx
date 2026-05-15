"use client";

import { FormEvent, useState } from "react";
import { ChatMessage } from "@/components/ChatMessage";
import { ProductContextBox } from "@/components/ProductContextBox";
import { isRoutineResult, RoutineResultCard } from "@/components/RoutineResultCard";
import { ToolResultCard } from "@/components/ToolResultCard";
import { chatWithAgent } from "@/lib/api";
import type { AgentChatContext, AgentChatResponse } from "@/types/analysis";

const USER_ID = "00000000-0000-0000-0000-000000000001";

const quickPrompts = [
  "Esse produto e bom para mim?",
  "Me indique alternativas melhores",
  "Monte uma rotina simples",
  "Quais ingredientes minha pele nao tolera bem?",
];

type ChatItem =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string; response: AgentChatResponse };

const defaultContext: AgentChatContext = {
  main_goal: "acne",
  exclude_ingredients: [],
  skin_profile: {
    skin_type: "oily",
    sensitive_skin: true,
    acne_prone: true,
    barrier_compromised: false,
    known_triggers: [],
    tolerated_ingredients: [],
  },
};

export function AgentChat() {
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [input, setInput] = useState("");
  const [context, setContext] = useState<AgentChatContext>(defaultContext);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function sendMessage(message: string) {
    const cleanMessage = message.trim();
    if (!cleanMessage || loading) return;

    setError(null);
    setLoading(true);
    setInput("");
    setMessages((current) => [...current, { role: "user", content: cleanMessage }]);

    try {
      const response = await chatWithAgent({
        user_id: USER_ID,
        message: cleanMessage,
        context,
      });
      setMessages((current) => [...current, { role: "assistant", content: response.answer, response }]);
    } catch {
      setError("Nao foi possivel conversar com o agente. Verifique se o backend esta rodando.");
    } finally {
      setLoading(false);
    }
  }

function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendMessage(input);
  }

  function Metadata({ response }: { response: AgentChatResponse }) {
    return (
      <div className="flex flex-wrap gap-2 text-xs">
        {response.confidence ? (
          <span className="rounded-md bg-white px-2 py-1 font-medium text-moss">Confianca: {response.confidence}</span>
        ) : null}
        {response.tools_used.length ? (
          <span className="rounded-md bg-white px-2 py-1 font-medium text-moss">
            Tools: {response.tools_used.join(", ")}
          </span>
        ) : null}
        {response.context_status === "insufficient_history" ? (
          <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 font-medium text-amber-900">
            Dados insuficientes
          </span>
        ) : (
          <span className="rounded-md border border-sage/20 bg-white px-2 py-1 font-medium text-sage">
            Baseado no seu historico
          </span>
        )}
        {response.risk_level === "high" ? (
          <span className="rounded-md border border-rose-200 bg-rose-50 px-2 py-1 font-medium text-rose-800">
            Atencao: possivel reacao importante
          </span>
        ) : null}
      </div>
    );
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="grid min-h-[34rem] gap-4 rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-sage">Agente SkinMatch</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">Converse sobre produtos, rotina e historico</h1>
        </div>

        <div className="flex flex-wrap gap-2">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => sendMessage(prompt)}
              className="rounded-md border border-ink/10 px-3 py-2 text-sm font-medium text-moss transition hover:border-sage hover:text-ink"
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="grid max-h-[32rem] gap-4 overflow-y-auto rounded-md bg-linen/60 p-4">
          {messages.length ? (
            messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className="grid gap-3">
                <ChatMessage role={message.role} content={message.content} />
                {message.role === "assistant" ? (
                  <div className="grid gap-3">
                    <Metadata response={message.response} />
                    {message.response.missing_info?.length ? (
                      <section className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                        Falta: {message.response.missing_info.join(", ")}
                      </section>
                    ) : null}
                    {isRoutineResult(message.response.structured_result) ? (
                      <RoutineResultCard routine={message.response.structured_result} />
                    ) : (
                      <ToolResultCard
                        toolsUsed={message.response.tools_used}
                        structuredResult={message.response.structured_result}
                      />
                    )}
                    {message.response.follow_up_suggestion ? (
                      <button
                        type="button"
                        onClick={() => sendMessage(message.response.follow_up_suggestion ?? "")}
                        className="justify-self-start rounded-md border border-ink/10 bg-white px-3 py-2 text-sm font-medium text-moss transition hover:border-sage hover:text-ink"
                      >
                        {message.response.follow_up_suggestion}
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ))
          ) : (
            <div className="flex min-h-56 items-center justify-center text-center">
              <p className="max-w-sm text-sm leading-6 text-moss">
                Pergunte sobre uma formula, peca alternativas, gere uma rotina ou consulte os padroes do seu historico.
              </p>
            </div>
          )}
          {loading ? <p className="text-sm text-moss">Pensando com as ferramentas internas...</p> : null}
        </div>

        {error ? (
          <p className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>
        ) : null}

        <form className="flex gap-3" onSubmit={onSubmit}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            className="min-h-12 flex-1 rounded-md border border-ink/15 px-4 text-sm outline-none transition focus:border-sage"
            placeholder="Ex: Esse serum pode piorar minha acne?"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-md bg-ink px-5 text-sm font-semibold text-white transition hover:bg-moss disabled:cursor-not-allowed disabled:opacity-60"
          >
            Enviar
          </button>
        </form>
      </section>

      <ProductContextBox value={context} onChange={setContext} />
    </div>
  );
}
