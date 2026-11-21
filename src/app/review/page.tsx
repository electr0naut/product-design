import Link from "next/link";
import { listProducts, readManifest } from "@/lib/review";

export default async function ReviewIndex() {
  const products = await listProducts();
  const summaries = await Promise.all(
    products.map(async (product) => {
      const manifest = await readManifest(product);
      const lanes = manifest.gates.reduce(
        (total, gate) => total + Object.keys(gate.lanes).length,
        0,
      );
      return { product, gates: manifest.gates.length, lanes };
    }),
  );

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-10 text-zinc-950">
      <div className="mx-auto max-w-4xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">Review</p>
        <h1 className="mt-2 text-3xl font-semibold">Products under review</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
          These pages are a local, unauthenticated review aid. They show recorded decisions and
          pending questions; they do not grant access and they do not approve anything.
        </p>
        <ul className="mt-6 divide-y divide-zinc-200 rounded-md border border-zinc-200 bg-white">
          {summaries.map((item) => (
            <li key={item.product}>
              <Link
                href={`/review/${item.product}`}
                className="flex items-center justify-between gap-4 px-5 py-4 hover:bg-zinc-50"
              >
                <span className="font-medium">{item.product}</span>
                <span className="text-sm text-zinc-600">
                  {item.gates} gates · {item.lanes} lanes
                </span>
              </Link>
            </li>
          ))}
          {summaries.length === 0 && (
            <li className="px-5 py-6 text-sm text-zinc-600">
              No review manifests yet. Add <code>review/&lt;product&gt;.json</code>.
            </li>
          )}
        </ul>
      </div>
    </main>
  );
}
