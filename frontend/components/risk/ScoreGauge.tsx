import { RISK_BANDS, STATUS_META } from "@/lib/risk";
import type { RiskStatus } from "@/lib/types/api";

/** 0–100 scale with three provisional bands and a marker at the score. */
export function ScoreGauge({ score, status }: { score: number; status: RiskStatus }) {
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div role="img" aria-label={`Score ${score} on a 0 to 100 scale, in the ${STATUS_META[status].label} band`} className="pt-2">
      <div className="relative">
        <div className="flex h-3 overflow-hidden rounded-pill">
          {RISK_BANDS.map((b) => (
            <div key={b.status} className={STATUS_META[b.status].bar} style={{ width: `${b.to - b.from}%` }} />
          ))}
        </div>
        <div className="absolute -top-1 h-5 w-1.5 -translate-x-1/2 rounded-pill bg-ink ring-2 ring-surface" style={{ left: `${pct}%` }} />
      </div>
      <div className="num relative mt-1 h-4 text-xs text-muted" aria-hidden="true">
        <span className="absolute left-0">0</span>
        <span className="absolute -translate-x-1/2" style={{ left: "40%" }}>40</span>
        <span className="absolute -translate-x-1/2" style={{ left: "70%" }}>70</span>
        <span className="absolute right-0">100</span>
      </div>
    </div>
  );
}
