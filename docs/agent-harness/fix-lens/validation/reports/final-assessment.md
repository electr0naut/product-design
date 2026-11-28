# Final production-readiness assessment

FIX Lens v1.2, validated on 2026-11-27 against the scoped brief. Evidence for every statement is in
`test-matrix.md`, `results.json`, `defects.md` and `benchmark-results.csv`.

## Verdict: NOT PRODUCTION READY

Two confirmed P0 defects are unresolved (FL-01, FL-02), and the brief rules that this prevents a
production-ready verdict. Both concern a use the PRD advertises: a pasted log that holds more than one
session ("a shared log", US-009).

The verdict is narrower than it sounds, and the evidence supports saying so:

- **On a log of one session** (one client, one venue), every result was right apart from one rounding case
  (FL-15): about 9,500 generated and engine-written messages, FIX 4.2 and 4.4, with every lifecycle path,
  trade cancels and corrections, resends and gaps, compared with an independent decimal ground truth.
- **The decode, the framing checks and the privacy rules are solid.** Identical accept/reject verdicts to the
  QuickFIX parser on 1,184 valid and damaged messages and on 1,042 messages of QuickFIX's own acceptance
  definitions; 16 representations of the same traffic give the same result; hostile markup stays text.

**It would be CONDITIONALLY READY** for FIX support technicians if either of these is done:

1. FL-01 and FL-02 are fixed (order and execution identifiers scoped by session; the PRD clauses AC-035 and
   AC-041 changed first), with FL-03 and FL-04, which touch the same code; or
2. until then, the tool is offered for **one session per paste**, with a visible line on the page such as
   "Paste one session at a time: order grouping, the Account filter and the trading summary are not reliable
   when a log holds several sessions", and technicians are told that "0 sequence gaps" says nothing after a
   session restart (FL-05).

The PRD already makes deployment wait for a test with the support team's real logs. That test is still
needed and could not be done here (BL-02).

## Scores

0 is unusable, 10 is no reservation. Each score is for the advertised scope only.

| Category | Score | Evidence | Limits of the evidence |
|---|---:|---|---|
| Protocol correctness | 7 | Dictionary equal to the pinned Orchestra files (DICT-42-01, DICT-44-01). FIX 4.2 ExecTransType and FIX 4.4 ExecType handled apart and correctly (S04-03, S07-04, S11-04). | Multiple-value fields (FL-14), number formats (FL-10), single-byte text (FL-13). No field-level validation, by scope. |
| Parsing reliability | 9 | 36 of 46 malformed-input cases right, with message number, position and rule; QuickFIX differential DF-01; properties PB-01 to PB-05; 48 format-equivalence checks; real clipboard paste keeps SOH (BR-03). | A message without BeginString vanishes (FL-12). Only Chromium. |
| Session reconstruction | 5 | Right on clean sessions, on the engine logs (the engine's own gap, resend request and gap fill: EN-42-02, EN-44-02) and on 13 of 21 hand-built session cases. | Wrong after a restart without 141=Y, with SubID sessions, for too-low numbers, for a PossDup at the expected number (FL-05, FL-06, FL-07, FL-09). |
| Order lifecycle reconstruction | 6 | Every one of 219 simulated and 26 engine-made orders grouped with its amendment chain; selection and banner right for 137 orders checked (DS-…-04, -06); engine logs EN-…-04. | Merged across sessions (FL-02); wrong order on an ambiguous id (FL-03); stale state after a resend (FL-11). |
| Execution and quantity accuracy | 6 | Bought, sold, averages and net equal to decimal ground truth on all four simulated datasets, both engine logs and 39 of 40 random seeds; cancels, corrections, resends and drop copies right (S07-04, S06-12, S07-10). | Fill dropped on colliding ids (FL-01); cancel before fill (FL-04); non-numbers counted (FL-10); ties and precision (FL-15, FL-16). |
| Multi-session isolation | 3 | Correct when every identifier is unique across the log (845 messages, 5 sessions: DS-mixed-sessions-01 to -07); FIX 4.2 and 4.4 side by side (S11-04); a reset on one session leaves the others alone (S11-03). | Fails as soon as identifiers or CompIDs collide: FL-01, FL-02, FL-06. Both P0 are here. |
| Fault tolerance | 9 | No exception on any input; a damaged message never took a neighbour with it (PB-03, S10-18, S10-19); over-limit input refused cleanly; no hang. | One message with 100,000 fields takes 4.5 s to draw. |
| Scalability within the stated limits | 8 | 1,000 messages: 50 ms of analysis, 1.2 to 1.7 s to the painted page; linear in messages, sessions and orders; refusal of 10,000 messages in 0.07 s. | A shared cloud machine; timings vary by about a third between runs. |
| Observability and diagnostics | 6 | Error cards name the message, the position and the rule; unmatched cancels are counted in a note. | Several things are left out or ignored without a word (FL-07, FL-12, fills not counted); "header order wrong" for an unknown delimiter; "unknown value" for a valid field. |
| Maintainability | 8 | 903 lines, pure modules, no dependency, a design document precise enough to test against. | Three scans of the text; a full re-render per interaction. |
| Test coverage (the product's own) | 6 | 264 passing tests, mutation-test discipline, static privacy checks. | They restate the PRD; none of the 16 defects is covered. 4 tests cannot run in this copy (missing XML). |
| Production readiness | 4 | Ready for one-session logs; not for shared logs. | No real logs, one browser. |

## What was tested, what passed, what failed

242 tests in the matrix: **203 PASS, 30 FAIL, 2 BLOCKED, 7 NOT APPLICABLE.**

| Brief section | Tested | Passed | Failed (defect) |
|---|---|---|---|
| 2 Baseline | the product's own suite | 264 of 268; the 4 failures are the known missing XML files | |
| 4 Protocol coverage | both versions apart; unsupported BeginString on 3 messages; unknown tags and values; dictionaries against two sources | all but | multiple-value field (FL-14) |
| 5 Generation | an independent simulator (seeded, decimal) and a real QuickFIX initiator and acceptor; each validated by the other side's rules | | |
| 6 Session level | every session message type; gaps; duplicates; out of order; PossDup; 141; NewSeqNo; reconnections; overlapping numbers | 13 of 21 cases; the gaps of all datasets and engine logs | restart at 1 (FL-05), SubID sessions (FL-06), too-low number (FL-07), resent order (FL-08), PossDup at expected, reset to lower (FL-09) |
| 7 Order lifecycle | all listed flows in both versions; cancels and corrections; duplicates; late and early reports; reused ClOrdIDs; summary with filters and with an order selected | 13 of 20 cases and all 40 dataset and engine checks | cancel before fill (FL-04), colliding ids (FL-01, FL-02, FL-03), stale banner (FL-11), tie rounding (FL-15) |
| 8 Repeated tags | a FIX 4.4 report with two groups, a FIX 4.2 NewOrderList | both | |
| 9 Formats | 16 representations of 3 datasets; empty input; truncation; wrapped message; log order | all 53 | |
| 10 Malformed and hostile | 46 fixtures | 36 | missing BeginString (FL-12), number forms (FL-10), precision (FL-16), single-byte text (FL-13) |
| 11 Multi-session | 5-session mixed log; both versions in one log; drop copy; same ExecID on two orders; SubIDs; reset on one session; incomplete log; merged log | the 8 checks on the 5-session dataset and 6 of 12 cases | FL-01, FL-02, FL-03, FL-06, FL-08 |
| 12 Performance and limits | 100 to 1,000 messages; both limits just under, at, just over; 10,000 refused; 11 hostile inputs; Node and Chromium | all | |
| 13 Ground truth | a manifest per dataset; cross-checked by a second validator and by QuickFIX | | |
| 14 Differential and property | QuickFIX parser; 7 properties with Hypothesis; determinism; equivalence | 7 of 8 | one random seed hit the tie rounding (FL-15) |

## What could not be tested (BLOCKED)

- **Real logs of the support team** (BL-02). None were supplied, and they must not leave the owner. This is the
  largest gap in the evidence: SD-1 (FIX 4.4 fills sent with ExecType 1 or 2) can only be settled there.
- **Firefox, Safari and Edge** (BL-01). Only Chromium is installed. The logic is the same in every browser;
  paste behaviour, layout and timings are not.

Not blocked, but worth knowing: the two engine logs cannot be regenerated byte for byte (wall-clock
timestamps); timings come from a shared cloud machine.

## Outside the advertised scope

Nothing in the brief's removed list was tested. Two things seen in passing are worth knowing: public sample
logs written by hand (two of the four in the brief's list) have wrong BodyLength in every message, so the tool
rightly shows them as all malformed, and a technician trying the tool with such examples will see only error
cards; and one row per Symbol nets different contracts of the same symbol (risk 1 in `defects.md`).

## What remains uncertain

- How often the owner's shared logs contain colliding ClOrdIDs, OrderIDs or ExecIDs. With plain counters it is
  certain; with prefixed ids it may never happen. One real multi-session log would tell.
- Whether real FIX 4.4 counterparties send ExecType 1 or 2 (SD-1).
- Behaviour with clipboard managers or terminals that alter SOH before the text reaches the page: Chromium's
  textarea keeps SOH, other paths were not tried.

## Highest-risk failure modes, in order of remediation

1. **Wrong bought/sold and merged orders in shared logs (FL-01, FL-02).** Give the tool one session identity
   (BeginString, CompIDs, SubIDs, LocationIDs) and use it in the three places that need it: the sequence
   direction, the ClOrdID / OrderID namespace, the execution key. This also resolves FL-06.
2. **Wrong order shown, and a busted trade still counted (FL-03, FL-04).** Small code changes; both are
   defects against the PRD as written.
3. **Blind spots in the session view (FL-05, FL-07, FL-09).** A new-session rule and a "too low" event.
4. **Silent omissions (FL-08, FL-10, FL-11, FL-12, FL-13).** Each needs a rule and, as important, a visible
   count of what was left out.
5. **Figures (FL-15, FL-16) and labels (FL-14).**

Every defect names a regression test that already exists in this folder; after remediation,
`bash tests/run_all.sh` should show them passing and nothing else changing.

## Performance inside today's limits

Measured on a 4-core Xeon 2.1 GHz cloud container, Node 22.23 and headless Chromium (Playwright 1.63), on
realistic mixes (5 sessions, FIX 4.2 and 4.4; at 1,000 messages: 164 orders, 656 execution reports, 93
cancel and replace requests, 25 cancel rejects, 62 session messages). Logic figures are medians of 15 runs,
repeated in 3 fresh processes; page figures are a first decode and the median of 5 more.

| Messages | Analysis (Node), median | Messages/s | Peak memory, Node process | Decode to painted page, first | repeated | Filter change | Order selection | DOM elements |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 4.6 ms | 21,900 | 60 MB | 0.19 s | 0.12 s | 0.02 s | 0.02 s | 12,527 |
| 250 | 7.5 ms | 33,500 | 73 MB | 0.35 s | 0.37 s | 0.11 s | 0.05 s | 31,912 |
| 500 | 17 ms | 29,500 | 98 MB | 0.74 s | 0.76 s | 0.17 s | 0.08 s | 64,412 |
| 1,000 | 50 ms | 20,000 | 146 MB | 1.55 s | 1.57 s | 0.48 s | 0.14 s | 129,174 |

- **Requirements:** 100 messages in under 5 s: 12.6 ms for the first call in Node, 0.19 s in the page. Each
  view under 1 s at 1,000 messages on the logic modules: order grouping 1.8 ms, trading summary 0.8 ms,
  filters 1.2 ms. All met with a wide margin (PF-01, PF-02, BR-13, BR-14).
- **Throughput** is 4 to 6 MB/s and 20,000 to 34,000 messages/s; an idle Node process peaks at 55 MB, so 1,000
  messages cost about 90 MB of peak resident memory over 15 repeated decodes; after a collection, with the
  result kept, 11 MB of heap is in use, 6 MB of which is the idle process. In the page the JavaScript heap is 6 MB after a decode of
  1,000 messages; the memory is in the 129,000 DOM elements, which the heap figure does not include.
- **Initialisation:** importing the modules 9 to 17 ms; page load to ready 0.12 s; the first decode in a
  process is 2 to 3 times the repeated one in Node and about the same in the page.
- **Limits:** 999 and 1,000 messages are decoded, 1,001 refused; 1,048,575 and 1,048,576 bytes decoded,
  1,048,577 refused; 10,000 messages (2.1 MB) refused in 68 ms in Node and 76 ms in the page, with both
  numbers in the warning, advice to split, and nothing else on the page (BR-12, PF-03).
- **Malformed messages cost nothing extra:** the 1,000-message log with 10%, 50% and 100% of its CheckSums
  broken takes 35, 35 and 38 ms, against 34 to 50 ms without.
- **More sessions and orders cost nothing extra:** 1, 5, 20 and 50 sessions (2 to 100 directions, 141 to 207
  orders) at 1,000 messages: 34, 50, 31 and 29 ms. One order of 1,000 chained amendments: 26 ms.
- **Hostile input inside 1 MiB:** eleven inputs in Node, all between 1 ms and 0.57 s; the slowest are 300,000
  empty fields (0.41 s) and one message with 100,000 fields (0.21 s). In the page the 100,000-field message
  takes 4.5 s to paint (500,000 elements); the others 0.06 to 0.29 s. No backtracking, no quadratic step, no
  hang.
- **Where the time goes:** in Node, `checkMessage` is half of the analysis (27 of 50 ms), the limit check and
  the split a third (the text is scanned three times in all). In the page, analysis is about 3% of the time
  to a painted result, building the DOM about 15%, and the browser's style, layout and paint the rest.

**Proposed acceptance criteria**, from the PRD's requirements and this baseline with about a factor of two
for a slower machine: analysis of 1,000 messages in 150 ms; decode to painted page in 3 s at 1,000 messages;
a filter change and an order selection in 1 s; an over-limit paste refused in 0.5 s; any input inside the
limits answered in 10 s.

## Information for the planned limit of 10,000 messages

Not a defect of v1.2 and not in the PASS/FAIL matrix. Measured on a **copy** of the product with one line of
`src/limits.js` changed (10,000 messages, 16 MiB), with the same realistic mixes (at 10,000 messages: 2.1 MB,
1,412 orders, 6,771 execution reports).

Logic modules under Node:

| Messages | Bytes | Analysis, median | first call | Messages/s | ms per 1,000 messages | Peak resident memory | Heap in use, result kept |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 208,290 | 34 ms | 67 ms | 29,800 | 34 | 150 MB | 11 MB |
| 2,500 | 528,866 | 101 ms | 180 ms | 24,700 | 41 | 202 MB | 19 MB |
| 5,000 | 1,063,192 | 193 ms | 235 ms | 25,800 | 39 | 281 MB | 32 MB |
| 10,000 | 2,146,439 | 362 ms | 550 ms | 27,600 | 36 | 418 MB | 59 MB |

At 10,000 messages by module: `checkMessage` 208 ms, `splitMessages` 65 ms, the limit check 56 ms, decode
41 ms, timeline 9 ms, order grouping 7 ms, trading summary 4 ms, Account filter 10 ms. One order of 10,000
chained amendments: 264 ms, no stack overflow.

The page in Chromium:

| Messages | Decode to painted, first | repeated (median of 5) | of which the handler (analysis + building the DOM) | Filter change | Order selection | Show all messages | DOM elements | JS heap |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 1.3 s | 1.3 s | 0.2 s | 0.38 s | 0.11 s | 1.5 s | 129,174 | 6 MB |
| 2,500 | 2.8 s | 3.3 s | 0.6 s | 0.97 s | 0.23 s | 2.9 s | 325,067 | 12 MB |
| 5,000 | 5.5 s | 5.5 s | 1.3 s | 2.6 s | 0.43 s | 6.2 s | 649,963 | 12 MB |
| 10,000 | 12.4 s | 13.3 s | 2.2 s | 4.3 s | 1.1 s | 10.4 s | 1,303,278 | 43 MB |

- **Nothing scales worse than linearly.** Analysis stays at 34 to 41 ms per 1,000 messages; the painted page
  at 1.1 to 1.3 s per 1,000 messages; memory at about 30 MB of peak resident memory and 5 MB of kept heap per
  1,000 messages.
- **The time is in drawing, not in analysis.** At 10,000 messages the analysis is 0.4 to 0.5 s; building 1.3
  million elements 1 to 2 s more; the remaining 10 to 11 s is the browser laying out and painting them.
  The page is frozen during that time, and again for 4 s on a filter change and 10 s on "Show all messages".
- **What 10,000 would need:** the logic is ready as it is. The page is not: it should draw only the cards in
  view (a windowed list) or page them, so that the time to a first painted result stays near the 1,000-message
  figure. The 1,048,576-byte limit must rise with the message limit: 10,000 realistic messages are 2.1 MB.
- The defects FL-01 and FL-02 matter more at 10,000 messages than at 1,000: a larger paste holds more
  sessions and more chances for identifiers to collide.
