"use client";
import { useCallback, useRef, useState } from "react";
import { analyzeTransaction } from "@/lib/api/analyze";
import { ApiError } from "@/lib/api/errors";
import type { AnalysisViewState, AnalyzeRequest } from "@/lib/types/api";

/** Owns the analysis lifecycle: empty → loading → success | error. Only one request at a time. */
export function useAnalysis() {
  const [state, setState] = useState<AnalysisViewState>({ kind: "empty" });
  const inFlight = useRef(false);

  const run = useCallback(async (req: AnalyzeRequest) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setState({ kind: "loading" }); // clears any previous result first
    try {
      setState({ kind: "success", result: await analyzeTransaction(req) });
    } catch (e) {
      const err = e instanceof ApiError ? e : new ApiError("UNKNOWN", "Something went wrong while analyzing.");
      setState(
        err.code === "INVALID_INPUT"
          ? { kind: "validation-error", message: err.message, requestId: err.requestId }
          : { kind: "service-error", code: err.code, message: err.message, requestId: err.requestId },
      );
    } finally {
      inFlight.current = false;
    }
  }, []);

  const reset = useCallback(() => setState({ kind: "empty" }), []);
  return { state, run, show: setState, reset };
}
