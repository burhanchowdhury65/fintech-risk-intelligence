"use client";
import { useEffect, useRef } from "react";
import { Card } from "@/components/ui/Card";
import { TransactionForm } from "@/components/transaction/TransactionForm";
import { ResultPanel } from "@/components/risk/ResultPanel";
import { CounterfactualBox } from "@/components/risk/CounterfactualBox";
import { STATUS_META } from "@/lib/risk";
import { FIELD_LABELS, fromRequest, toAnalyzeRequest, validate } from "@/lib/validation";
import type { AnalysisViewState, FieldName } from "@/lib/types/api";
import type { DemoScenario } from "@/lib/mock/scenarios";
import { useAnalysisContext } from "./AnalysisProvider";

function announce(s: AnalysisViewState): string {
  switch (s.kind) {
    case "loading": return "Analyzing transaction.";
    case "success": return `Analysis complete. Risk score ${s.result.risk_score} out of 100, ${STATUS_META[s.result.risk_status].label}.`;
    case "validation-error": return "Some fields need attention.";
    case "service-error": return "Analysis could not be completed.";
    default: return "";
  }
}

export function AnalysisWorkspace() {
  const { state, run, show, reset, stale, setStale, values, setValues, errors, setErrors, activeDemo, setActiveDemo, origin, setOrigin } = useAnalysisContext();
  const resultRef = useRef<HTMLDivElement>(null);
  const returnFocusTo = useRef<HTMLElement | null>(null);
  const loading = state.kind === "loading";

  /* Controls are disabled while loading, which drops keyboard focus to <body>.
     Put focus back where the user was once the request finishes (without scrolling). */
  useEffect(() => {
    if (!loading && returnFocusTo.current) {
      if (document.activeElement === document.body || document.activeElement === null) {
        returnFocusTo.current.focus({ preventScroll: true });
      }
      returnFocusTo.current = null;
    }
  }, [loading]);

  function onChange(name: FieldName, value: string) {
    setValues((v) => ({ ...v, [name]: value }));
    setActiveDemo(null);
    setErrors((e) => ({ ...e, [name]: undefined }));
    if (state.kind === "success" && origin === "form") setStale(true);
    if (state.kind === "validation-error" && state.fieldErrors) {
      // keep the error summary in sync with the fields the user has already fixed
      const left = { ...state.fieldErrors };
      delete left[name];
      const keys = Object.keys(left) as FieldName[];
      if (keys.length === 0) reset();
      else show({ ...state, fieldErrors: left, message: keys.map((k) => `${FIELD_LABELS[k]}: ${left[k]}`).join(" ") });
    }
  }

  function onSelectDemo(s: DemoScenario) {
    if (loading) return;
    setValues(fromRequest(s.input));
    setActiveDemo(s.id);
    setErrors({});
    setStale(false);
    reset();
  }

  async function onSubmit() {
    if (loading) return;
    const found = validate(values);
    const first = (Object.keys(found) as FieldName[])[0];
    if (first) {
      setErrors(found);
      const list = (Object.keys(found) as FieldName[]).map((k) => `${FIELD_LABELS[k]}: ${found[k]}`);
      show({ kind: "validation-error", message: list.join(" "), fieldErrors: found });
      document.getElementById(first)?.focus();
      return;
    }
    setStale(false);
    setOrigin("form");
    returnFocusTo.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    if (window.matchMedia("(max-width: 1023px)").matches) {
      const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      resultRef.current?.scrollIntoView({ behavior: calm ? "auto" : "smooth", block: "start" });
    }
    await run(toAnalyzeRequest(values));
  }

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      <p className="sr-only" role="status" aria-live="polite">{announce(state)}</p>
      <div id="analyze" className="min-w-0 scroll-mt-4 lg:col-span-2">
        <Card headingId="analyze-title" title="Transaction analysis" description="Enter the details of one transaction, or start from a demo input.">
          <TransactionForm
            values={values}
            errors={errors}
            activeDemo={activeDemo}
            loading={loading}
            onChange={onChange}
            onSelectDemo={onSelectDemo}
            onSubmit={onSubmit}
          />
        </Card>
      </div>
      <div id="result" ref={resultRef} tabIndex={-1} className="min-w-0 scroll-mt-4 outline-none lg:col-span-3">
        <Card headingId="result-title" title="Analysis result">
          <ResultPanel state={state} stale={stale} fromChat={origin === "chat"} />
        </Card>
        {state.kind === "success" && !stale && <CounterfactualBox result={state.result} />}
      </div>
    </div>
  );
}
