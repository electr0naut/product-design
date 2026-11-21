import { NextResponse, type NextRequest } from "next/server";

const LOOPBACK = new Set(["127.0.0.1", "localhost", "[::1]", "::1"]);

export function proxy(request: NextRequest) {
  if (process.env.REVIEW_PORTAL_TRUSTED_PROXY === "1") return NextResponse.next();
  const host = request.headers.get("host") ?? "";
  const hostname = host.startsWith("[") ? host.slice(0, host.indexOf("]") + 1) : host.split(":")[0];
  if (!LOOPBACK.has(hostname)) {
    return new NextResponse("Review pages are local-only.", { status: 403 });
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/review/:path*", "/api/:path*"],
};
