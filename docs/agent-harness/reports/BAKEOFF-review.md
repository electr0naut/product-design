# Implementer bake-off on the Alibaba token plan (instruction; runs beside FIX Lens, touches nothing live)

**Goal:** find out whether a model on the user's token plan implements as well as Codex, so that Codex quota can
be saved for planning. Compare them on a ticket whose correct outcome is already known.

**Candidates,** from the plan's model list the user pasted on 2026-11-26:
- `qwen4-max`
- `qwen3.8-max`
- `qwen3.7-max`
- `deepseek-v4-pro`
- `glm-5.3`

The baselines are already known: `qwen3.7-plus` failed FXL-1B twice, and `gpt-6-sol` (Codex) passed the gates
first time. Use the exact model ids your provider config accepts. If one isn't reachable through the configured
provider, skip it and say so.

## Setup (all throwaway; approved as reversible)

- **One temporary Hermes profile per candidate** (`bake-<model>`), copied from `implementer`, with that model as
  the default and **no fallbacks**, so a failure is a failure and not a silent switch. Delete them all at the
  end.
- **A scratch clone of `fix-lens`** at FXL-1B's base, the trusted main FXL-1B attempt 3 started from, and a
  **scratch trusted root**, as in D0. Never use the live board, the live trusted repo, or `work/fix-lens`.
- **The same inputs for every candidate:**
  - the FXL-1B ticket text;
  - the stage card body the loader writes for the implementer;
  - **Codex's `plan.json` from attempt 3,**

  so only the implementer differs.

## Per candidate, two runs each (models vary from run to run)

1. Run the implementer card with `hermes -p bake-<model>`, in its own scratch worktree. Time limit: 30 minutes.
2. Run `harness.gates` inside the container, on that head, with the FIX Lens overlay.
3. Run the hidden acceptance suite (`acc-framing` and `acc-check`) against that head, with `harness.score` or the
   acceptance runner pointed at the scratch trusted root.
4. **No Claude review.** This costs only plan tokens. Run at night if the discounts apply and the timing allows.

## Report as `BAKEOFF.md`

One row per run:
- model;
- whether the gates passed first time, plus `missing_acs`;
- `acc-framing` passed out of 9;
- `acc-check` passed out of 9 (the baseline at FXL-1B's base, for reference);
- the base test files it touched;
- minutes;
- tokens, from `state.db`.

Add one line on anything odd: loops, timeouts, ignored instructions.

**Don't change the live implementer profile.** I'll recommend the choice from the results, and the user decides.
