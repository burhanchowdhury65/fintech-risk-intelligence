"use client";
import { createContext, useContext, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import { EMPTY_FORM, type FormValues } from "@/lib/validation";
import type { FieldErrors } from "@/lib/types/api";
import { useAnalysis } from "./useAnalysis";

type Value = ReturnType<typeof useAnalysis> & {
  stale: boolean;
  setStale: Dispatch<SetStateAction<boolean>>;
  values: FormValues;
  setValues: Dispatch<SetStateAction<FormValues>>;
  errors: FieldErrors;
  setErrors: Dispatch<SetStateAction<FieldErrors>>;
  /** Where the shown result came from: the form, or an ARIA chat message (inputs may not match the form). */
  origin: "form" | "chat";
  setOrigin: Dispatch<SetStateAction<"form" | "chat">>;
  activeDemo: string | null;
  setActiveDemo: Dispatch<SetStateAction<string | null>>;
};
const Ctx = createContext<Value | null>(null);

/** One shared source of truth for the form, the analysis result and the ARIA chat. */
export function AnalysisProvider({ children }: { children: ReactNode }) {
  const analysis = useAnalysis();
  const [stale, setStale] = useState(false);
  const [values, setValues] = useState<FormValues>(EMPTY_FORM);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [origin, setOrigin] = useState<"form" | "chat">("form");
  const [activeDemo, setActiveDemo] = useState<string | null>(null);
  return <Ctx.Provider value={{ ...analysis, stale, setStale, values, setValues, errors, setErrors, origin, setOrigin, activeDemo, setActiveDemo }}>{children}</Ctx.Provider>;
}

export function useAnalysisContext(): Value {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAnalysisContext must be used inside <AnalysisProvider>");
  return v;
}
