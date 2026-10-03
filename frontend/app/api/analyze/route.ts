import { proxyPost } from "@/lib/server/proxy";

export const POST = (req: Request) => proxyPost(req, "/analyze", 30_000);
