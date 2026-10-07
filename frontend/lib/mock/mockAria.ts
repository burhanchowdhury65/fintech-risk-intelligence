/**
 * MOCK ARIA. Template replies built only from structured results. It invents no reasons, scores or factors,
 * and it cannot change the score. Chat-to-analysis uses the real API client (mock or live, per the app mode).
 * Replaced by the real /aria/chat call once its contract is locked.
 */
import { LIMITATIONS_TEXT } from "@/lib/copy";
import { categoryLabel } from "@/lib/constants";
import { analyzeTransaction } from "@/lib/api/analyze";
import { ApiError } from "@/lib/api/errors";
import { STATUS_META } from "@/lib/risk";
import { FIELD_LABELS, validate, type FormValues } from "@/lib/validation";
import type { AnalyzeResponse } from "@/lib/types/api";
import type { AriaContext, AriaReply } from "@/lib/types/aria";
import { parseTransactionText, toRequest } from "./parseTransaction";

export const ARIA_ERROR_PROMPT = "Demo: ARIA unavailable";
const DELAY_MS = 700;
const EXAMPLE = "Analyze: amount 890, shopping_net, 03:15, 240 km";

function summary(r: AnalyzeResponse): string {
  const meta = STATUS_META[r.risk_status];
  const factors = r.model_factors.length ? "The factors it reported are in the result card." : "It did not report any specific risk factors.";
  return `The model ${r.is_fraud ? "flagged" : "did not flag"} this transaction: ${meta.label.toLowerCase()}, score ${r.risk_score} / 100. ${factors}${r.explanation ? `\n\n${r.explanation}` : ""}`;
}

async function analyzeFromChat(message: string): Promise<AriaReply | null> {
  const p = parseTransactionText(message);
  const found = p.amount !== undefined || p.category !== undefined || p.time !== undefined || p.distance !== undefined;
  if (!found && !/analy[sz]e/i.test(message)) return null;

  const missing = [p.amount === undefined && "the amount", !p.category && "the merchant category", !p.time && "the time"].filter(Boolean);
  if (missing.length) {
    return { text: `To analyze a transaction I still need ${missing.join(", ")}. For example:\n${EXAMPLE}` };
  }
  const request = toRequest({ ...p, amount: p.amount!, category: p.category!, time: p.time! });
  const form: FormValues = {
    transaction_amount: String(request.transaction_amount), transaction_time: request.transaction_time.slice(0, 16),
    transaction_type: request.transaction_type, merchant_category: request.merchant_category,
    distance_from_home: request.distance_from_home == null ? "" : String(request.distance_from_home),
    customer_latitude:
      typeof request.location === "object" && request.location !== null && "customer_lat" in request.location
        ? String(request.location.customer_lat)
        : "",
    customer_longitude:
      typeof request.location === "object" && request.location !== null && "customer_long" in request.location
        ? String(request.location.customer_long)
        : "",
    merchant_latitude:
      typeof request.location === "object" && request.location !== null && "merchant_lat" in request.location
        ? String(request.location.merchant_lat)
        : "",
    merchant_longitude:
      typeof request.location === "object" && request.location !== null && "merchant_long" in request.location
        ? String(request.location.merchant_long)
        : "",
  };
  const problems = Object.entries(validate(form)).map(([k, v]) => `${FIELD_LABELS[k as keyof typeof FIELD_LABELS]}: ${v}`);
  if (problems.length) return { text: `I couldn't use those details, so nothing was analyzed.\n${problems.join("\n")}` };

  const result = await analyzeTransaction(request); // throws ApiError on failure: no fabricated result
  const read = `amount ${request.transaction_amount}, ${categoryLabel(request.merchant_category).toLowerCase()}, time ${p.time}${request.distance_from_home != null ? `, distance ${request.distance_from_home}` : ""}`;
  return { text: `I analyzed: ${read}. (Preview: details were read by simple text matching, and today's date was used. Check the form to confirm.)\n\n${summary(result)}`, toolResult: result, analyzedRequest: request };
}

export async function mockAriaReply(message: string, ctx: AriaContext): Promise<AriaReply> {
  await new Promise((r) => setTimeout(r, DELAY_MS));
  if (message === ARIA_ERROR_PROMPT) throw new ApiError("UNKNOWN", "ARIA is unavailable.");
  if (ctx.running) return { text: "An analysis is still running. Ask me again when the result appears." };

  const fromChat = await analyzeFromChat(message);
  if (fromChat) return fromChat;

  const m = message.toLowerCase();
  const r = ctx.result;
  if (!r) return { text: `There is no analysis result yet. Run an analysis above, or ask me here, for example:\n${EXAMPLE}` };

  const meta = STATUS_META[r.risk_status];
  const note = ctx.stale ? "\n\nNote: the form changed after this analysis, so this is about the last result." : "";
  const reply = (text: string): AriaReply => ({ text: text + note, toolResult: r });
  if (/limit/.test(m)) return reply(LIMITATIONS_TEXT);
  if (/score|mean|probab|percent/.test(m))
    return reply(`The risk score runs from 0 to 100 and is a relative ranking, not a probability or a percentage. This result is ${r.risk_score} / 100, in the ${meta.label.toLowerCase()} band. The bands (0–39 low, 40–69 medium, 70–100 high) are provisional.`);
  if (/why|flag|factor|reason|explain|result/.test(m)) return reply(summary(r));
  return { text: "I can explain the current result (status, score, factors, limitations) or analyze a transaction you describe. I can't change the score." };
}
