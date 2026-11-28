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
| `acc-summary.test.js` | FXL-12 | 18 |
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

## Added with design v1.2.2: one test in `acc-summary.test.js`

`a report that names an unmatched report which made no execution is unmatched too (design v1.2.2)` pins the
reading Ubay Gonzalez chose on 2026-11-27 ("A"). Its figures were worked by hand from section 13. It passes on
the landed FXL-12 code and fails, as it should, on the independent build's first reading. It reaches the host
copy, together with the design copy, with a `refresh_copies` sent when no card is running.

## v1.3 (reviewer, 2026-11-27, for tickets FXL-19 to FXL-21)

Written from PRD v1.3 and technical design v1.3 (sections 4, 9 and 16). Every expected number follows from how
each test builds its log.

| File | Ticket | Tests |
|---|---|---|
| `acc-limits.test.js` | FXL-19 | 4 (three new, replacing two) |
| `acc-analyse.test.js` | FXL-19 | 4 (one replaced) |
| `acc-presentation.test.js` | FXL-19 | 21 (one replaced) |
| `acc-performance.test.js` | FXL-19 | 2 |
| `acc-paging.test.js` | FXL-20 | 14 |
| `acc-pager.test.js` | FXL-21 | 24 |

The folder now holds 20 files and 214 tests.

**Checked before use.**
- **Two builds.** The reviewer's own build of v1.3 and a second build made by another agent from the three
  tickets and the design alone, without seeing this folder. All 214 tests pass on both, first time on the
  second build. Its report named four loose points in the tickets (which old-limit lines move, the size of the
  padding, the sequence numbers of AC8, where a SequenceGap row goes); the tickets were tightened.
- **v1.2 as landed.** 171 tests pass. The 43 that fail are new: 3 in `acc-limits`, 1 in `acc-analyse`, 2 in
  `acc-performance`, the 14 of `acc-paging` (the module is not there) and 23 of the 24 in `acc-pager` (the one
  that passes says a log of 200 messages has no pager).
- **Deliberate breaks.** 33 single changes to the reviewer's build (the timeline not paged, the trading summary
  or the filter lists following the page, a missing or misplaced pager, each of the four returns to page 1, the
  scroll missing or unguarded, off-by-one buttons, the limits one off, bytes counted as characters, a bare
  `toLocaleString()`, and others). Each makes at least one test fail.
- **A real browser** (Chromium, both themes, 1280 and 375 pixels wide), on the reviewer's build with 10,000
  messages, plain and padded to 10.4 MB: the first page is painted 0.7 to 1.3 seconds after Decode, a page
  change takes 0.2 to 0.4 seconds, a filter change under 0.4 seconds, and the page never scrolls sideways.

**v1.2 tests that v1.3 changes on purpose.** Four tests pinned the old limits. They are retired with a
`retire_hidden` decision before FXL-19 is loaded, and replaced in the same files:

| Test | Replaced by |
|---|---|
| `acc-limits.test.js` > `byte limit is UTF-8 and inclusive at 1,048,576` | `byte limit is UTF-8 and inclusive at 10,485,760 (v1.3)` |
| `acc-limits.test.js` > `message limit: 1,000 accepted, 1,001 refused, warning names both numbers` | `message limit: 10,000 accepted, 10,001 refused, warning names both numbers (v1.3)` |
| `acc-analyse.test.js` > `over a limit nothing is decoded` | `at the v1.3 limit everything is decoded, over it nothing is` |
| `acc-presentation.test.js` > `empty states and the size warning` | `empty states and the size warning at the v1.3 limit` |

**Expected files** (`[expected_hidden.fix-lens]` in the kit's `harness.host.toml`, D24): FXL-19 `acc-limits`,
`acc-analyse`, `acc-presentation` and `acc-performance`; FXL-20 `acc-paging`; FXL-21 `acc-pager`.

**Order of operations.** Retire the four tests and refresh the host copy; deploy the kit commit that adds the
three lines to the table; then load FXL-19 to FXL-21.

## v1.4 (reviewer, 2026-11-27, for tickets FXL-22 to FXL-26)

Written from the PRD v1.4 and technical design v1.4 drafts (sections 3, 7, 8.2, 12 and 13), for the seven
findings of the validation of 2026-11-27 that Ubay Gonzalez put into phase 1 ("as recommended", 2026-11-27).
He approved the wording of both on 2026-11-27 ("v1.4 approved"). Every expected
value follows from who sends each message and from the rules of the design, never from the product.

| File | Ticket | Tests | Finding |
|---|---|---|---|
| `acc-parties.test.js` | FXL-22 | 17 | FL-01, FL-02 (ids within their parties), `findOrder` by message |
| `acc-executions.test.js` | FXL-23 | 15 | FL-01 (two venues, same OrderID and ExecID), FL-04 (cancel before its fill) |
| `acc-restart.test.js` | FXL-24 | 11 | FL-05 (a Logon numbered 1 restarts the count) |
| `acc-single-byte.test.js` | FXL-25 | 9 | FL-13 (single-byte text outside ASCII) |
| `acc-pick.test.js` | FXL-26 | 11 | FL-03 (the button opens the order of its message), FL-15 (a half rounds away from zero) |

The folder now holds 25 files and 277 tests.

**Checked before use.**
- **The reviewer's build of v1.4.** All 277 pass.
- **A second build, made from the tickets and the design alone** (another agent, which saw neither the
  reviewer's build nor these tests). All 277 pass. The points it found loose in the tickets are now written
  into FXL-22, FXL-23, FXL-24, FXL-26 and the design; on each of them the two builds already agreed.
- **v1.3 (the reviewer's build).** 236 pass. The 41 that fail are all in the five new files: 13 in
  `acc-parties`, 10 in `acc-executions`, 4 in `acc-restart`, 5 in `acc-single-byte` and 9 in `acc-pick`.
- **One ticket at a time.** On v1.3, adding the v1.4 `src/orders.js` makes `acc-parties` pass and nothing else
  fail; `src/summary.js`, `src/timeline.js` and `src/framing.js` each make exactly their own file pass, in any
  order; `acc-pick` needs FXL-22 and FXL-26.
- **The validation's own corpus,** on the reviewer's build: of its 106 hand cases 86 pass (78 on v1.3), and the
  8 that changed are the cases of the seven findings; its 88 dataset checks give the same verdicts as on v1.3;
  its property tests PB-01 to PB-07 pass (PB-06 failed on v1.3). Its page check needed one line of its own
  handler changed to pass the message number on; that was done in a scratch copy.
- **Deliberate breaks.** 55 single changes to the reviewer's build (the client or the executing party read
  from the wrong tag, a cancel reject read as sent by the client, an id without its party, the two parts of a
  key run together, `findOrder` ignoring the number or giving up without it, executions keyed without their
  sender, one pass instead of two, a correction taking its own number, any message numbered 1 restarting, both
  directions restarting, the length or the checksum alone accepting single-byte text, characters above U+00FF
  let in, a button without its number, the old rounding, a half rounded down or to even, the sign lost, and
  others). 53 make at least one test fail; two tests were added for breaks missed at first (a missing party
  written as a word, 12 significant digits instead of 15). The other two change nothing that can be seen: the
  list of executions is already in log order when it is sorted, and a view that kept the number of an earlier
  click can't be reached, because a selected order shows only its own buttons.

**Existing tests changed, none retired.** The fixtures of `acc-orders.test.js` sent every report in the
direction of its order, and those of `acc-performance.test.js` spread one order over two pairs of CompIDs,
which no real log does and which the party rule reads as different parties. The fixtures now send types 8 and 9
from the executing party, and choose the pair per order. Test names and expected values are unchanged, and both
files pass on v1.3 and on v1.4, so no `retire_hidden` is needed.

**Expected files** (to add to `[expected_hidden.fix-lens]` in the kit's `harness.host.toml`, D24): FXL-22
`acc-parties`; FXL-23 `acc-executions`; FXL-24 `acc-restart`; FXL-25 `acc-single-byte`; FXL-26 `acc-pick`.

**Order of operations.** After the approval of the v1.4 wording, and once FXL-19 to FXL-21 have landed and no
card is running: refresh the host copy; deploy the kit commit that adds the five lines to the table; then load
FXL-22 to FXL-26.
