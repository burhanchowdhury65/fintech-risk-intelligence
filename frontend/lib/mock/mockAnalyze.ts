import { statusFromScore } from "@/lib/risk";
import type { AnalyzeRequest, AnalyzeResponse } from "@/lib/types/api";
import { ApiError } from "@/lib/api/errors";
import { DEMO_SCENARIOS } from "./scenarios";

const MOCK_DELAY_MS = 900;
let customCount = 0;

const signature = (i: AnalyzeRequest) =>
  [i.transaction_amount, i.transaction_type, i.merchant_category, i.transaction_time, i.distance_from_home ?? ""].join("|");

/** Rough rules for inputs that are not a demo. Clearly labelled mock; NOT the model. */
function estimate(i: AnalyzeRequest): AnalyzeResponse {
  const hour = Number(i.transaction_time.slice(11, 13));
  const factors: string[] = [];
  let score = 0;
  if (i.transaction_amount >= 500) { score += 35; factors.push("Transaction amount is unusually high"); }
  if ((i.distance_from_home ?? 0) >= 100) { score += 30; factors.push("Transaction location is far from customer's home"); }
  if (hour < 5) { score += 25; factors.push("Transaction occurred at an unusual hour"); }
  return {
    request_id: `MOCK-REQ-CUSTOM-${++customCount}`, is_fraud: score >= 70, risk_score: score, risk_status: statusFromScore(score),
    model_factors: factors, model_version: "mock-model-v0",
  };
}

export async function mockAnalyze(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  await new Promise((r) => setTimeout(r, MOCK_DELAY_MS));
  const hit = DEMO_SCENARIOS.find((s) => s.outcome && signature(s.input) === signature(req));
  if (hit?.outcome?.kind === "error") throw new ApiError(hit.outcome.code, hit.outcome.message, hit.outcome.requestId);
  if (hit?.outcome?.kind === "response") return hit.outcome.response; // CACHED only ever comes from an exact match
  return estimate(req);
}

/** Saved demo result for an EXACT match of a predefined cached demo input; null for anything else. */
export function cachedDemoFor(req: AnalyzeRequest): AnalyzeResponse | null {
  const hit = DEMO_SCENARIOS.find(
    (s) => s.outcome?.kind === "response" && s.outcome.response.source_mode === "CACHED" && signature(s.input) === signature(req),
  );
  return hit?.outcome?.kind === "response" ? hit.outcome.response : null;
}
