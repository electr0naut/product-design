# FIX Lens hidden acceptance suite

Written by the reviewer from the PRD v1.1 and technical design v1.1, with FIX reference values computed
independently (Python, CheckSum and BodyLength over SOH). **Never shown to the implementing agents.** Copied to
host-only state and run with `harness.score` against the trusted `main` after every ticket (see `D10-review.md`).

Files for features not built yet fail at import; that is expected. A test that passed once must never fail later.
Each file carries its own small message builder (`fixmsg`), computed over SOH, independent of the product's
helper.

## Baseline (reviewer, 2026-11-26, against FXL-3 + FXL-1 + FXL-2 rebuilt from their patches)

- `acc-framing`: 4 of 9 pass. The failures are the FXL-1 deviations FXL-1b fixes: no `end`, `offset` instead of
  `position`, a prefix with `=` hiding the message, and a candidate without CheckSum dropped.
- `acc-check`: 4 of 9 pass. The failures: CheckSum over pipe bytes (FXL-2b), UTF-8 BodyLength on a pipe line (the
  same CheckSum cause), and a missing or malformed CheckSum not reaching `checkMessage` (FXL-1b).
- `acc-dictionary`: 1 of 4 pass. The argument order is reversed (FXL-3b). Calling it with the current order
  instead, every expected value is right (`SenderCompID`, `Buy`, `ExecutionReport`, `Trade` in 4.4 only,
  `Logon`), which confirms the suite's values against the real Orchestra data.
- `acc-decode`, `acc-timeline`, `acc-limits`, `acc-analyse`: not built yet.

After FXL-1b, FXL-2b and FXL-3b land, `acc-framing`, `acc-check` and `acc-dictionary` should pass in full.

`acc-page.test.js` (added before FXL-7 landed) checks the page independently: one exact CSP meta first in
<head>, the textarea attributes, no inline script/style/handlers, and no network, storage, logging or unsafe-markup
API in `src/`. It expects to run from the repo root with `index.html` at the root.

## v1.2 (reviewer, 2026-11-27, for tickets FXL-9 to FXL-16)

Written from PRD v1.2 and technical design v1.2. The fixed messages and the trading-summary figures were computed
in Python, independently of the product code.

| File | Ticket | Tests |
|---|---|---|
| `acc-delimiters.test.js` | FXL-9 | 14 |
| `acc-framing-rules.test.js` | FXL-9 (added after it landed) | 11 |
| `acc-events.test.js` | FXL-10 | 11 |
| `acc-orders.test.js` | FXL-11 | 10 |
| `acc-summary.test.js` | FXL-12 | 17 |
| `acc-filters.test.js` | FXL-13 | 8 |
| `acc-presentation.test.js` | FXL-14 | 21 |
| `acc-order-story.test.js` | FXL-15 | 12 |
| `acc-trades.test.js` | FXL-16 | 14 |

**Checked before use.** A second agent built v1.2 from the design alone, without seeing this folder. Against that
build, 99 of the 102 new tests passed at once. The other three were places where the design is silent and the
tickets pin the behaviour (no empty `span.order-state`, the size warning as `p.warning`, a net that rounds to
zero written `0`); with those three behaviours added, all 102 pass. Five more tests were then added for points that
agent's report showed were open (the hidden `<main>`, banner parts, and four trading-summary rules), 107 in all;
with those behaviours added to the build as well, all 107 pass, together with the 54 v1.1 tests that stay. The page files (`acc-presentation`,
`acc-order-story`, `acc-trades`) run in jsdom from the repo root and also drive `src/main.js` through the page.

**v1.1 tests that v1.2 changes on purpose.** Run against the v1.2 build, 54 of the 59 v1.1 tests still pass. The
five that do not are retired with the harness's `retire_hidden` decision, never by editing host state by hand:

| Retire before | Test | Why | Replaced by |
|---|---|---|---|
| FXL-9 is loaded | `acc-check.test.js` > `bad tags` | with a pipe, `\|ab=x` is no longer a field boundary | the test with the longer title in the same file |
| FXL-9 is loaded | `acc-timeline.test.js` > `event keys` | events gain `origClOrdId` and `execRefId` | `acc-events.test.js` > `event keys include origClOrdId and execRefId` |
| FXL-14 is loaded | all five tests of `acc-render.test.js` | they describe the v1.1 page; three fail on the v1.2 page and two depend on its old structure | `acc-presentation.test.js`; the file is then deleted from this folder |

**Order of operations.** Refresh the host copy and retire the first two tests, then load FXL-9 to FXL-13. After
FXL-13 lands: retire the five `acc-render` tests, delete the file here, refresh, then load FXL-14 to FXL-16. The
two replaced tests in `acc-check` and `acc-timeline` already pass on the v1.1 code, as do all 59 tests of the
folder as it stands.

## Added after FXL-9 landed: `acc-framing-rules.test.js`

Mutation testing of FXL-9 left 70 mutants of `src/framing.js` alive. Applied one by one and compared on generated
pastes, 44 change behaviour, and the suite as it was caught 5 of them (`reports/FXL-9-survivors-classified.md`).
This file holds the rules the design pins and nothing was holding: a delimiter followed by digits without `=`,
or by `=` without digits, a delimiter at the end of the text, `8=FIX` after a digit, a tag with a letter after
its digits, a CheckSum of the wrong length, the header order and where its error points, a BodyLength that is
not a number, the position of a missing CheckSum, and the shape of every error text. It passes on the landed
code and on the independent build, and with it 23 of the 44 are caught. Of the other 21, 12 are in places the
design does not pin, 1 changes only a wording, and 8 are edge cases of detecting `^A` and `<SOH>`.

It reaches the host copy with the next `refresh_copies`, in the commit that retires the `acc-render` tests.
