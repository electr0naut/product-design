# FIX Lens validation: the reviewer's check of the findings (2026-11-27)

The validation agent's output is in `fix-lens/validation/` (commit `c84ee82`); start with
`reports/executive-summary.md` there. This file is my own check of it. Nothing here changes the PRD, the
design or the queue: which findings are fixed in phase 1 is Ubay's decision.

## What I checked, and how
- **All 16 confirmed defects reproduce** on FIX Lens v1.2 as landed (trusted main `6f2f554`). I ran the 26
  reproduction logs through the product's own modules with a script of mine (`analyse`, `orderGroups`,
  `tradeSummary`, `applyFilters`, the timeline), not through the agent's checker, and read the raw answers.
  The agent's own `reproductions/repro.mjs` gives the same.
- **The fixtures are what they claim to be.** I recomputed BodyLength and CheckSum of every message in the 26
  logs from the bytes. All frames are valid, apart from the two that are meant not to be: the message without
  BeginString (FL-12) and the message that is valid in ISO-8859-1 and not in UTF-8 (FL-13).
- **The expected results are right.** I read each against the FIX rules it cites and against the PRD clause it
  names (AC-035, AC-036, AC-040, AC-041, AC-044, AC-045, AC-051, TR-002, TR-003). The split between "defect
  against the PRD" (FL-03, FL-04, FL-15) and "gap in the PRD or design" (the other 13) is right.
- **v1.3 changes none of it.** My v1.3 reference build gives the same answers on all 26 logs, as expected:
  v1.3 touches the limits and the paging only.
- Not checked by me: the agent's 203 passing tests, its QuickFIX runs and its benchmarks. I read their
  reports; I did not rerun them.

## The findings
| Id | Sev | What happens | Against | Already in phase 2 as |
|---|---|---|---|---|
| FL-01 | P0 | fills of two venues that share OrderID and ExecID count as one | gap (AC-041) | D: executions on several feeds |
| FL-02 | P0 | two clients reusing a ClOrdID become one order; the Account filter shows the other client's flow | gap (AC-035, AC-051) | D: order identity scoped to its session |
| FL-03 | P1 | clicking an OrderID opens another order whose ClOrdID has the same value | PRD AC-036 (design 12) | |
| FL-04 | P1 | a trade cancel that stands before its fill is not applied | PRD AC-041/042/044 (design 13) | |
| FL-05 | P1 | after a restart at 1 without 141=Y, gaps are no longer found | gap (TR-003) | C: disconnects, reconnects, resets |
| FL-06 | P1 | sessions that differ only by SubID share one counter | gap (TR-003) | C: session identity beyond the CompIDs |
| FL-07 | P1 | a MsgSeqNum already used, without PossDupFlag, is not pointed out | gap (design 11) | C: duplicate and too-low numbers |
| FL-08 | P2 | a resent NewOrderSingle counts as a second order | gap (AC-040) | D |
| FL-09 | P2 | false gap after a PossDup with the expected number, and after a reset to a lower number | gap (TR-003) | C |
| FL-10 | P2 | `0x10`, `1e3`, ` 100 ` count as quantities and prices | gap (design 13) | E: field formats |
| FL-11 | P2 | the order banner takes its state from a resent older report | gap (AC-036) | D: a full state for every order |
| FL-12 | P2 | a message without BeginString disappears without an error | gap (TR-002) | |
| FL-13 | P2 | a message with accented single-byte text (ISO-8859-1 on the wire) is called malformed | gap (design 3.7) | |
| FL-14 | P3 | `18=1 6` (a valid multiple-value field) is labelled "unknown value" | gap (AC-004) | E: enumerations |
| FL-15 | P3 | an average that ends exactly on a half is rounded down (1.00255 shown as 1.0025) | PRD AC-045 | |
| FL-16 | P3 | figures finer than 4 decimals or above 2^53 are shown as other values | gap (design 13) | |

Verdict of the validation: **not production ready**, because of the two P0. Both need a log that holds several
sessions whose identifiers collide. On one-session logs every result was right, apart from FL-15.
Blocked, not tested: Firefox, Safari and Edge (only Chromium here); the support team's real logs.
Suspected, not confirmed: SD-1, FIX 4.4 counterparties that still send ExecType `1` or `2` for fills would get
no fill counted. Only real logs can show whether that happens.

## My recommendation (waits for Ubay: it changes the approved PRD and design)
**A v1.4 inside phase 1, after v1.3 lands, for seven findings:**
- FL-01 and FL-02, the two P0: ClOrdIDs scoped to the party that sent the order, OrderIDs and ExecIDs to the
  executing party. This pulls two items of theme D forward from phase 2.
- FL-03, FL-04 and FL-15: the three defects against the PRD. FL-03 and FL-04 sit in the code the P0 fixes
  rewrite.
- FL-05: a Logon with MsgSeqNum 1 on a direction already seen starts a new session. Small, and without it
  "0 sequence gaps" is wrong for any paste that covers a daily restart.
- FL-13: accept a message whose length and checksum are right at one byte per character. Small, and likely
  in Ubay's real-log test: European counterparties send accented names.

About four tickets. **The other nine stay in phase 2**, where themes C, D and E already hold them (FL-12 and
FL-16 added to E).

The cheaper alternative the validation offers: no fix, and a line on the page, "Paste one session at a time".
I do not recommend it: US-009 exists for one client's flow in a shared log.

For the real-log test: search the FIX 4.4 logs for `150=1` or `150=2` (SD-1).
