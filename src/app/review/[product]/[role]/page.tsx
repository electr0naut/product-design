import Link from "next/link";
import { getView, type LaneEntry } from "@/lib/review";

function LaneList({
  product,
  role,
  entries,
  empty,
}: {
  product: string;
  role: string;
  entries: LaneEntry[];
  empty: string;
}) {
  if (entries.length === 0) {
    return <p className="mt-2 text-sm text-zinc-600">{empty}</p>;
  }
  return (
    <ul className="mt-2 divide-y divide-zinc-200 rounded border border-zinc-200 bg-white">
      {entries.map((entry) => (
        <li key={`${entry.gate}-${entry.lane}`}>
          <Link
            href={`/review/${product}/${role}/${entry.gate}/${entry.lane}`}
            className="block px-4 py-3 hover:bg-zinc-50"
          >
            <span className="font-medium">
              {entry.gate} / {entry.lane}
            </span>
            <span className="ml-2 rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700">
              {entry.ready ? "ready" : entry.reasons[0] ?? "blocked"}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export default async function RoleQueue({
  params,
}: {
  params: Promise<{ product: string; role: string }>;
}) {
  const { product, role } = await params;
  let view;
  try {
    view = await getView(product, role);
  } catch {
    return (
      <main className="min-h-screen bg-stone-50 px-6 py-10">
        <div className="mx-auto max-w-4xl">
          <p className="rounded border border-amber-300 bg-amber-50 p-4 text-sm">
            This role is not configured for {product}, or the manifest is invalid.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-10 text-zinc-950">
      <div className="mx-auto max-w-4xl">
        <Link href={`/review/${product}`} className="text-sm text-cyan-700 underline">
          {product} roles
        </Link>
        <h1 className="mt-3 text-3xl font-semibold capitalize">{role} review queue</h1>
        <p className="mt-2 text-sm text-zinc-600">
          Generated {new Date(view.generated_at).toLocaleString()} from the review manifest.
        </p>

        <section className="mt-8">
          <h2 className="text-lg font-semibold">Needs your attention</h2>
          <LaneList
            product={product}
            role={role}
            entries={view.pending_for_role}
            empty="Nothing is waiting for this role."
          />
        </section>

        <section className="mt-8">
          <h2 className="text-lg font-semibold">Blocked on other roles</h2>
          <LaneList
            product={product}
            role={role}
            entries={view.blocked_on_others}
            empty="No lane has your approval while waiting on someone else."
          />
        </section>

        <section className="mt-8">
          <h2 className="text-lg font-semibold">Context</h2>
          <LaneList
            product={product}
            role={role}
            entries={view.context}
            empty="No other lanes."
          />
        </section>

        {view.questions_for_role.length > 0 && (
          <section className="mt-8 rounded border border-amber-300 bg-amber-50 p-4">
            <h2 className="text-lg font-semibold text-amber-900">Open questions for you</h2>
            <ul className="mt-2 space-y-2 text-sm text-amber-900">
              {view.questions_for_role.map((question) => (
                <li key={question.id}>
                  <span className="font-mono text-xs">{question.id}</span> {question.text}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
