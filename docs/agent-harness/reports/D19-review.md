# D19: retire hidden tests on purpose, and refresh the host copies from a named commit (instruction)

**Priority:** after FXL-8 lands and the bake-off runs finish. Build on a branch; I review; the user deploys
between tickets. Include the D18 test id fix (`pytest.param(..., id="deep-nesting")`).

**Why:** two things in the kit will stop the next FIX Lens tickets, which change the page's DOM.

- `harness.acceptance` counts a hidden test that vanished as a regression, and nothing can take a test out of
  the history. When I replace the `acc-render` tests for the new presentation, the queue holds, and the only
  way out is a hand edit of host-only state.
- The host copies of the technical design and the hidden suite are copied by hand. Nothing records which
  version they are, so a spec pass can review against an old design without anyone seeing it.

## 1. Decision action `retire_hidden`

`{id, action: "retire_hidden", key, tests: [<exact hidden test ids>], reason}`.
- Each id must be in the acceptance history's `passed` list for that repository, or the decision is rejected
  whole. No globs.
- The runner removes those ids from `passed` and appends `{id, tests, reason, at}` to a `retired` list in the
  same history file. A retired id that passes again later is simply a pass.
- A regression report names retired ids separately, so a retirement never hides a real regression in another
  test.

## 2. Decision action `refresh_copies`

`{id, action: "refresh_copies", key, commit: <40 hex>, reason}`.
- The runner reads from its host-only mirror of the decisions repository, at exactly that commit, never from a
  worktree: the paths listed per repository in the reviewed config (for `fix-lens`: the technical design and the
  `acceptance/` folder).
- It writes them to the host-only `specs/` and `acceptance/` folders, replacing what is there, and writes the
  workers' reading copy of the design. It records the commit and a sha256 per file in host-only state.
- The commit must be an ancestor of the fetched branch head. A file missing at that commit rejects the decision.
- **Every review records what it read:** `review.json` gets the commit and the design's sha256. The acceptance
  summary gets the commit and the hidden file count. A copy whose sha256 no longer matches the recorded one
  blocks the review `needs_input`.
- Refuse `refresh_copies` while a card of that repository is running; it applies on a later pass.

## 3. Tests

Retire: unknown id rejected; ids removed and logged; a different vanished test still reports a regression.
Refresh: content comes from the commit, not a worktree; a non-ancestor commit is rejected; a tampered copy
blocks; the recorded commit appears in `review.json`; refused while a card runs.

Report as `D19-retire-refresh.md` with the branch sha and the test output.
