/**
 * MOCK ONLY: reads transaction details from chat text with simple patterns.
 * The real ARIA agent does this with an LLM; this stands in until /aria/chat is wired.
 * It never guesses a missing value. Missing details are reported back so ARIA can ask for them.
 */
import { MERCHANT_CATEGORIES } from "@/lib/constants";
import type { AnalyzeRequest } from "@/lib/types/api";

export interface ParsedTransaction {
  amount?: number;
  category?: string;
  time?: string; // HH:MM, 24h
  distance?: number;
}

const num = (s?: string) => (s === undefined ? undefined : Number(s.replace(/,/g, "")));

export function parseTransactionText(raw: string): ParsedTransaction {
  const text = raw.toLowerCase().replace(/from home/g, " "); // "home" is also a merchant category
  const out: ParsedTransaction = {};

  out.amount = num(
    text.match(/amount\D{0,3}(\d[\d,]*(?:\.\d+)?)/)?.[1] ??
      text.match(/(?:\$|usd|bdt|tk|৳)\s*(\d[\d,]*(?:\.\d+)?)/)?.[1] ??
      text.match(/(\d[\d,]*(?:\.\d+)?)\s*(?:usd|dollars?|bdt|taka|tk)\b/)?.[1],
  );
  out.distance = num(
    text.match(/(\d+(?:\.\d+)?)\s*(?:km|kilomet(?:er|re)s?|miles?)\b/)?.[1] ?? text.match(/distance\D{0,3}(\d+(?:\.\d+)?)/)?.[1],
  );
  out.category = MERCHANT_CATEGORIES.find((c) => text.includes(c) || text.includes(c.replace("_", " ")));

  const clock = text.match(/\b(\d{1,2}):(\d{2})\s*(am|pm)?/) ?? text.match(/\b(\d{1,2})()\s*(am|pm)\b/);
  if (clock) {
    let h = Number(clock[1]);
    if (clock[3] === "pm" && h < 12) h += 12;
    if (clock[3] === "am" && h === 12) h = 0;
    if (h <= 23 && Number(clock[2] || 0) <= 59) out.time = `${String(h).padStart(2, "0")}:${clock[2] || "00"}`;
  }
  return out;
}

const pad = (n: number) => String(n).padStart(2, "0");

/** Assumptions (mock): today's date, and transaction_type "purchase" (required by the contract, unused by the model). */
export function toRequest(p: Required<Pick<ParsedTransaction, "amount" | "category" | "time">> & ParsedTransaction): AnalyzeRequest {
  const d = new Date();
  return {
    transaction_amount: p.amount,
    transaction_type: "purchase",
    merchant_category: p.category,
    transaction_time: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${p.time}:00`,
    distance_from_home: p.distance ?? null,
    location: null,
  };
}
