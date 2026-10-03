import { Badge } from "@/components/ui/Badge";
import { ResultView } from "./ResultView";
import { SERVICE_COPY } from "@/lib/errorCopy";
import type { AnalysisViewState } from "@/lib/types/api";

function Message({ tone, title, children, alert }: { tone: "neutral" | "danger" | "warning"; title: string; children: React.ReactNode; alert?: boolean }) {
  const box = { neutral: "border-dashed border-line", danger: "border-danger/30 bg-danger-soft", warning: "border-warning/30 bg-warning-soft" }[tone];
  return (
    <div role={alert ? "alert" : undefined} className={`rounded-card border p-5 ${box}`}>
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      <div className="mt-2 max-w-prose space-y-2 text-sm text-ink [overflow-wrap:anywhere]">{children}</div>
    </div>
  );
}

function Skeleton() {
  const bar = "rounded-control bg-sunken motion-safe:animate-pulse";
  return (
    <div aria-hidden="true" className="space-y-5">
      <div className="flex gap-2"><div className={`${bar} h-6 w-28`} /><div className={`${bar} h-6 w-24`} /></div>
      <div className={`${bar} h-40`} />
      <div className="grid grid-cols-3 gap-4"><div className={`${bar} h-10`} /><div className={`${bar} h-10`} /><div className={`${bar} h-10`} /></div>
      <div className={`${bar} h-24`} />
    </div>
  );
}

export function ResultPanel({ state, stale, fromChat }: { state: AnalysisViewState; stale: boolean; fromChat: boolean }) {
  switch (state.kind) {
    case "loading":
      return (
        <div className="min-h-[28rem]">
          <p className="mb-4 flex items-center gap-2 text-sm font-medium text-ink"><span aria-hidden="true" className="size-4 animate-spin rounded-full border-2 border-line-strong border-t-primary motion-reduce:animate-none" />Analyzing transaction…</p>
          <Skeleton />
        </div>
      );
    case "success":
      return <ResultView result={state.result} stale={stale} fromChat={fromChat} />;
    case "validation-error":
      return (
        <Message tone="danger" title="Some fields need attention" alert>
          {state.fieldErrors ? (
            <ul className="list-disc space-y-1 pl-5">{Object.entries(state.fieldErrors).map(([k, v]) => <li key={k}>{v}</li>)}</ul>
          ) : (
            <p>{state.message}</p>
          )}
          <p className="text-muted">
            {state.fieldErrors ? "Correct the highlighted fields" : "Check the values you entered"}, then select Analyze again. No result was produced.
            {state.requestId ? ` Reference: ${state.requestId}.` : ""}
          </p>
        </Message>
      );
    case "service-error": {
      const copy = SERVICE_COPY[state.code];
      return (
        <Message tone="warning" title={copy.title} alert>
          <p>{copy.help}</p>
          {process.env.NODE_ENV === "development" && state.code === "UNKNOWN" && <p className="text-muted">Details: {state.message}</p>}
          <p className="text-muted">No result was produced, and the previous result is not shown.{state.requestId ? ` Reference: ${state.requestId}.` : ""}</p>
        </Message>
      );
    }
    default:
      return (
        <Message tone="neutral" title="No analysis yet">
          <p>Fill in the transaction details, or pick a demo input, then select Analyze. The result will appear here:</p>
          <ul className="flex flex-wrap gap-2 pt-1">
            {["Risk score", "Risk status", "Model version", "Model factors", "Explanation"].map((t) => <li key={t}><Badge>{t}</Badge></li>)}
          </ul>
        </Message>
      );
  }
}
