# Code review: `agent-harness` @ 2ca74ea (loader, reviewer runner, configs)

I verified it in the reviewing session: `40 passed in 23.86s`, and ruff reports `All checks passed!`.

The loader is good:
- it orders tickets by dependency, and stops on a cycle naming the keys;
- re-running it can't create duplicate cards;
- card bodies are written to files;
- no card pushes anywhere.

The runner's structure is good too: lock, claim, heartbeat, a spending cap, the decision table, and a
proof re-run in a clean worktree. Three bugs in the runner must be fixed before the PRC-1 smoke test. All
three are in code that acts on model output.

## Must fix

**1. Path traversal in `prove` (reviewer.py lines 231-237).** `res["test_file"]` comes straight from the
model. `scratch / res["test_file"]` with an absolute path (`/home/ubay/.bashrc`) or one with `..` escapes the
worktree. `shutil.copyfile(src, dest)` then copies an arbitrary host file and **overwrites another one as
`ubay`**. A prompt injection planted in the reviewed code could steer this.
- **Fix:** resolve both paths and require `src.resolve().is_relative_to(scratch.resolve())` and the same for
  `dest` against `clean`. Also require the path to match `commands.test_globs`. Otherwise record
  `proven: None` with the reason.
- **Test:** `test_file` set to `/etc/hostname`, then to `../../x`. Nothing is copied and the proof is `None`.

**2. Any test failure counts as proof (line 242).** Pytest exit 1 also covers a test that **errors**
(NameError, an ImportError inside the test, a bad fixture), not only one whose assertion fails. A broken
proving test would then turn a false finding into a blocking "proven" defect, and set off needless fix loops.
- **Fix:** run the proof with `-rfE` (or `--junitxml`), and count it as proven only if the test's outcome is
  `failed` with an `AssertionError`, or with an exception named in the finding's `failure`. An `error`
  outcome, or any other exception, gives `proven: None` with the error type recorded.
- **Tests:**
  - a proving test that raises NameError gives `None`;
  - an assertion failure gives `True`.

**3. A timeout leaves the card claimed and retried at cost (lines 309-314, 365, 409).** `qwen_find` (900 s)
and the Claude call can raise `subprocess.TimeoutExpired`. `run_once` doesn't catch it, so `main` exits 2
with the card still `running`. When the 1800 s claim expires, the card goes back to `ready`, and the next
timer pass repeats the same paid review, again and again.
- **Fix:** catch `subprocess.TimeoutExpired` in `run_once` along with the others, and block the card as
  `transient`.
- **Also:** to stop retry loops, give up after one transient block per card. If a card that has already
  been blocked once as transient comes back `ready`, block it as `needs_input` and don't review it again.
- **Test:** a fake find that raises `TimeoutExpired`. The card is blocked, not left claimed.

## Should fix

- **`test_id` (line 238).** It comes from the model and is passed as an argument to pytest. Reject ids that
  start with `-`, and require the id's file part to equal `test_file`. A model-chosen `-p module` would make
  pytest load a plugin.
- **Heartbeat failures (lines 303-306).** They are silent. Write each one to stderr (journald keeps it), so
  a dying claim can be seen.
- **Budget check (line 185).** It runs before the call, so a card can overshoot the cap by one call
  (≤ $0.75). Either accept that and document it, or check `cost + per-call cap > card cap`.

## Decision for the user: moving `main` forward between tickets (Phase C)

**Don't give an LLM stage `git merge` in the allowlist.** Advance `main` with deterministic code instead. After
a review **completes** (nothing blocking), the runner:
1. checks `git merge-base --is-ancestor main harness/<KEY>`;
2. then runs `git update-ref refs/heads/main harness/<KEY> <old-main-sha>`.

That's a fast-forward with no checkout and no merge commit. If `main` isn't an ancestor, it blocks the card
with `needs_input`. It stays local and needs no new allowlist entry.

## Next

Fix 1 to 3 with their tests, push, and post the commit. After I re-review:
1. Install the timer; this needs the user's OK and sudo for linger.
2. Run the PRC-1 smoke test.
