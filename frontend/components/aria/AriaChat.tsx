"use client";
import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ToolResultCard } from "./ToolResultCard";
import { useAnalysisContext } from "@/components/dashboard/AnalysisProvider";
import { askAria } from "@/lib/api/aria";
import { ApiError } from "@/lib/api/errors";
import { USE_MOCK_API } from "@/lib/config";
import { SERVICE_COPY } from "@/lib/errorCopy";
import { ARIA_ERROR_PROMPT } from "@/lib/mock/mockAria";
import { fromRequest } from "@/lib/validation";
import type { AnalyzeResponse } from "@/lib/types/api";
import type { ChatMessage } from "@/lib/types/aria";

const GREETING: ChatMessage = {
  id: 0,
  role: "aria",
  text: "Hi, I'm ARIA. I explain the result the risk model gives for a transaction, and I can analyze one you describe. I can't change the score.\n\nTry: Analyze: amount 890, shopping_net, 03:15, 240 km",
};
const EXAMPLE = "Analyze: amount 890, shopping_net, 03:15, 240 km";
// Live ARIA does not receive the dashboard result, so result-based prompts are mock-only.
const PROMPTS = USE_MOCK_API
  ? [EXAMPLE, "Explain this result", "What does the score mean?", "Why was it flagged?", "Model limitations", ARIA_ERROR_PROMPT]
  : [EXAMPLE, "What can you help me with?"];
const INVALID_TEXT = `The risk service couldn't use those details, so nothing was analyzed. Please include the amount, merchant category and time, for example:\n${EXAMPLE}`;
const resultKey = (r: AnalyzeResponse) => `${r.request_id}|${r.risk_score}|${r.risk_status}|${r.model_factors.join(",")}`;

function Bubble({ m, onRetry, busy }: { m: ChatMessage; onRetry: () => void; busy: boolean }) {
  const user = m.role === "user";
  return (
    <div data-msg className={`flex gap-2 ${user ? "justify-end" : "justify-start"}`}>
      {!user && <span aria-hidden="true" className="mt-1 grid size-7 shrink-0 place-items-center rounded-full bg-primary text-xs font-semibold text-white">A</span>}
      <div
        className={`min-w-0 max-w-[85%] rounded-card px-3.5 py-2.5 text-sm ${
          user ? "rounded-br-sm bg-primary text-white" : m.error ? "rounded-tl-sm border border-danger/30 bg-danger-soft text-ink" : "rounded-tl-sm border border-line bg-surface text-ink shadow-card"
        }`}
      >
        <span className="sr-only">{user ? "You: " : "ARIA: "}</span>
        <p className="whitespace-pre-line [overflow-wrap:anywhere]">{m.text}</p>
        {m.toolResult && <ToolResultCard result={m.toolResult} />}
        {m.error && m.retryable !== false && (
          <Button variant="secondary" className="mt-2 min-h-11" onClick={onRetry} disabled={busy}>
            Try again
          </Button>
        )}
      </div>
    </div>
  );
}

export function AriaChat() {
  const { state, stale, show, setStale, setValues, setErrors, setActiveDemo, setOrigin } = useAnalysisContext();
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const busy = useRef(false);
  const nextId = useRef(1);
  const shown = useRef(new Set<string>());
  const log = useRef<HTMLDivElement>(null);
  const dashboardLoading = useRef(false);
  useEffect(() => {
    dashboardLoading.current = state.kind === "loading";
  }, [state.kind]);

  useEffect(() => {
    const el = log.current;
    if (!el) return;
    const items = [...el.querySelectorAll<HTMLElement>("[data-msg]")];
    const last = items[items.length - 1];
    const before = items[items.length - 2];
    let top = el.scrollHeight;
    // A new ARIA reply is read from the top. If the question above it also fits, show both.
    if (!sending && last && messages[messages.length - 1]?.role === "aria") {
      const replyTop = Math.max(0, last.offsetTop - 12);
      const pairTop = before ? Math.max(0, before.offsetTop - 12) : replyTop;
      top = last.offsetTop + last.offsetHeight - pairTop <= el.clientHeight ? pairTop : replyTop;
    }
    el.scrollTo({ top });
  }, [messages, sending]);

  async function send(text: string, retry = false) {
    const msg = text.trim();
    if (!msg || busy.current) return; // empty or already sending
    busy.current = true;
    setSending(true);
    if (!retry) setDraft("");
    setMessages((prev) => [...prev.filter((m) => !m.error), ...(retry ? [] : [{ id: nextId.current++, role: "user" as const, text: msg }])]);
    try {
      const ctx = { result: state.kind === "success" ? state.result : null, running: state.kind === "loading", stale };
      const { analyzedRequest, toolResult, text: replyText } = await askAria(msg, ctx);
      // Mock ARIA only syncs when it ran a new analysis; live ARIA's tool_result is always a fresh analysis.
      // If the dashboard is still analyzing, its own result wins the panel; the chat keeps its card.
      if (toolResult && !dashboardLoading.current && (USE_MOCK_API ? Boolean(analyzedRequest) : true)) {
        if (analyzedRequest) setValues(fromRequest(analyzedRequest)); // a live tool_result has no inputs, so the form is left alone
        setErrors({});
        setActiveDemo(null);
        setStale(false);
        setOrigin(analyzedRequest ? "form" : "chat");
        show({ kind: "success", result: toolResult });
      }
      let card = toolResult;
      let body = replyText;
      if (card) {
        const key = resultKey(card);
        if (shown.current.has(key)) {
          card = undefined; // never repeat the same result card
          body += "\n\nThis is the same result as the card above.";
        } else shown.current.add(key);
      }
      setMessages((prev) => [...prev, { id: nextId.current++, role: "aria", text: body, toolResult: card }]);
    } catch (e) {
      const invalid = e instanceof ApiError && e.code === "INVALID_INPUT";
      const reason = e instanceof ApiError && e.code !== "UNKNOWN" && !invalid ? `${SERVICE_COPY[e.code].title}. ` : "";
      const text = invalid ? INVALID_TEXT : `${reason}I couldn't answer just now, and nothing was analyzed. Your analysis result is unchanged. Please try again.`;
      setMessages((prev) => [...prev, { id: nextId.current++, role: "aria", error: true, retryable: !invalid, text }]);
    } finally {
      busy.current = false;
      setSending(false);
    }
  }

  const lastUser = [...messages].reverse().find((m) => m.role === "user");

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="info">{USE_MOCK_API ? "Preview" : "AI assistant"}</Badge>
        <p className="text-sm text-muted">ARIA explains the model&apos;s result. It does not calculate or change the score.</p>
      </div>
      <p className="mt-1 text-xs text-muted">
        {USE_MOCK_API
          ? "Preview: replies come from templates and transaction details are read by simple text matching. The real ARIA agent is not connected yet."
          : "ARIA's wording is AI-generated and may be imperfect. The risk result card comes from the risk model."}
      </p>

      <div ref={log} role="log" tabIndex={0} aria-label="Conversation with ARIA" aria-live="polite" className="relative mt-4 max-h-[26rem] min-h-40 space-y-3 overflow-y-auto rounded-control border border-line bg-sunken/60 p-3 sm:p-4">
        {messages.map((m) => (
          <Bubble key={m.id} m={m} busy={sending} onRetry={() => lastUser && send(lastUser.text, true)} />
        ))}
        {sending && (
          <p className="flex items-center gap-2 text-sm text-muted">
            <span aria-hidden="true" className="size-3.5 animate-spin rounded-full border-2 border-line-strong border-t-primary motion-reduce:animate-none" />
            ARIA is thinking…
          </p>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Suggested messages">
        {PROMPTS.map((p) => (
          <button key={p} type="button" disabled={sending} onClick={() => send(p)} className="min-h-11 rounded-pill border border-line-strong bg-surface px-3 text-left text-sm text-ink transition-colors hover:bg-sunken disabled:cursor-not-allowed disabled:text-muted">
            {p}
          </button>
        ))}
      </div>

      <form className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-end" onSubmit={(e) => { e.preventDefault(); void send(draft); }}>
        <label htmlFor="aria-input" className="sr-only">Message to ARIA</label>
        <textarea
          id="aria-input"
          rows={2}
          value={draft}
          maxLength={500}
          autoComplete="off"
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              void send(draft);
            }
          }}
          placeholder="Describe a transaction, or ask about the result"
          aria-describedby="aria-input-hint"
          className="min-h-11 flex-1 resize-none rounded-control border border-line-strong bg-surface px-3 py-2 text-sm placeholder:text-muted"
        />
        <Button type="submit" disabled={sending || !draft.trim()}>Send</Button>
      </form>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
        <p id="aria-input-hint">Enter to send, Shift+Enter for a new line. Don&apos;t type real card or account numbers. Nothing is saved.</p>
        <button type="button" className="min-h-11 rounded-control px-2 underline hover:text-ink" onClick={() => { setMessages([GREETING]); shown.current.clear(); }} disabled={sending}>Clear conversation</button>
      </div>
    </div>
  );
}
