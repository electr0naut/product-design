import { NextResponse, type NextRequest } from "next/server";

const LOOPBACK = new Set(["127.0.0.1", "localhost", "[::1]", "::1"]);

export function proxy(request: NextRequest) {
  const host = request.headers.get("host") ?? "";
  const hostname = host.startsWith("[") ? host.slice(0, host.indexOf("]") + 1) : host.split(":")[0];
  if (process.env.REVIEW_PORTAL_TRUSTED_PROXY !== "1" && !LOOPBACK.has(hostname)) {
    return new NextResponse("Review pages are local-only.", { status: 403 });
  }
  if (request.nextUrl.pathname.startsWith("/review")) {
    const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
    const csp = [
      "default-src 'self'",
      `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${process.env.NODE_ENV === "development" ? " 'unsafe-eval'" : ""}`,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data:",
      "connect-src 'self'",
      "font-src 'self' data:",
      "object-src 'none'",
      "frame-ancestors 'none'",
      "base-uri 'none'",
      "form-action 'self'",
    ].join("; ");
    const headers = new Headers(request.headers);
    headers.set("x-nonce", nonce);
    headers.set("Content-Security-Policy", csp);
    const response = NextResponse.next({ request: { headers } });
    response.headers.set("Content-Security-Policy", csp);
    response.headers.set("Cache-Control", "private, no-store");
    return response;
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/review/:path*", "/api/:path*"],
};
