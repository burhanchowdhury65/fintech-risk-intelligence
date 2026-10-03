import type { BadgeTone } from "@/components/ui/Badge";
import type { RiskStatus } from "@/lib/types/api";

/** Thresholds are PROVISIONAL (Person A). Used for display bands and mock data only. */
export const RISK_BANDS: { status: RiskStatus; from: number; to: number }[] = [
  { status: "low", from: 0, to: 40 },
  { status: "medium", from: 40, to: 70 },
  { status: "high", from: 70, to: 100 },
];

export function statusFromScore(score: number): RiskStatus {
  return score >= 70 ? "high" : score >= 40 ? "medium" : "low";
}

export const STATUS_META: Record<RiskStatus, { label: string; tone: BadgeTone; icon: string; bar: string; panel: string; text: string }> = {
  low: { label: "Low risk", tone: "success", icon: "✓", bar: "bg-success/45", panel: "border-success/30 bg-success-soft", text: "text-success" },
  medium: { label: "Medium risk", tone: "warning", icon: "!", bar: "bg-warning/45", panel: "border-warning/30 bg-warning-soft", text: "text-warning" },
  high: { label: "High risk", tone: "danger", icon: "▲", bar: "bg-danger/45", panel: "border-danger/40 bg-danger-soft", text: "text-danger" },
};
