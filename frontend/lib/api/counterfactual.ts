import type { Counterfactual, RiskStatus } from "@/lib/types/api";

const STATUSES: RiskStatus[] = ["low", "medium", "high"];
const num = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v); // 0 is a valid number
const text = (v: unknown): string | undefined => (typeof v === "string" && v.trim() ? v : undefined);

/**
 * Validates the optional counterfactual object. Returns undefined (nothing to show) when it is absent or incomplete.
 * Nothing is guessed: a "found" result without its values is dropped, never filled in.
 */
export function parseCounterfactual(raw: unknown): Counterfactual | undefined {
  if (typeof raw !== "object" || raw === null) return undefined;
  const r = raw as Record<string, unknown>;
  if (r.found === false) return { found: false };
  if (r.found !== true) return undefined;

  const changed_feature = text(r.changed_feature);
  const changed_feature_label = text(r.changed_feature_label);
  if ((!changed_feature && !changed_feature_label) || !num(r.original_value) || !num(r.suggested_value) || !num(r.new_risk_score)) return undefined;
  if (r.new_risk_score < 0 || r.new_risk_score > 100) return undefined;

  const status = typeof r.new_risk_status === "string" ? (r.new_risk_status.toLowerCase() as RiskStatus) : undefined;
  return {
    found: true,
    changed_feature,
    changed_feature_label,
    original_value: r.original_value,
    suggested_value: r.suggested_value,
    new_risk_score: r.new_risk_score,
    new_risk_status: status && STATUSES.includes(status) ? status : undefined,
    reason: text(r.reason),
  };
}
