"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Bot, User, Sparkles, BookText, Wrench } from "lucide-react";
import { copilotAsk } from "@/lib/api";
import type { AOI, CopilotResponse, LayerResponse } from "@/lib/types";
import { COPILOT_EXAMPLES } from "@/lib/presets";
import { SourceBadge, Spinner } from "@/components/ui";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  response?: CopilotResponse;
}

export function CopilotPanel({
  aoi,
  onLayer,
}: {
  aoi: AOI;
  onLayer: (layer: LayerResponse) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || loading) return;
    setError(null);
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await copilotAsk({ question: q, aoi });
      setMessages((m) => [
        ...m,
        { role: "assistant", text: res.answer, response: res },
      ]);
      if (res.layers?.[0]) onLayer(res.layers[0]);
    } catch (e: any) {
      setError(e?.detail || e?.message || "GeoCopilot request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* header */}
      <div className="flex items-center gap-2.5 border-b border-line px-4 py-3.5">
        <div className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient text-space-950">
          <Bot size={17} />
        </div>
        <div>
          <div className="text-sm font-semibold text-white">GeoCopilot</div>
          <div className="text-[11px] text-slate-500">
            Grounded climate-risk agent
          </div>
        </div>
      </div>

      {/* messages */}
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.length === 0 && !loading && (
          <div className="pt-2">
            <div className="mb-3 flex items-center gap-2 text-sm text-slate-400">
              <Sparkles size={14} className="text-brand-cyan" />
              Ask anything about climate risk over your AOI.
            </div>
            <div className="space-y-2">
              {COPILOT_EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => send(ex)}
                  className="block w-full rounded-xl border border-line bg-space-850 px-3.5 py-2.5 text-left text-xs leading-relaxed text-slate-300 transition-all hover:border-brand-cyan/40 hover:text-white"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end gap-2">
              <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-brand-gradient px-3.5 py-2.5 text-sm font-medium text-space-950">
                {m.text}
              </div>
              <div className="mt-1 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-line bg-space-800 text-slate-400">
                <User size={13} />
              </div>
            </div>
          ) : (
            <div key={i} className="flex gap-2">
              <div className="mt-1 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-space-950">
                <Bot size={13} />
              </div>
              <div className="max-w-[88%] space-y-2.5">
                <div className="rounded-2xl rounded-tl-sm border border-line bg-space-850 px-3.5 py-2.5 text-sm leading-relaxed text-slate-200">
                  {m.text}
                </div>
                {m.response && <AssistantMeta res={m.response} />}
              </div>
            </div>
          ),
        )}

        {loading && (
          <div className="flex gap-2">
            <div className="mt-1 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-space-950">
              <Bot size={13} />
            </div>
            <div className="rounded-2xl rounded-tl-sm border border-line bg-space-850 px-4">
              <Spinner label="Routing & computing…" />
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-200">
            {error}
          </div>
        )}
      </div>

      {/* input */}
      <div className="border-t border-line p-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="flex items-center gap-2 rounded-xl border border-line bg-space-850 p-1.5 focus-within:border-brand-cyan/50"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask GeoCopilot…"
            className="flex-1 bg-transparent px-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient text-space-950 transition hover:brightness-110 disabled:opacity-40"
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  );
}

function AssistantMeta({ res }: { res: CopilotResponse }) {
  return (
    <div className="space-y-2 pl-0.5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1 rounded-full border border-line bg-space-800 px-2 py-0.5 text-[10px] text-slate-400">
          <Wrench size={10} /> {res.tool}
        </span>
        <SourceBadge source={res.source} />
        {res.llm_used && (
          <span className="inline-flex items-center gap-1 rounded-full border border-violet-400/30 bg-violet-500/10 px-2 py-0.5 text-[10px] text-violet-300">
            <Sparkles size={10} /> LLM
          </span>
        )}
      </div>
      {res.note && (
        <p className="text-[11px] italic text-amber-300/80">{res.note}</p>
      )}
      {res.citations?.length > 0 && (
        <details className="group">
          <summary className="flex cursor-pointer list-none items-center gap-1.5 text-[11px] text-slate-500 transition hover:text-slate-300">
            <BookText size={11} />
            {res.citations.length} citation
            {res.citations.length > 1 ? "s" : ""}
          </summary>
          <ul className="mt-1.5 space-y-1 border-l border-line pl-3">
            {res.citations.map((c, i) => (
              <li key={i} className="text-[11px] leading-relaxed text-slate-500">
                {c}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
