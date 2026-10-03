import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { USE_MOCK_API } from "@/lib/config";
import { STATUS_META } from "@/lib/risk";
import type { AnalyzeResponse } from "@/lib/types/api";

const fmt = (n: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(n);
const humanize = (name: string) => name.replace(/_/g, " ");
const numbersIn = (t: string) => (t.match(/\d[\d,]*(?:\.\d+)?/g) ?? []).map((n) => Number(n.replace(/,/g, "")));

/**
 * "What would change this result?" Shown only when the backend returned counterfactual.found === true for THIS result.
 * Every number comes from the response. The original score is the result's own risk_score.
 */
export function CounterfactualBox({ result }: { result: AnalyzeResponse }) {
  const cf = result.counterfactual;
  if (!cf || cf.found !== true) return null; // not found or absent: render nothing

  const label = cf.changed_feature_label ?? humanize(cf.changed_feature ?? "this feature");
  const band = cf.new_risk_status ? STATUS_META[cf.new_risk_status].label : null;
  // The backend's reason may just repeat the sentence above. Show it only if it adds something.
  const found = cf.reason ? numbersIn(cf.reason) : [];
  const reason = cf.reason && !(found.includes(cf.original_value) && found.includes(cf.suggested_value)) ? cf.reason : null;

  return (
    <Card headingId="counterfactual-title" title="What Would Change This Result?" className="mt-6">
      <p className="max-w-prose text-base text-ink [overflow-wrap:anywhere]">
        If {label} had been <strong className="num font-semibold">{fmt(cf.suggested_value)}</strong> instead of{" "}
        <strong className="num font-semibold">{fmt(cf.original_value)}</strong>, the risk score would have been{" "}
        <strong className="num font-semibold">{fmt(cf.new_risk_score)}</strong> instead of{" "}
        <strong className="num font-semibold">{fmt(result.risk_score)}</strong>.
      </p>
      {(band || USE_MOCK_API) && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {band && cf.new_risk_status && <Badge tone={STATUS_META[cf.new_risk_status].tone}>With that change: {band.toLowerCase()}</Badge>}
          {USE_MOCK_API && <Badge tone="info">Sample data</Badge>}
        </div>
      )}
      {reason && <p className="mt-3 max-w-prose text-sm text-muted [overflow-wrap:anywhere]">{reason}</p>}
      <p className="mt-3 max-w-prose text-xs text-muted">
        This is an illustrative single-feature suggestion based on the model&apos;s tested candidate values. It is not a guarantee that changing a real transaction will prevent fraud.
      </p>
    </Card>
  );
}
