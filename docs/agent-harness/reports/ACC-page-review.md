# Hidden suite: add `acc-page.test.js` before FXL-7 lands

The page's security had no independent hidden test. Copy the new `docs/agent-harness/fix-lens/acceptance/acc-page.test.js`
(4 tests) into `~/.local/state/agent-harness/acceptance/fix-lens/` now, so FXL-7's landing run includes it. If it
fails to collect because of the scoring layout (it reads `index.html` and `src/` from the worktree root), say so on
PR #47 rather than editing it.
