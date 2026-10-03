import type { ApiErrorBody, ServiceErrorCode } from "@/lib/types/api";

const KNOWN: ServiceErrorCode[] = ["INVALID_INPUT", "ML_NODE_UNAVAILABLE", "ML_NODE_TIMEOUT", "NETWORK_ERROR"];

export class ApiError extends Error {
  constructor(
    public code: ServiceErrorCode,
    message: string,
    public requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Builds an ApiError from a failed fetch Response (used by the real API call on Day 3). */
export async function toApiError(res: Response): Promise<ApiError> {
  try {
    const d = ((await res.json()) as Partial<ApiErrorBody>).detail;
    if (d && !Array.isArray(d) && typeof d.error_code === "string") {
      const code = KNOWN.find((k) => k === d.error_code);
      return new ApiError(code ?? "UNKNOWN", d.message ?? "The request failed.", d.request_id);
    }
  } catch {
    /* body was not JSON */
  }
  if (res.status === 401 || res.status === 403) {
    return new ApiError("UNKNOWN", `The backend rejected the token (HTTP ${res.status}). Generate a new DEV_JWT; tokens expire after 60 minutes.`);
  }
  return new ApiError("UNKNOWN", `The request failed (HTTP ${res.status}).`);
}
