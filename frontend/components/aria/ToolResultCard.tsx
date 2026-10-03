import { Badge } from "@/components/ui/Badge";
import { SourceBadge } from "@/components/risk/SourceBadge";
import { STATUS_META } from "@/lib/risk";
import type { AnalyzeResponse } from "@/lib/types/api";

/** The structured risk-model result an ARIA reply is based on. The model result is the source of truth. */
export function ToolResultCard({ result }: { result: AnalyzeResponse }) {
  const meta = STATUS_META[result.risk_status];
  return (
    <div role="group" aria-label="Risk model result" className="mt-3 rounded-control border border-line bg-sunken/60 p-3 text-sm">
      <p className="text-xs font-medium text-muted">Risk model result</p>
      <div className="mt-1.5 flex flex-wrap items-center gap-2">
        <Badge tone={meta.tone}><span aria-hidden="true">{meta.icon}</span>{meta.label}</Badge>
        <Badge tone={result.is_fraud ? "danger" : "neutral"}>{result.is_fraud ? "Flagged" : "Not flagged"}</Badge>
        <SourceBadge result={result} />
      </div>
      <p className="num mt-2 text-2xl font-semibold text-ink">
        {result.risk_score}
        <span className="ml-1 text-sm font-normal text-muted">/ 100</span>
      </p>
      <p className="text-xs text-muted">Relative risk score, not a probability.</p>
      <p className="num mt-1 text-xs text-muted [overflow-wrap:anywhere]">Model {result.model_version}</p>
      {result.model_factors.length > 0 && (
        <ul className="mt-2 space-y-1 border-t border-line pt-2">
          {result.model_factors.map((f, i) => (
            <li key={`${i}-${f}`} className="flex gap-2 text-ink"><span aria-hidden="true" className="text-danger">▲</span><span className="min-w-0 [overflow-wrap:anywhere]">{f}</span></li>
          ))}
        </ul>
      )}
      {result.explanation && <p className="mt-2 border-t border-line pt-2 text-ink [overflow-wrap:anywhere]">{result.explanation}</p>}
      <p className="num mt-2 text-xs text-muted [overflow-wrap:anywhere]">Request ID: {result.request_id}</p>
    </div>
  );
}
