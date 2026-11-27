# Executive summary

Independent validation and stress test of FIX Lens v1.2 (a read-only rebuild of the trusted main at
`6f2f554`), done on 2026-11-27 to the scoped brief. The product was not changed.

## Verdict: NOT PRODUCTION READY

Two critical (P0) defects are unresolved. Both appear only when one pasted log holds **several sessions**,
which is a use the PRD advertises (filtering "one client's flow in a shared log"). On a log of **one
session** the tool was right in everything it showed, apart from one rounding case.

It would be conditionally ready if the two P0 defects are fixed, or if it is offered for one session per paste
with a line on the page that says so. The conditions are in `final-assessment.md`.

## What was done

- **242 tests: 203 PASS, 30 FAIL, 2 BLOCKED, 7 not applicable** (`test-matrix.md`). Nothing is marked PASS
  that did not run.
- **Two independent sources of traffic:** a seeded simulator written for this work (decimal arithmetic, its
  own encoder and validator), and a real QuickFIX initiator and acceptor talking over loopback. About 9,500
  messages in FIX 4.2 and 4.4, each with a ground truth that was never taken from the tool.
- **106 hand-built cases** for the brief's sections 4 to 11, each tied to a clause of the PRD or of the FIX
  specification.
- **Differential and property tests:** the same accept or reject verdict as the QuickFIX parser on 1,184
  messages; seven properties with Hypothesis; 16 representations of the same log.
- **The page in a real browser** (Chromium): pasting, filters, order selection, limits, hostile markup,
  timings.
- **Benchmarks** in Node and in the browser, inside the limits, at the limits, and at 2,500 to 10,000
  messages on a copy with the limit lifted.

## What holds up

| Area | Result |
|---|---|
| Decoding and framing | Every well-formed message was read back field for field; every damaged one was reported with its number, position and rule; no neighbour was lost. Verdicts identical to QuickFIX. |
| Dictionary | Identical to the pinned Orchestra FIX 4.2 and 4.4 files (405 and 912 fields). |
| FIX 4.2 against FIX 4.4 | ExecTransType and ExecType are handled apart and correctly, including trade cancels and corrections. |
| One-session logs | Every event, sequence gap, order chain, filter result and trading figure equal to ground truth on four simulated datasets, two engine logs and 39 of 40 random seeds. |
| Input formats | SOH, `\|`, `^A`, `<SOH>`, CRLF, BOM, prefixes, QuickFIX log lines, several messages per line: same result every time. |
| Limits and speed | 1,000 messages: 50 ms of analysis, about 1.5 s to the painted page. Both limits exact. 10,000 messages refused in under 0.1 s. No hostile input caused a hang. |
| Privacy | No request during a decode, nothing stored, markup in pasted values stays text. |

## What fails: 16 confirmed defects

**2 P0, 5 P1, 6 P2, 3 P3.** Thirteen are gaps in the product's own documents: the tool does what the PRD and
design say, and that is wrong for real FIX traffic. Three are defects against the PRD (FL-03, FL-04, FL-15).
Details, minimal logs and commands are in `defects.md`.

The three that matter most:

1. **FL-01 (P0): fills from two venues that share OrderID and ExecID are counted as one.** A client filled 100
   on one venue and 200 on another, both numbering from 1, is shown as bought 100. Nothing on the page says a
   fill was left out.
2. **FL-02 (P0): orders of two clients that reuse a ClOrdID become one order.** The Account filter for one
   client then shows the other client's messages and trades.
3. **FL-05 (P1): after a session restarts at 1 without ResetSeqNumFlag, sequence gaps are no longer found.**
   "0 sequence gaps" is then not evidence that nothing was lost. Daily resets and reset-on-logout
   configurations restart this way.

The rest, in short: the wrong order opens when a value is a ClOrdID of one order and the OrderID of another
(FL-03); a trade cancel listed before its fill is not applied (FL-04); sessions told apart by SubID share one
sequence counter (FL-06); a reused sequence number is not pointed out (FL-07); a resent order is counted
twice in the order column (FL-08); two cases of false gaps (FL-09); `0x10` and `1e3` are counted as
quantities (FL-10); the order banner can show a stale state (FL-11); a message without BeginString vanishes
without an error (FL-12); accented text in a single-byte encoding makes a valid message "malformed" (FL-13);
`18=1 6` is labelled "unknown value" (FL-14); an average ending exactly on a half is rounded down (FL-15);
very small and very large figures (FL-16).

**One root cause is behind the four most serious:** the tool has no single notion of a session. Sequence
tracking, order identity and execution identity each use a partial key. Giving them one session identity
(BeginString, CompIDs, SubIDs) fixes FL-01, FL-02 and FL-06 and prepares FL-05.

## What could not be tested

- **The support team's real logs** (BLOCKED): none were supplied. The PRD already makes deployment wait for
  that test; it is still needed.
- **Firefox, Safari and Edge** (BLOCKED): only Chromium is installed here.
- One suspicion can only be settled with real logs: FIX 4.4 counterparties that still send ExecType 1 or 2
  for fills would get no fill counted. The tool follows the dictionaries here; it is listed as suspected, not
  as a defect.

## For the planned limit of 10,000 messages

Information only, measured on a copy with the limit lifted. The analysis is ready: 0.36 s for 10,000 messages,
linear. The page is not: 12 to 13 s to the first painted result, 4 s for a filter change, 1.3 million DOM
elements. Nothing scales worse than linearly; the time is in drawing every card at once. A windowed or paged
list is needed before the limit is raised, and the byte limit has to rise with it (10,000 messages are 2.1 MB).

## Recommended order of work

1. One session identity, used for sequence numbers, order ids and execution ids (FL-01, FL-02, FL-06), with
   AC-035, AC-041 and TR-003 changed first.
2. FL-03 and FL-04: small, and both against the PRD as written.
3. The session view: a new-session rule and a "sequence too low" event (FL-05, FL-07, FL-09).
4. Say what was left out: a visible count wherever the tool ignores or skips something (FL-08, FL-10 to FL-13).
5. Decimal arithmetic for the figures (FL-15, FL-16); multiple-value fields (FL-14).
6. Test with the support team's real logs, then decide on deployment.

Every defect has a regression test in this folder. `bash tests/run_all.sh` re-runs everything.
