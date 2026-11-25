# D4: the JavaScript fixture through the live pipeline (`agent-harness@47c65fa`)

Kit `master` = `47c65fa` (`git ls-remote` confirmed): `262 passed, 3 skipped`, ruff clean (host); the container suite is unchanged by this commit apart from one new test. **No stage was played by hand for JSN-1 and JSN-2**: real triage, planner, implementer (Qwen), host gates, the Qwen finder, the Claude refuter and prover, scribe (DeepSeek). The seeded variant JSEED-2 is the one exception, and says so below.

## What had to be built for a live JS run
`work/fixture-js-repo` is its own repository, so the loader, the gates and the runner needed per-repo configuration: `[repos.fixture-js-repo] overlay = "eval/fixture-js/harness.js.toml"` in both configs (`repos.py`). The loader writes `repo.txt` per run, links the installed dependencies as a `node_modules` link (`.gitignore` is `node_modules`, without the trailing slash: a directory-only pattern does not ignore a symlink and a worker's `git add -A` would have committed it), and words the planner and implementer cards from the overlay; the gatekeeper passes `--overlay <absolute path>` to `harness.gates`; the runner applies the overlay on attach. (Already in D3.1's `0a9479c`.)

## JSN-1 and JSN-2 (real, nothing played by hand)
| | JSN-1 slugify | JSN-2 chunk |
|---|---|---|
| triage, planner, implementer, finder | `qwen3.7-plus`, $0 | `qwen3.7-plus`, $0 |
| gates | passed, 4 valid tests | passed, 5 valid tests |
| tier | standard | standard |
| finder findings / Claude (refuter, prover) | 0 / $0 | 0 / $0 |
| mutation (Stryker 10.1.1, report-only) | engine ran, 11 killed, **5 survived**, 0 unrun, 1.9 s | 14 killed, **4 survived**, 0 unrun, **46.7 s** |
| fix pass | none | none |
| scribe | `deepseek-flash` | `deepseek-flash` |
Scribe cost for both tickets together: **$0.0291**; all Qwen stages $0; Claude $0 (the finder found nothing, so no refuter or prover call was made).
**Score against the hidden tests on the trusted main of `fixture-js-repo`: `jsn1.test.js 4/4, jsn2.test.js 5/5, hidden 9/9, baseline 11/11`** (expected 9/9). The trusted main holds both ticket commits; nothing was approved by hand.
Mutation added 2 s and 47 s to the gates, inside the "about 60 s" the D3 review allowed. The survivors are real: JSN-1's trim regex (AC3) has no test; JSN-2's four are on the validation line.

## The J1-style seeded bug (variant): a real defect found, fixed, and re-run
The bug is `pairs(items)` swapping every pair after the first; the tests are top-level `test()` calls on two items, so the gates pass and only the review sees it. The operator played triage, planner and implementer (`tools/seed_js.py`); everything else was live.
- **JSEED-1: blocked, `blocking_unproven: [F1]`, $0.63.** The Qwen finder found it (high, confidence 100, "reverses the pair order", with the exact failing input) and the Claude refuter said *stands*, but the **model-written JS proof was rejected**: `proofs.json` says `test_id does not belong to test_file`; the prover returned `test_file: tests/pairs-f1.test.js` and `test_id: "pairs (F1) keeps item order in every consecutive pair"`. **Cause (mine):** the prover prompt was Python-shaped: "one new file under `tests/`" and no id format. The JS tests live in `test/`, ids are `file > suite > test`. As designed, an unproven finding blocks and never starts a fix pass. This is exactly the "model-written JS proof has never run" risk the review named.
- **Fix `47c65fa`:** the prover prompt now names the repo's `test_dir`, the `id_kind` and `collect_display` and an `id_example` from the overlay (`commands.test_dir = "test/"` added to the JS overlay). Test: the prompt carries the defaults for Python and the JS values when configured.
- **JSEED-2 (same bug, re-seeded): completed after one pass.** Review 1 ($0.59): the finder found it again; the refuter and prover ran; the proof test `test/pairs-f1.test.js > pairs > keeps element order in every consecutive pair` failed as an assertion, so the finding was **proven** (`blocking: [F1]`). Ledger entry `trigger: review`. The Qwen implementer fixed it in one commit (`fix(pairs): always push [items[i], items[i+1]] in order`, one line in `src/pairs.js`). The retry: gates passed, the host-stored proof passed, the fresh review found 0 findings ($0.0), mutation **9 killed, 0 survived, 1.6 s**, ticket completed, scribe done ($0.0166). Models: Qwen for implementer and finder ($0), Claude for refuter and prover, DeepSeek for the scribe.

## Costs (live)
Qwen $0; DeepSeek scribes $0.0291 (JSN-1/2) + $0.0166 (JSEED-2); Claude $0.63 (JSEED-1, wasted on the prompt bug) + $0.59 (JSEED-2 review 1). Total about $1.27, of which $0.63 was the bug.

## What I want the reviewer to look at
- The model-written JS proof now works with this prompt, but it ran **once** (JSEED-2). The prover also wrote the test **outside** `test/`-style folders the first time; the safe-path check and the id/file check refused it, which is the behaviour we want. Is one live run enough before the FIX Lens pilot, or do you want a second variant?
- JSN-2 spent 46.7 s on mutation for a 7-line file (Stryker's startup plus the per-mutant timeouts); a bigger FIX Lens ticket may hit the `time_cap_s = 300` cap and report `incomplete`.
- The planner and implementer produced Vitest ids in the `file > suite > test` format without trouble; no card-text change was needed.

## State
Seed cards (JSEED-1, JSEED-2) archived; JSN-1/2 cards stay on the board as the evidence. `fixture-js-repo`'s trusted main now has JSN-1, JSN-2 and JSEED-2 commits. `[fixloop]`, `[risk]` and (container) `[mutation]` are on.

## D5 is parked, waiting for the user
The D5 code (host-only kit for the runner, startup guard, deploy tool, unit template; 273 tests) is on a **local branch `d5-host-kit` (`5637d4a`), not pushed and not deployed**. The auto-mode classifier denied the combined step "push, run `tools/deploy_host_kit.py --install-unit`, rewrite `~/.config/systemd/user/harness-reviewer.service`", so I stopped and asked the user instead of routing around it. For about a minute my uncommitted D5 edits were in the live working tree and one runner tick failed (`23:43:49`, nothing on the board needed the gatekeeper then); I moved the work onto the branch and the next tick was a clean `idle; idle`. The `D5-host-kit.md` report follows the user's decision.
