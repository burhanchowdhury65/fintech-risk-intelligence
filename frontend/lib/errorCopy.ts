import type { ServiceErrorCode } from "@/lib/types/api";

/** User-facing wording for each error category. No technical details. */
export const SERVICE_COPY: Record<ServiceErrorCode, { title: string; help: string }> = {
  ML_NODE_UNAVAILABLE: { title: "The risk service is unavailable", help: "The analysis could not be completed. Wait a moment, then select Analyze again." },
  ML_NODE_TIMEOUT: { title: "The risk service took too long", help: "The analysis could not be completed in time. Select Analyze again." },
  NETWORK_ERROR: { title: "Could not connect to the analysis service", help: "Check your connection and that the service is running, then select Analyze again." },
  INVALID_INPUT: { title: "The input was not accepted", help: "Check the fields and try again." },
  UNKNOWN: { title: "The analysis could not be completed", help: "Something unexpected happened. Select Analyze to try again." },
};
