/* ---------- CONFIRMED by Person A: POST /aria/chat (Bearer JWT) ---------- */
export interface AriaChatRequest {
  message: string;
  /** Optional, server default "English". */
  language?: string;
  /** Optional. The server does not generate one; the response echoes it (null if omitted). */
  session_id?: string;
}

export interface AriaChatResponse {
  reply: string;
  /** "groq" or "openai", depending on fallback. */
  provider: string;
  session_id: string | null;
  /** Same core fields as /analyze, or null for normal chat. This is the source of truth, not the reply text. */
  tool_result: AnalyzeResponse | null;
}
/* TBD (Person A): error shape when both LLM providers fail, latency, source_mode, follow-up for missing fields. */

/**
 * TEMPORARY, MOCK-ONLY types. The real POST /aria/chat contract (request, response, session id,
 * tool-result shape) is NOT defined yet (Person A). Replace these when it is locked.
 */
import type { AnalyzeRequest, AnalyzeResponse } from "./api";

export interface ChatMessage {
  id: number;
  role: "user" | "aria";
  text: string;
  /** Snapshot of the structured risk result this reply is based on. */
  toolResult?: AnalyzeResponse;
  error?: boolean;
  /** false = trying the same message again cannot help. */
  retryable?: boolean;
}

export interface AriaContext {
  result: AnalyzeResponse | null;
  running: boolean;
  /** The form was edited after `result` was produced. */
  stale: boolean;
}

export interface AriaReply {
  text: string;
  toolResult?: AnalyzeResponse;
  /** Set when this reply ran a new analysis from the chat message. */
  analyzedRequest?: AnalyzeRequest;
}
