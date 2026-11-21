import { describe, expect, it } from "vitest";
import { POST } from "@/app/api/assist/route";

const payload = { product: "sample", gate: "design-to-backlog", lane: "E01", role: "product", questionId: "Q-001" };
function request(headers: Record<string, string> = {}, body = JSON.stringify(payload)) {
  return new Request("http://127.0.0.1:3197/api/assist", {
    method: "POST",
    headers: { host: "127.0.0.1:3197", "content-type": "application/json", "x-review-request": "assist", ...headers },
    body,
  });
}

describe("assist API security boundary (disabled; no model invocation)", () => {
  it("rejects foreign origins before processing the body", async () => {
    const response = await POST(request({ origin: "https://evil.example" }));
    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ error: "cross-origin request refused" });
  });

  it("requires the custom request header", async () => {
    const response = await POST(request({ "x-review-request": "" }));
    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ error: "missing request header" });
  });

  it("requires JSON content type", async () => {
    const response = await POST(request({ "content-type": "text/plain" }));
    expect(response.status).toBe(415);
    expect(await response.json()).toEqual({ error: "expected JSON" });
  });

  it("does not expose the model while disabled", async () => {
    const prior = process.env.REVIEW_ASSIST_ENABLED;
    delete process.env.REVIEW_ASSIST_ENABLED;
    try {
      const response = await POST(request());
      expect(response.status).toBe(503);
      expect(await response.json()).toEqual({ error: "assist is not enabled" });
    } finally {
      if (prior === undefined) delete process.env.REVIEW_ASSIST_ENABLED;
      else process.env.REVIEW_ASSIST_ENABLED = prior;
    }
  });
});
