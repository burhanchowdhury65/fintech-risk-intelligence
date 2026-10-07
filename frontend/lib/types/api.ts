/**
 * API types for the Fintech Risk Intelligence frontend.
 *
 * SOURCE: Person A "Frontend API Contract Confirmation" (docs/api-contract.md on
 * branch person-a-backend). Fields are grouped by confirmation status so nothing
 * unconfirmed is mistaken for final. Do NOT add fields here without Person A.
 */

/* ---------- CONFIRMED: POST /analyze request ---------- */
export interface AnalyzeRequest {
  transaction_amount: number;
  transaction_type: string;
  merchant_category: string;
  /** ISO datetime string, e.g. "2026-09-26T14:30:00" */
  transaction_time: string;
  distance_from_home?: number | null;
  /** Shape (object | string | null) is confirmed as flexible, not detailed. */
  location?: Record<string, unknown> | string | null;
  // simulate_timeout / simulate_unavailable are internal test fields: never expose in UI.
}

/* ---------- CONFIRMED: POST /analyze response ---------- */
/** Current implementation; thresholds 0-39 / 40-69 / 70-100 are PROVISIONAL. */
export type RiskStatus = "low" | "medium" | "high";

/** Confirmed by Person B: a flat array of plain-text, rule-based hints. [] when not flagged. */
export type ModelFactor = string;

/** Optional and NOT yet verified by backend. Never assume it is returned. */
export interface CounterfactualFound {
  found: true;
  /** At least one of changed_feature / changed_feature_label is present (checked before use). */
  changed_feature?: string;
  changed_feature_label?: string;
  original_value: number;
  suggested_value: number;
  new_risk_score: number;
  new_risk_status?: RiskStatus;
  reason?: string;
}
/** A search that found nothing returns only { found: false }. */
export interface CounterfactualNotFound {
  found: false;
}
export type Counterfactual = CounterfactualFound | CounterfactualNotFound;

export interface AnalyzeResponse {
  request_id: string;
  is_fraud: boolean;
  /** 0-100 relative risk score. NOT a probability, NOT a percentage. */
  risk_score: number;
  risk_status: RiskStatus;
  model_factors: ModelFactor[];
  /** Verified value today: "histgb-candidate-day3-v1"; may change. */
  model_version: string;
  counterfactual?: Counterfactual;

  /* TBD by Person A: in the roadmap's minimum contract but NOT returned yet.
     Kept optional so the UI renders correctly whether or not they arrive. */
  score_type?: string;
  explanation?: string;
  source_mode?: "LIVE" | "CACHED";
}

/* ---------- CONFIRMED: error codes ----------
   400 INVALID_INPUT (negative amount, from backend)
   422 INVALID_INPUT (negative distance, ML node rejected input; structured, not Pydantic array)
   503 ML_NODE_UNAVAILABLE, 504 ML_NODE_TIMEOUT. Final envelope for other errors still TBD. */
export type ApiErrorCode = "INVALID_INPUT" | "ML_NODE_UNAVAILABLE" | "ML_NODE_TIMEOUT";
/** Adds frontend-only codes: the browser could not reach the app/backend, or the error was not recognised. */
export type ServiceErrorCode = ApiErrorCode | "NETWORK_ERROR" | "UNKNOWN";

export interface ApiErrorBody {
  detail: {
    error_code: ApiErrorCode;
    message: string;
    request_id?: string;
  };
}

/* ---------- CONFIRMED: GET /health ---------- */
export interface HealthResponse {
  status: string;
  service: string;
}

/* ---------- Frontend-only UI state (not part of the API contract) ---------- */
export type FieldName =
  | "transaction_amount"
  | "transaction_time"
  | "transaction_type"
  | "merchant_category"
  | "distance_from_home"
  | "customer_latitude"
  | "customer_longitude"
  | "merchant_latitude"
  | "merchant_longitude";

export type FieldErrors = Partial<Record<FieldName, string>>;

/** Cached demo is a `success` whose result has source_mode "CACHED". */
export type AnalysisViewState =
  | { kind: "empty" }
  | { kind: "loading" }
  | { kind: "success"; result: AnalyzeResponse }
  | { kind: "validation-error"; message: string; fieldErrors?: FieldErrors; requestId?: string }
  | { kind: "service-error"; code: ServiceErrorCode; message: string; requestId?: string };

/*
 * NOT DEFINED YET (do not create types): POST /aria/chat, POST /auth/login,
 * GET /health/dependencies, GET /analysis/{request_id}, demo transaction list.
 * Auth is Bearer JWT: `Authorization: Bearer <token>`.
 */
