"use client";

import { useMemo, useState } from "react";

type Artifact = { path: string; sha256: string };
type Question = { id: string; text: string };

type Props = {
  product: string;
  gate: string;
  lane: string;
  role: string;
  artifacts: Artifact[];
  sourceCommit: string;
  questions: Question[];
};

type AssistResult = {
  answer: string;
  quotes: string[];
  missing: string[];
  model: string | null;
  error?: string;
};

export default function DecisionForm({
  product,
  gate,
  lane,
  role,
  artifacts,
  sourceCommit,
  questions,
}: Props) {
  const [reviewer, setReviewer] = useState("");
  const [decision, setDecision] = useState("approve");
  const [comment, setComment] = useState("");
  const [questionId, setQuestionId] = useState(questions[0]?.id ?? "");
  const [assist, setAssist] = useState<AssistResult | null>(null);
  const [assistBusy, setAssistBusy] = useState(false);
  const [packet, setPacket] = useState<string>("");

  const packetObject = useMemo(
    () => ({
      schema_version: 1,
      product,
      gate,
      lane,
      role,
      decision,
      reviewer,
      artifact_sha256: Object.fromEntries(artifacts.map((a) => [a.path, a.sha256])),
      feedback: comment.trim() ? [{ text: comment.trim() }] : [],
      created_at: new Date().toISOString(),
      source_commit: sourceCommit,
    }),
    [product, gate, lane, role, decision, reviewer, artifacts, comment, sourceCommit],
  );

  function buildPacket() {
    if (!reviewer.trim()) {
      setPacket("Enter the reviewer name that the maintainer can verify.");
      return;
    }
    setPacket(JSON.stringify(packetObject, null, 2));
  }

  function download() {
    const body = packet.trim() ? packet : JSON.stringify(packetObject, null, 2);
    const blob = new Blob([body], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${product}-${gate}-${lane}-${role}-packet.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function askAssist() {
    if (!questionId) return;
    setAssistBusy(true);
    setAssist(null);
    try {
      const response = await fetch("/api/assist", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Review-Request": "assist" },
        body: JSON.stringify({ product, gate, lane, role, questionId }),
      });
      setAssist((await response.json()) as AssistResult);
    } catch {
      setAssist({ answer: "", quotes: [], missing: [], model: null, error: "Assist unavailable." });
    } finally {
      setAssistBusy(false);
    }
  }

  return (
    <section className="rounded-md border border-zinc-200 bg-white p-5">
      <h2 className="text-lg font-semibold">Record your review</h2>
      <p className="mt-1 text-sm leading-6 text-zinc-600">
        This page is not an approval system. A packet is a draft for the maintainer, who verifies
        the hashes and records it with <code>record_decision.py</code>. Typed names are unverified.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="text-sm">
          <span className="font-medium">Reviewer name</span>
          <input
            className="mt-1 w-full rounded border border-zinc-300 px-3 py-2"
            value={reviewer}
            onChange={(event) => setReviewer(event.target.value)}
            placeholder="As agreed with the maintainer"
          />
        </label>
        <label className="text-sm">
          <span className="font-medium">Decision</span>
          <select
            className="mt-1 w-full rounded border border-zinc-300 px-3 py-2"
            value={decision}
            onChange={(event) => setDecision(event.target.value)}
          >
            <option value="approve">Approve this revision</option>
            <option value="request_changes">Request changes</option>
            <option value="not_applicable">Not applicable to my role</option>
            <option value="cannot_determine">Cannot determine</option>
          </select>
        </label>
      </div>

      {questions.length > 0 && (
        <div className="mt-4 rounded border border-amber-200 bg-amber-50 p-3">
          <p className="text-sm font-medium text-amber-900">Open questions for this lane</p>
          <ul className="mt-2 space-y-2 text-sm text-amber-900">
            {questions.map((question) => (
              <li key={question.id}>
                <span className="font-mono text-xs">{question.id}</span> {question.text}
              </li>
            ))}
          </ul>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <select
              className="rounded border border-amber-300 bg-white px-2 py-1 text-sm"
              value={questionId}
              onChange={(event) => setQuestionId(event.target.value)}
            >
              {questions.map((question) => (
                <option key={question.id} value={question.id}>
                  {question.id}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={askAssist}
              disabled={assistBusy}
              className="rounded bg-amber-900 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
            >
              {assistBusy ? "Drafting..." : "AI draft answer"}
            </button>
            <span className="text-xs text-amber-800">
              AI drafts are grounded in the cited section and are never submitted automatically.
            </span>
          </div>
          {assist && (
            <div className="mt-3 rounded bg-white p-3 text-sm text-zinc-800">
              {assist.error ? (
                <p className="text-red-700">{assist.error}</p>
              ) : (
                <>
                  <p className="whitespace-pre-wrap">{assist.answer}</p>
                  {assist.quotes.length > 0 && (
                    <ul className="mt-2 list-disc pl-5 text-xs text-zinc-600">
                      {assist.quotes.map((quote) => (
                        <li key={quote}>{quote}</li>
                      ))}
                    </ul>
                  )}
                  {assist.missing.length > 0 && (
                    <p className="mt-2 text-xs text-zinc-600">
                      Missing information: {assist.missing.join("; ")}
                    </p>
                  )}
                  <button
                    type="button"
                    className="mt-2 rounded border border-zinc-300 px-3 py-1 text-xs font-medium"
                    onClick={() => setComment((current) => `${current}${current ? "\n" : ""}${assist.answer}`)}
                  >
                    Use this draft in my comment
                  </button>
                  <p className="mt-2 text-xs text-zinc-500">
                    AI draft{assist.model ? ` (${assist.model})` : ""} — verify before submitting.
                  </p>
                </>
              )}
            </div>
          )}
        </div>
      )}

      <label className="mt-4 block text-sm">
        <span className="font-medium">Comment</span>
        <textarea
          className="mt-1 h-32 w-full rounded border border-zinc-300 px-3 py-2"
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="What should change, and why?"
        />
      </label>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={buildPacket}
          className="rounded bg-zinc-900 px-3 py-2 text-sm font-medium text-white"
        >
          Build packet
        </button>
        <button
          type="button"
          onClick={download}
          className="rounded border border-zinc-300 px-3 py-2 text-sm font-medium"
        >
          Download JSON
        </button>
      </div>

      {packet && (
        <div className="mt-4">
          <pre className="max-h-72 overflow-auto rounded bg-zinc-950 p-3 text-xs text-zinc-100">
            {packet}
          </pre>
          <p className="mt-2 text-xs text-zinc-600">
            Maintainer command: <code>record_decision.py --manifest review/{product}.json --packet
            &lt;file&gt; --evidence &lt;channel-ref&gt;</code>
          </p>
        </div>
      )}
    </section>
  );
}
