import Link from "next/link";
import { listRoles } from "@/lib/review";

export default async function ProductReview({
  params,
}: {
  params: Promise<{ product: string }>;
}) {
  const { product } = await params;
  let roles: string[] = [];
  let error = "";
  try {
    roles = await listRoles(product);
  } catch {
    error = "No review manifest for this product.";
  }

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-10 text-zinc-950">
      <div className="mx-auto max-w-4xl">
        <Link href="/review" className="text-sm text-cyan-700 underline">
          All products
        </Link>
        <h1 className="mt-3 text-3xl font-semibold">{product}</h1>
        <p className="mt-2 text-sm text-zinc-600">Choose the role you are reviewing as.</p>
        {error ? (
          <p className="mt-6 rounded border border-amber-300 bg-amber-50 p-4 text-sm">{error}</p>
        ) : (
          <ul className="mt-6 grid gap-3 sm:grid-cols-2">
            {roles.map((role) => (
              <li key={role}>
                <Link
                  href={`/review/${product}/${role}`}
                  className="block rounded-md border border-zinc-200 bg-white px-5 py-4 hover:bg-zinc-50"
                >
                  <span className="font-medium capitalize">{role}</span>
                  <span className="mt-1 block text-sm text-zinc-600">Open the review queue</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
