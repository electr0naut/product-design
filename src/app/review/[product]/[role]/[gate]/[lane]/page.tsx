import Link from "next/link";
import DecisionForm from "@/components/DecisionForm";
import { getArtifact, getView, headCommit, readManifest } from "@/lib/review";

export default async function LaneReview({
  params,
}: {
  params: Promise<{ product: string; role: string; gate: string; lane: string }>;
}) {
  const { product, role, gate, lane } = await params;
  let view;
  try {
    view = await getView(product, role);
  } catch {
    return (
      <main className="min-h-screen bg-stone-50 px-6 py-10">
        <p className="mx-auto max-w-4xl rounded border border-amber-300 bg-amber-50 p-4 text-sm">
          Cannot load this review queue. Check the manifest.
        </p>
      </main>
    );
  }
  const entry = [...view.pending_for_role, ...view.blocked_on_others, ...view.context].find(
    (item) => item.gate === gate && item.lane === lane,
  );
  if (!entry) {
    return (
      <main className="min-h-screen bg-stone-50 px-6 py-10">
        <p className="mx-auto max-w-4xl rounded border border-amber-300 bg-amber-50 p-4 text-sm">
          This lane is not part of the {role} review.
        </p>
      </main>
    );
  }

  const manifest = await readManifest(product);
  const questions = manifest.questions.filter((question) =>
    (entry.questions ?? []).includes(question.id),
  );
  const artifacts = entry.artifacts ?? [];
  const contents = await Promise.all(
    artifacts.map(async (artifact, index) => {
      try {
        const file = await getArtifact(product, gate, lane, index);
        return { ...artifact, text: file.text };
      } catch {
        return { ...artifact, text: "Unavailable." };
      }
    }),
  );
  const commit = await headCommit();

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-10 text-zinc-950">
      <div className="mx-auto max-w-4xl">
        <Link
          href={`/review/${product}/${role}`}
          className="text-sm text-cyan-700 underline"
        >
          {role} queue
        </Link>
        <h1 className="mt-3 text-2xl font-semibold">
          {gate} / {lane}
        </h1>
        <p className="mt-2 text-sm text-zinc-600">
          {entry.ready
            ? "This lane is ready; your decision is already recorded."
            : "This lane needs a decision before the next phase can consume it."}
        </p>

        {entry.reasons.length > 0 && (
          <section className="mt-4 rounded border border-zinc-200 bg-white p-4">
            <h2 className="text-sm font-semibold">What blocks it</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-zinc-700">
              {entry.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </section>
        )}

        <section className="mt-6">
          <h2 className="text-lg font-semibold">Reviewed artifacts</h2>
          <p className="mt-1 text-xs text-zinc-500">
            Hashes are what an approval binds. Source commit: <code>{commit || "unknown"}</code>
          </p>
          <ul className="mt-3 space-y-3">
            {contents.map((artifact) => (
              <li key={artifact.path} className="rounded border border-zinc-200 bg-white">
                <div className="border-b border-zinc-200 px-4 py-3">
                  <p className="font-mono text-xs text-zinc-700">{artifact.path}</p>
                  <p className="mt-1 break-all font-mono text-[10px] text-zinc-500">
                    sha256 {artifact.sha256}
                  </p>
                </div>
                <details className="px-4 py-3">
                  <summary className="cursor-pointer text-sm font-medium">Show content</summary>
                  <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap text-xs text-zinc-800">
                    {artifact.text}
                  </pre>
                </details>
              </li>
            ))}
          </ul>
        </section>

        {entry.other_roles && Object.keys(entry.other_roles).length > 0 && (
          <section className="mt-6 rounded border border-zinc-200 bg-white p-4">
            <h2 className="text-sm font-semibold">Other required roles</h2>
            <ul className="mt-2 space-y-1 text-sm text-zinc-700">
              {Object.entries(entry.other_roles).map(([name, decision]) => (
                <li key={name}>
                  <span className="font-medium capitalize">{name}</span>:{" "}
                  {decision.decision.replaceAll("_", " ")} by {decision.reviewer} on{" "}
                  {new Date(decision.recorded_at).toLocaleDateString()}
                </li>
              ))}
            </ul>
          </section>
        )}

        <div className="mt-8">
          <DecisionForm
            product={product}
            gate={gate}
            lane={lane}
            role={role}
            artifacts={artifacts}
            sourceCommit={commit}
            questions={questions.map((question) => ({ id: question.id, text: question.text }))}
          />
        </div>
      </div>
    </main>
  );
}
