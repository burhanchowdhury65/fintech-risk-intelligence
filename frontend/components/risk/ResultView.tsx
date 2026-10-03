import { Badge } from "@/components/ui/Badge";
import { ScoreGauge } from "./ScoreGauge";
import { RISK_BANDS, STATUS_META } from "@/lib/risk";
import { LIMITATIONS_TEXT } from "@/lib/copy";
import { SourceBadge } from "./SourceBadge";
import type { AnalyzeResponse } from "@/lib/types/api";

const note = "rounded-control border border-warning/30 bg-warning-soft p-3 text-sm text-warning";

export function ResultView({ result, stale, fromChat }: { result: AnalyzeResponse; stale: boolean; fromChat: boolean }) {
  const meta = STATUS_META[result.risk_status];
  const cached = result.source_mode === "CACHED";

  return (
    <div className="space-y-5">
      {stale && <p role="note" className={note}>The inputs have changed since this result. Analyze again to get a result for the new inputs.</p>}

      {fromChat && !stale && (
        <p role="note" className="rounded-control border border-info/30 bg-info-soft p-3 text-sm text-info">
          This result came from your ARIA chat message. The form may not show the same transaction.
        </p>
      )}

      {/* Verdict: the first thing to read. Colour + icon + words, never colour alone. */}
      <div className={`flex items-start gap-3 rounded-card border p-4 ${meta.panel}`}>
        <span aria-hidden="true" className={`grid size-10 shrink-0 place-items-center rounded-full bg-surface text-lg font-semibold ${meta.text}`}>{meta.icon}</span>
        <div className="min-w-0">
          <h3 className="text-lg font-semibold text-ink">{result.is_fraud ? "Flagged by model" : "Not flagged by model"}</h3>
          <p className={`text-sm font-medium ${meta.text}`}>{meta.label}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <SourceBadge result={result} />
            <Badge tone="info">Demo / synthetic data</Badge>
          </div>
        </div>
      </div>

      {cached && <p role="note" className={note}>This is a saved demo result for one fixed demo input. It was not calculated just now.</p>}

      <div className="rounded-card border border-line bg-sunken/50 p-4 sm:p-5">
        <h3 className="text-sm font-medium text-muted">Risk score</h3>
        <p className="num mt-1 text-5xl font-semibold text-ink sm:text-6xl">
          {result.risk_score}
          <span className="ml-2 text-xl font-normal text-muted">/ 100</span>
        </p>
        <ScoreGauge score={result.risk_score} status={result.risk_status} />
        <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink" aria-label="What the score bands mean (provisional)">
          {RISK_BANDS.map((b) => (
            <li key={b.status} className="flex items-center gap-1.5">
              <span aria-hidden="true" className={`size-2.5 rounded-sm ${STATUS_META[b.status].bar}`} />
              <span className="num">{b.from}–{b.to === 100 ? 100 : b.to - 1}</span> {STATUS_META[b.status].label.replace(" risk", "")}
            </li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-muted">A 0 to 100 relative risk score, not a probability or a percentage. Band limits are provisional.</p>
      </div>

      <dl>
        <dt className="text-xs text-muted">Model version</dt>
        <dd className="num mt-0.5 text-sm font-medium text-ink [overflow-wrap:anywhere]">{result.model_version}</dd>
      </dl>

      <section aria-labelledby="factors-title">
        <h3 id="factors-title" className="text-sm font-medium text-ink">Model factors</h3>
        <p className="mt-0.5 text-xs text-muted">Simple rule-based hints from the model, not a formal interpretability method.</p>
        {result.model_factors.length === 0 ? (
          <p className="mt-2 text-sm text-muted">No risk factors were reported for this result.</p>
        ) : (
          <ul className="mt-2 divide-y divide-line rounded-control border border-line">
            {result.model_factors.map((f, i) => (
              <li key={`${i}-${f}`} className="flex items-start gap-2 p-3 text-sm text-ink">
                <span aria-hidden="true" className="mt-0.5 text-danger">▲</span>
                <span className="min-w-0 [overflow-wrap:anywhere]">{f}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {result.explanation && (
        <section aria-labelledby="explanation-title">
          <h3 id="explanation-title" className="text-sm font-medium text-ink">Explanation</h3>
          <p className="mt-1 max-w-prose text-sm text-ink [overflow-wrap:anywhere]">{result.explanation}</p>
        </section>
      )}

      <section aria-labelledby="limits-title" className="rounded-control border border-line p-3">
        <h3 id="limits-title" className="text-sm font-medium text-ink">Model limitations</h3>
        <p className="mt-1 text-sm text-muted">{LIMITATIONS_TEXT}</p>
      </section>

      <details className="text-sm">
        <summary className="min-h-11 cursor-pointer py-2 text-muted hover:text-ink">Technical details</summary>
        <dl className="grid gap-2 pb-1 sm:grid-cols-2">
          <div>
            <dt className="text-xs text-muted">Request ID</dt>
            <dd className="num text-ink [overflow-wrap:anywhere]">{result.request_id}</dd>
          </div>
          {result.score_type && (
            <div>
              <dt className="text-xs text-muted">Score type</dt>
              <dd className="num text-ink [overflow-wrap:anywhere]">{result.score_type}</dd>
            </div>
          )}
        </dl>
      </details>
    </div>
  );
}
