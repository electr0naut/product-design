# D6 setup: FIX Lens repository, dependencies, overlay branch, tickets staged (nothing started)

Per the D6 instruction, the tickets do not start until the user has run the D5 deploy and the D5.1 `sudo` lines and I have verified the renames are refused. That has **not** happened yet (the deploy is still waiting for the user; see D5.1-lockdown.md). So this is the setup, and then I stop.

## 1. The repository: `/srv/lab/agent-harness/work/fix-lens` (initial commit `544c8c5`, made as the operator, branch `main`)
- `package.json`: `"type": "module"`, exact versions: `vitest 5.1.2`, `@stryker-mutator/core 10.1.1`, `@stryker-mutator/vitest-runner 10.1.1` (the D4 versions), `jsdom 31.0.1` (current; its engines accept the container's Node 26.12.1).
- `.gitignore`: `node_modules` (no trailing slash), `reports/`, `.stryker-tmp/`.
- `vendor/orchestra/`: `OrchestraFIX42.xml` (672 357 bytes) and `OrchestraFIX44.xml` (1 517 010 bytes), copied unchanged from `github.com/FIXTradingCommunity/orchestrations`, folder `FIX Standard`, at the **current commit of the default branch (`master`): `ed111f1bd84bb4e7209e52f939aefe83b86cbc7f`** (2026-11-18, "Corrected EP313 pedigree"); the repository's top-level `LICENSE` (Apache License 2.0; the repository has **no NOTICE file**); `SOURCE.md` naming the commit sha, the two source paths and the sha256 of both files.
- `README.md`: one line.
It is a plain local git repository; nothing else was written to it.

## 2. Dependencies: `/srv/lab/agent-harness/deps/fix-lens/node_modules`
Installed as `hermes` in the container with `npm install --ignore-scripts` (235 packages); `vitest --version` = 5.1.2, `stryker --version` = 10.1.1, `jsdom` present. They are installed in the D5.1 layout (`deps/`, not `work/`) and **before** the lockdown, as the instruction said; after the user's `sudo` lines a reinstall needs `sudo` (a stop). They are still owned by `ubay` today.

## 3. The overlay (a kit change, for review): branch `d6-fixlens` @ `82012ef`
Stacked on `d5.1-lockdown` (`9e27bd5`), which is on kit `master` (`441ef62`). **Pushed as a branch only; not merged, not deployed.**
- `eval/fix-lens/harness.fixlens.toml`: the same Vitest commands and `test_dir = "test/"` as the D4 JS overlay, `deps_dir = "/srv/lab/agent-harness/deps/fix-lens/node_modules"`, `[mutation] engine = "stryker"`.
- `[repos.fix-lens]` registered in `harness.toml` and `harness.host.toml`, so the runner accepts `work/fix-lens` in a run's `repo.txt`, and the overlay is read from the code root (host kit) only.
- **Loader `--hold "<reason>"`** (new): creates one unassigned card, `HOLD: <reason>`, which the first ticket's triage waits for. The tickets sit on the board in order, with their `blocked_by` links, and nothing starts until I complete the hold card; nobody can work an unassigned card, so the dispatcher cannot pick it up. It's how I satisfy "load the tickets, don't start the dispatcher on them" without touching the Hermes config. Without `--hold` nothing changes.
- Tests: 5 new (registry and overlay values, `deps_dir` under `deps/` for the new overlay too, hold card is unassigned and is a parent of only the first triage, no extra card without a hold). Branch from a fresh clone: **`280 passed, 3 skipped`**, `ruff check` and `ruff format --check` clean.

## 4. The tickets (copied unchanged)
`FXL-1.md` to `FXL-7.md` are copied byte for byte to `/srv/lab/agent-harness/work/fix-lens-tickets/` (checked with `cmp`). They parse, and the loader's order is: FXL-1, FXL-2, FXL-3, FXL-4, FXL-5, FXL-6, FXL-7 (FXL-4 after FXL-1 and FXL-3; FXL-7 after FXL-2, FXL-4, FXL-5, FXL-6; FXL-7 carries label `security`, which is a high-risk label in the config). I have not audited them against the technical design; nothing in them stopped the load. They will be loaded with `--hold` once the deploy has made the new loader and registry live.

## Not done, and why
- **Tickets not loaded:** the loader runs from `/srv/lab/agent-harness`, which still has the old registry (no `fix-lens`) and no `--hold`; loading before the reviewed overlay is deployed would either fail or use the wrong config.
- **Not deployed:** the overlay branch needs the review, then the deploy to the host kit and the container copy as D5 describes. Both the D5 deploy and the lockdown are the user's steps.
- **Dispatcher untouched; Hermes config untouched; no sudo.**

## What I need
1. The user runs the D5 deploy line, then the `sudo` lines (D5.1-lockdown.md has them in order). 2. A review of `d6-fixlens`. Then I deploy the reviewed sha, load the tickets with `--hold`, verify the renames are refused as `hermes`, and release the hold.
