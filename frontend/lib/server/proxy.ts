import { API_BASE_URL } from "@/lib/config";
import type { ServiceErrorCode } from "@/lib/types/api";

/**
 * Dev proxy helper (server only). Adds the JWT (DEV_JWT, never NEXT_PUBLIC_) so it stays out of the browser.
 * DEV ONLY: do not deploy these routes with a real DEV_JWT; they forward any caller's request with that token.
 * Replace DEV_JWT with the real login flow once Person A locks it.
 * Optional PROXY_TIMEOUT_MS (server env) overrides every route's limit, so QA can trigger a timeout quickly.
 */
const fail = (status: number, message: string, error_code: ServiceErrorCode = "UNKNOWN") =>
  Response.json({ detail: { error_code, message } }, { status });

export async function proxyPost(req: Request, path: string, timeoutMs: number, timeoutCode: ServiceErrorCode = "ML_NODE_TIMEOUT"): Promise<Response> {
  const token = process.env.DEV_JWT;
  if (!token) return fail(500, "DEV_JWT is not set. Add it to .env.local and restart the dev server.");
  const limit = Number(process.env.PROXY_TIMEOUT_MS) || timeoutMs;
  try {
    const upstream = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: await req.text(),
      cache: "no-store",
      signal: AbortSignal.timeout(limit),
    });
    return new Response(await upstream.text(), { status: upstream.status, headers: { "Content-Type": "application/json" } });
  } catch (e) {
    if (e instanceof DOMException && e.name === "TimeoutError") return fail(504, "The backend did not answer in time.", timeoutCode);
    return fail(502, `Could not reach the backend at ${API_BASE_URL}. Check that it is running.`, "NETWORK_ERROR");
  }
}
