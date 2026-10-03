import { Badge } from "@/components/ui/Badge";
import { USE_MOCK_API } from "@/lib/config";
import type { AnalyzeResponse } from "@/lib/types/api";

export function SourceBadge({ result }: { result: AnalyzeResponse }) {
  if (result.source_mode === "CACHED") return <Badge tone="warning">CACHED DEMO</Badge>;
  if (USE_MOCK_API) return <Badge tone="info">Mock result</Badge>;
  if (result.source_mode === "LIVE") return <Badge tone="success">LIVE ANALYSIS</Badge>;
  return <Badge tone="neutral">From API</Badge>; // source_mode is not in the real response yet (TBD)
}
