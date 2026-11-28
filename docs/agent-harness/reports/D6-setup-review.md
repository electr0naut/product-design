# D6 setup review (`agent-harness` branch `d6-fixlens` @ `82012ef`)

**Approved, with one small change before the deploy.** Verified in the reviewing session: `280 passed, 3 skipped in
79.37s` (with `-p no:cacheprovider`), and ruff is clean.

- **The repository:**
  - the initial commit is the right shape;
  - the Orchestra files are pinned to `ed111f1` with sha256 sums;
  - `LICENSE` is copied, and the missing `NOTICE` is stated;
  - the exact dependency versions are the ones already proven in D4.
- **The dependencies** are installed in the `deps/` layout before the lockdown, so the user's `sudo` doesn't need
  repeating.
- **The `--hold` card** is a clean way to load without starting: it's unassigned, so it doesn't touch the Hermes
  config, and it has tests.
- **The overlay** is read from the code root only, and its `deps_dir` is under `deps/`, with a test.

## Change before the deploy

**The test-id wording in `eval/fix-lens/harness.fixlens.toml` is copied from the fixture.** It shows a `slugify`
example and the `file > suite > test` form. But the technical design asks for top-level `test()` calls, whose
Vitest ids are `file > test name`. The planner and implementer copy these exact strings into their work.
- Set `id_example = "test/framing.test.js > splits two messages on one line"`.
- Set `id_kind = "Vitest test id (file > test name)"`.
- `collect_regex` already matches both forms.

Commit it to `d6-fixlens`, and deploy that sha after the D5 and D5.1 steps.

## Order (unchanged)

1. The user's D5 deploy.
2. You: the deps move, merge `d5.1-lockdown`, then `d6-fixlens`.
3. Redeploy the host kit at the new `master`.
4. The user's two `sudo` lines.
5. Verify the lockdown, then load the tickets with `--hold`.
6. Release the hold.
7. Per-ticket evidence and a PR comment, as `D6-review.md` says.
