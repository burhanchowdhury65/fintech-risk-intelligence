import { proxyPost } from "@/lib/server/proxy";

// ARIA can make two LLM calls plus the ML call. Latency is not benchmarked yet (Person A), so this limit is provisional.
// A timeout here is not necessarily the ML node, so it is reported as a generic error, not ML_NODE_TIMEOUT.
export const POST = (req: Request) => proxyPost(req, "/aria/chat", 60_000, "UNKNOWN");
