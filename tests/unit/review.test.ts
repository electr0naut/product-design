import { readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { getArtifact, getView, listProducts, readManifest, readSection, type PortalView } from "@/lib/review";

const product = "portal-smoke";
const fixture = path.join(process.cwd(), "tests/fixtures/portal-smoke.json");
const manifest = path.join(process.cwd(), `review/${product}.json`);

let installed = false;
beforeAll(async () => {
  await writeFile(manifest, await readFile(fixture), { flag: "wx" });
  installed = true;
});
afterAll(async () => {
  if (installed) await rm(manifest, { force: true });
});

describe("review repository boundary", () => {
  it("lists configured products but excludes the EXAMPLE template", async () => {
    const products = await listProducts();
    expect(products).toContain(product);
    expect(products).not.toContain("EXAMPLE");
    expect(products).toEqual([...products].sort());
  });

  it.each(["../EXAMPLE", "..", "EXAMPLE/../../etc/passwd", "UPPERCASE", "a.b"])(
    "rejects unsafe product segment %s before reading a manifest",
    async (segment) => {
      await expect(readManifest(segment)).rejects.toThrow("invalid path segment");
    },
  );

  it("rejects unknown artifacts rather than accepting client paths", async () => {
    await expect(getArtifact(product, "design-to-backlog", "E01", -1)).rejects.toThrow("unknown artifact");
    await expect(getArtifact(product, "design-to-backlog", "E01", 99)).rejects.toThrow("unknown artifact");
    await expect(readSection(product, "../../etc/passwd", "Anything")).rejects.toThrow(
      "artifact is not part of any review lane",
    );
  });

  it("round-trips the Python portal contract and keeps unassigned lanes read-only", async () => {
    const view: PortalView = await getView(product, "product");
    expect(view).toMatchObject({
      product,
      role: "product",
      pending_for_role: [{ gate: "design-to-backlog", lane: "E01", ready: false }],
      blocked_on_others: [],
      context: [{ gate: "design-to-backlog", lane: "E02" }],
      questions_for_role: [],
    });
    expect(Number.isNaN(Date.parse(view.generated_at))).toBe(false);
    expect(view.pending_for_role[0].artifacts).toEqual([
      { path: "README.md", sha256: expect.stringMatching(/^[a-f0-9]{64}$/) },
    ]);
    expect(view.context[0]).not.toHaveProperty("artifacts");
  });
});
