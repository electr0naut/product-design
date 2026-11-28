const phases = [
  {
    id: "01",
    name: "Ideation",
    path: "01-ideation/",
    output: "Completed idea canvas",
  },
  {
    id: "02",
    name: "Analysis",
    path: "02-analysis/",
    output: "Role-specific reviews",
  },
  {
    id: "03",
    name: "BRD",
    path: "03-brd/",
    output: "Business requirements",
  },
  {
    id: "04",
    name: "PRD",
    path: "04-prd/",
    output: "Product requirements",
  },
  {
    id: "05",
    name: "Technical Design",
    path: "05-technical-design/",
    output: "Architecture and specs",
  },
  {
    id: "06",
    name: "Backlog",
    path: "06-backlog/",
    output: "Traceable user stories",
  },
  {
    id: "07",
    name: "Implementation",
    path: "07-implementation/",
    output: "Implementation plan",
  },
];

const commands = [
  "cp 01-ideation/templates/idea-canvas.md 01-ideation/my-product.md",
  "python shared/scripts/generate_analysis.py --idea 01-ideation/my-product.md",
  "python shared/scripts/generate_brd.py --idea 01-ideation/my-product.md --analysis 02-analysis/",
  "python shared/scripts/generate_prd.py --brd 03-brd/my-product-brd.md",
  "python shared/scripts/generate_technical_design.py --prd 04-prd/my-product-prd.md",
  "python shared/scripts/generate_stories.py --prd 04-prd/my-product-prd.md --technical-design 05-technical-design/architecture/my-product-technical-design.md",
  "python shared/scripts/validate_backlog.py --brd 03-brd/my-product-brd.md --prd 04-prd/my-product-prd.md",
  "python shared/scripts/scaffold_code.py --technical-design 05-technical-design/architecture/my-product-technical-design.md",
];

export default function Home() {
  return (
    <main className="min-h-screen bg-stone-50 text-zinc-950">
      <section className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
              Product Design Template
            </p>
            <h1 className="mt-3 text-4xl font-semibold tracking-normal text-zinc-950">
              Clone once per product, then generate each phase from the last.
            </h1>
            <p className="mt-4 max-w-xl text-base leading-7 text-zinc-600">
              Edit the markdown documents in order. Each script combines the
              previous approved phase, the matching prompt, and the target
              template to draft the next artifact.
            </p>
          </div>
          <div className="rounded-md border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-700">
            <span className="font-semibold text-zinc-950">Current step:</span>{" "}
            start with <code>01-ideation/templates/idea-canvas.md</code>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[1fr_420px]">
        <div>
          <h2 className="text-lg font-semibold text-zinc-950">Lifecycle</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {phases.map((phase) => (
              <article
                key={phase.id}
                className="rounded-md border border-zinc-200 bg-white p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-cyan-700">
                      {phase.id}
                    </p>
                    <h3 className="mt-1 text-base font-semibold">
                      {phase.name}
                    </h3>
                  </div>
                  <code className="rounded bg-zinc-100 px-2 py-1 text-xs text-zinc-700">
                    {phase.path}
                  </code>
                </div>
                <p className="mt-4 text-sm leading-6 text-zinc-600">
                  {phase.output}
                </p>
              </article>
            ))}
          </div>
        </div>

        <aside className="rounded-md border border-zinc-200 bg-zinc-950 p-4 text-zinc-100">
          <h2 className="text-lg font-semibold">Command Order</h2>
          <ol className="mt-4 space-y-3">
            {commands.map((command) => (
              <li key={command}>
                <code className="block overflow-x-auto rounded bg-white/10 px-3 py-2 text-xs leading-5 text-zinc-100">
                  {command}
                </code>
              </li>
            ))}
          </ol>
        </aside>
      </section>
    </main>
  );
}
