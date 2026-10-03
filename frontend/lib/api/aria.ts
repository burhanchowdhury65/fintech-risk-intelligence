import { USE_MOCK_API } from "@/lib/config";
import { mockAriaReply } from "@/lib/mock/mockAria";
import type { AnalyzeResponse } from "@/lib/types/api";
import type { AriaChatResponse, AriaContext, AriaReply } from "@/lib/types/aria";
import { normalize } from "./analyze";
import { ApiError, toApiError } from "./errors";

const CLIENT_TIMEOUT_MS = 70_000; // provisional: ARIA latency is not benchmarked yet (Person A)

/**
 * Single entry point for ARIA chat.
 * - Mock mode: lib/mock/mockAria (template replies).
 * - Live mode: POST /api/aria/chat (server proxy that adds the JWT) → backend POST /aria/chat.
 *   A card is shown ONLY for a valid, non-null tool_result. Nothing is guessed from the reply text.
 */
export async function askAria(message: string, ctx: AriaContext): Promise<AriaReply> {
  if (USE_MOCK_API) return mockAriaReply(message, ctx);

  let res: Response;
  try {
    res = await fetch("/api/aria/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        language: "English",
        context: {
          result: ctx.result,
          running: ctx.running,
          stale: ctx.stale,
        },
      }),
      signal: AbortSignal.timeout(CLIENT_TIMEOUT_MS),
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "TimeoutError") throw new ApiError("UNKNOWN", "ARIA did not answer in time.");
    throw new ApiError("NETWORK_ERROR", "Could not reach the app server.");
  }
  if (!res.ok) throw await toApiError(res);

  let body: Partial<AriaChatResponse>;
  try {
    body = (await res.json()) as Partial<AriaChatResponse>;
  } catch {
    throw new ApiError("UNKNOWN", "ARIA returned a response that is not valid JSON.");
  }
  if (typeof body.reply !== "string" || !body.reply.trim()) throw new ApiError("UNKNOWN", "ARIA returned an empty reply.");
  // Invalid tool_result throws: the reply may describe an analysis that cannot be trusted, so show an error instead.
  const toolResult: AnalyzeResponse | undefined = body.tool_result ? normalize(body.tool_result) : undefined;
  return { text: body.reply, toolResult };
}
