import { USE_MOCK_API } from "@/lib/config";
import { cachedDemoFor, mockAnalyze } from "@/lib/mock/mockAnalyze";
import type { AnalyzeRequest, AnalyzeResponse, RiskStatus } from "@/lib/types/api";
import { parseCounterfactual } from "./counterfactual";
import { ApiError, toApiError } from "./errors";

const CLIENT_TIMEOUT_MS = 40_000; // the proxy gives up at 30 s, so this only covers a dead app server
const STATUSES: RiskStatus[] = ["low", "medium", "high"];
const malformed = (field: string) => new ApiError("UNKNOWN", `The backend returned an unexpected result (${field}).`);

/**
 * Guards the UI against a malformed payload. Required fields must be present and valid, otherwise a controlled
 * error is shown. Nothing is guessed or derived: a missing status or flag is an error, not a default.
 * model_factors may be missing/null and is treated as "no factors".
 */
export function normalize(raw: Partial<AnalyzeResponse>): AnalyzeResponse {
  const { risk_score, risk_status, is_fraud, request_id, model_version } = raw;
  if (typeof risk_score !== "number" || !Number.isFinite(risk_score) || risk_score < 0 || risk_score > 100) throw malformed("risk_score");
  const status = typeof risk_status === "string" ? (risk_status.toLowerCase() as RiskStatus) : undefined;
  if (!status || !STATUSES.includes(status)) throw malformed("risk_status");
  if (typeof is_fraud !== "boolean") throw malformed("is_fraud");
  if (typeof request_id !== "string" || typeof model_version !== "string") throw malformed("request_id or model_version");
  return {
    ...raw,
    request_id,
    is_fraud,
    risk_score,
    risk_status: status,
    model_factors: Array.isArray(raw.model_factors) ? raw.model_factors.map(String) : [],
    model_version,
    // Optional fields are kept only if they have the confirmed type. An unknown source_mode is dropped, never shown as LIVE.
    source_mode: raw.source_mode === "LIVE" || raw.source_mode === "CACHED" ? raw.source_mode : undefined,
    score_type: typeof raw.score_type === "string" ? raw.score_type : undefined,
    explanation: typeof raw.explanation === "string" ? raw.explanation : undefined,
    counterfactual: parseCounterfactual(raw.counterfactual),
  };
}

/**
 * Single entry point the UI calls.
 * - Mock mode: lib/mock.
 * - Live mode: POST /api/analyze (server proxy that adds the JWT). A failed live call is an error, never a mock result.
 *   The one exception is a predefined CACHED demo input picked on purpose by the user; it is shown as CACHED DEMO.
 */
export async function analyzeTransaction(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  if (USE_MOCK_API) return mockAnalyze(req);
  const saved = cachedDemoFor(req);
  if (saved) return saved;

  let res: Response;
  try {
    res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: AbortSignal.timeout(CLIENT_TIMEOUT_MS),
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "TimeoutError") throw new ApiError("ML_NODE_TIMEOUT", "The request timed out.");
    throw new ApiError("NETWORK_ERROR", "Could not reach the app server.");
  }
  if (!res.ok) throw await toApiError(res);

  let body: Partial<AnalyzeResponse>;
  try {
    body = (await res.json()) as Partial<AnalyzeResponse>;
  } catch {
    throw new ApiError("UNKNOWN", "The backend returned a response that is not valid JSON.");
  }
  return normalize(body);
}
