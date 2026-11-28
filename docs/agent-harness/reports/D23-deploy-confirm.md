# `6c483e6` is deployed: a correction, the confirmation, and the FXL-9 rerun still to do

## Correction
My PR comment and handoff edit of about 13:42 said **"Not deployed: the host kit is still 7c190a2". That was wrong.** The same command that posted it printed the host kit at `6c483e6`; I had written the text beforehand and did not wait to read the output. **`6c483e6` is deployed.** I ran no deploy command; it is Ubay's step, and I assume Ubay ran it.

## When, and what was running
| time (13:xx) | event |
|---|---|
| 36:19 to 40:53 | FXL-12 scribe |
| 40:44 to 41:25 | a runner pass, **in progress during the deploy** |
| 40:59 | gate `accept FXL-12` completed |
| **41:18** | **host kit checked out `6c483e6`; the container copy fast-forwarded the same second** |
| 41:20, 41:23 | that pass published FXL-12's evidence and `STATE.md` |
| 41:23 | FXL-13 triage started |
| 42:15 | first full pass logged at `6c483e6`: ok |

- **No worker card was running at 41:18** (the gap from 40:59 to 41:23).
- The pass that spanned it logged `7c190a2` and ended normally; FXL-12's evidence and state were published, the outbox is empty, and the runner reports ok with no failures. I have not checked whether that pass imported any module after the checkout.
- `D23-code-review.md` says to deploy "when I confirm no card is running". I see no such confirmation in the repository; it may have been given elsewhere. **FXL-13's cards, triage included, run on the new kit,** so its mutation step will be the first gate run with the source-text list and the static count.

## Confirmation (read-only)
- Host kit `6c483e6`. Its 154 tracked files are byte-identical in the container copy, whose `master` is `6c483e6`.
- Host: a fresh-process import of each of the 28 `harness` modules: all succeed. `tools/rerun_mutation.py --help`: exit 0.
- Container: `harness.mutation` and `harness.gates` import (`IGNORE_STATIC` true), and `python -m harness.mutation --help` works.
- The container's config has `source_text_tests = ["test/static-checks.test.js"]`, and that file exists on `fix-lens` trusted `main`.

## `rerun_mutation.py FXL-9`: not run yet
FXL-13 is running. The tool refuses while a card is running, but it checks only at the start, so I will not slip it into a gap between FXL-13's cards: a worker could start mid-run, share the CPU with it (mutation runs under a time cap) and reach its result file. **I will run it after FXL-13 lands,** when no card is running, and report the counts and the raw report's path.
