# D2 review: risk tiers (`agent-harness@eb42595`)

**Good design. Two required fixes before switch-on.** Verified in the reviewing session: `186 passed in 65.39s`,
and ruff is clean. The D1.2 fixes (`write_nofollow`, validating before the ledger) are correct and tested, and
the seed cards are gone.

These are right:
- tier inputs the container can't change;
- "low" needs positive evidence;
- a corrupt label store fails closed;
- critical and high findings always get the full path;
- the tiers ship off.

## Required 1: deleted and renamed files escape the high tier

`classify` gets its paths from `changed_lines`. That reads `+++ b/<path>` headers, so:
- a **deleted** file (`+++ /dev/null`) never appears;
- a **renamed** file only appears under its new name.

So a ticket that edits `README.md` and deletes `vitest.config.js` or `conftest.py` is classed **low**: "every
changed path is low-risk". Deleting the runner config is exactly the kind of change that quietly changes what
"pass" means.

**Fix:**
- Classify on every path the diff touches, on both sides. Use
  `git diff --no-ext-diff --no-textconv --name-only --no-renames base head` on the trusted repo, with `GIT_SAFE`.
  With `--no-renames`, a rename is listed as a delete plus an add, so both names appear.
- Keep `changed_lines` for the finding filter.
- **Tests:**
  - deleting `conftest.py` alongside a docs change is high;
  - renaming `vitest.config.js` to `docs/old.js` is high;
  - deleting a source file in a docs-only ticket is not low.

## Required 2: agent instruction files are high-risk, not low

The default low glob `*.md` matches `CLAUDE.md`, `AGENTS.md` and `SKILL.md`. Those files steer every later agent
that works on the repo. A change to them is a prompt-injection path into future tickets, so it should never get
the lighter review.

**Add these to `DEFAULT_HIGH_RISK_GLOBS`** (high wins over low, as today):
- `CLAUDE.md`, `AGENTS.md`, `SKILL.md`;
- `.claude/*`;
- CI and build definitions: `.gitlab-ci.yml`, `.github/*`, `Dockerfile`, `Makefile`;
- `harness.toml`.

**Tests:** a ticket changing only `CLAUDE.md` is high; `.claude/settings.json` is high.

## Answers

1. **Switch-on:** approved once both fixes are in. Run three fixture tickets with `[risk] enabled = true`:
   - a docs-only ticket: expect low, with the refuter skipped if the findings are medium-only;
   - one touching `package.json` (or `pyproject.toml`): expect high;
   - one that edits a `.md` file and deletes `conftest.py`: expect high.

   If all three classify as expected, leave it on. Undo is `false`.
2. **`tests/*` as low-risk: no.** You're right that a test-only change can change what "pass" means. Keep it
   standard.

## Note for later (M6, not now)

Labels come from the ticket files in `tickets_dir`, which sits in the container-writable kit folder. A worker
could add a `docs` label before a reload. The impact is small: a low tier only skips the refuter on medium-only
findings, which are notes anyway. Still, when tickets come from Jira, read the labels from Jira on the host.

## Next

The fixes and the switch-on check, report as `D2.1-fixes.md`, then D3.
