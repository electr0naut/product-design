import "server-only";

import { execFile } from "node:child_process";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);
const ROOT = process.cwd();
const REVIEW = path.join(ROOT, "review");
const PRODUCT = /^[a-z0-9-]+$/;
const ROLE = /^[a-z0-9-]+$/;

export type Decision = {
  id: string;
  decision: string;
  reviewer: string;
  recorded_at: string;
  evidence: string;
  source_commit: string;
};

export type LaneEntry = {
  gate: string;
  lane: string;
  ready: boolean;
  reasons: string[];
  artifacts?: { path: string; sha256: string }[];
  decision?: Decision;
  other_roles?: Record<string, Decision>;
  questions?: string[];
};

export type PortalView = {
  product: string;
  role: string;
  generated_at: string;
  pending_for_role: LaneEntry[];
  blocked_on_others: LaneEntry[];
  context: LaneEntry[];
  questions_for_role: {
    id: string;
    text: string;
    source: { artifact: string; heading: string };
  }[];
};

type Manifest = {
  product: string;
  gates: {
    id: string;
    lanes: Record<string, { roles: string[]; artifacts: string[]; epic?: boolean }>;
  }[];
  questions: {
    id: string;
    gate: string;
    lane: string;
    role: string;
    text: string;
    source: { artifact: string; heading: string };
  }[];
};

function safeSegment(value: string, pattern: RegExp): string {
  if (!pattern.test(value)) throw new Error("invalid path segment");
  return value;
}

export async function listProducts(): Promise<string[]> {
  const entries = await readdir(/*turbopackIgnore: true*/ REVIEW, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() && entry.name.endsWith(".json"))
    .map((entry) => entry.name.slice(0, -".json".length))
    .filter((name) => name !== "EXAMPLE" && PRODUCT.test(name))
    .sort();
}

export async function readManifest(product: string): Promise<Manifest> {
  const name = safeSegment(product, PRODUCT);
  const raw = await readFile(/*turbopackIgnore: true*/ path.join(REVIEW, `${name}.json`), "utf8");
  return JSON.parse(raw) as Manifest;
}

export async function listRoles(product: string): Promise<string[]> {
  const manifest = await readManifest(product);
  const roles = new Set<string>();
  for (const gate of manifest.gates) {
    for (const lane of Object.values(gate.lanes)) {
      for (const role of lane.roles) roles.add(role);
    }
  }
  return [...roles].sort();
}

export async function getView(product: string, role: string): Promise<PortalView> {
  const name = safeSegment(product, PRODUCT);
  const subject = safeSegment(role, ROLE);
  const manifestPath = path.join(REVIEW, `${name}.json`);
  const { stdout } = await run(
    process.env.REVIEW_PYTHON ?? "python3",
    [
      /*turbopackIgnore: true*/ path.join(ROOT, "shared", "scripts", "check_gate.py"),
      "--manifest",
      manifestPath,
      "--role",
      subject,
    ],
    { cwd: ROOT, maxBuffer: 4 * 1024 * 1024 },
  );
  return JSON.parse(stdout) as PortalView;
}

export async function getArtifact(
  product: string,
  gate: string,
  lane: string,
  index: number,
): Promise<{ path: string; sha256: string; text: string }> {
  const manifest = await readManifest(product);
  const gateEntry = manifest.gates.find((entry) => entry.id === gate);
  if (!gateEntry) throw new Error("unknown gate");
  const laneEntry = gateEntry.lanes[lane];
  if (!laneEntry) throw new Error("unknown lane");
  const artifacts = laneEntry.artifacts;
  if (!artifacts || !Number.isInteger(index) || index < 0 || index >= artifacts.length) {
    throw new Error("unknown artifact");
  }
  const relative = artifacts[index];
  const resolved = path.resolve(/*turbopackIgnore: true*/ ROOT, relative);
  if (!resolved.startsWith(ROOT + path.sep)) throw new Error("artifact outside repository");
  const text = await readFile(/*turbopackIgnore: true*/ resolved, "utf8");
  return { path: relative, sha256: "", text: text.slice(0, 200_000) };
}

export function questionFor(
  manifest: Manifest,
  id: string,
): Manifest["questions"][number] | undefined {
  return manifest.questions.find((question) => question.id === id);
}

export async function readSection(product: string, artifact: string, heading: string) {
  const manifest = await readManifest(product);
  const allowed = new Set<string>();
  for (const gate of manifest.gates) {
    for (const lane of Object.values(gate.lanes)) {
      for (const item of lane.artifacts) allowed.add(item);
    }
  }
  if (!allowed.has(artifact)) throw new Error("artifact is not part of any review lane");
  const resolved = path.resolve(/*turbopackIgnore: true*/ ROOT, artifact);
  if (!resolved.startsWith(ROOT + path.sep)) throw new Error("artifact outside repository");
  const text = await readFile(/*turbopackIgnore: true*/ resolved, "utf8");
  const lines = text.split("\n");
  const start = lines.findIndex(
    (line) => line.replace(/^#+\s*/, "").trim() === heading.trim() && line.startsWith("#"),
  );
  if (start === -1) return text.slice(0, 12_000);
  let end = lines.length;
  for (let cursor = start + 1; cursor < lines.length; cursor += 1) {
    if (/^#{1,6}\s/.test(lines[cursor])) {
      end = cursor;
      break;
    }
  }
  return lines.slice(start, end).join("\n").slice(0, 12_000);
}

export async function headCommit(): Promise<string> {
  try {
    const { stdout } = await run("git", ["rev-parse", "HEAD"], { cwd: ROOT });
    return stdout.trim();
  } catch {
    return "";
  }
}
