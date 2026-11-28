# Architecture assessment

What FIX Lens v1.2 is, how it reads a log, and the assumptions built into it. Written from the source
(903 lines in `src/`), the PRD v1.2 and the technical design v1.2.2, before the tests were run, and checked
against the test results afterwards.

## Shape

One static page and twelve plain ES modules, no build step, no runtime dependency, no backend.

```
paste (textarea) -> analyse(text)
                      checkLimits   bytes (UTF-8) and candidate count      src/limits.js
                      splitMessages candidates from "8=FIX" to "10=nnn"    src/framing.js
                      checkMessage  six framing rules, first failure only  src/framing.js
                      decode        tag -> name, enum meaning              src/decode.js, dictionary.js, dictionary/fix42.js, fix44.js
                      timeline      events, sequence gaps                  src/timeline.js, execution.js
                 -> render(result, view)                                    src/render.js   (the only DOM code, with main.js)
                      orderGroups   union-find over 11, 41, 37             src/orders.js
                      applyFilters  Account (through groups), 49, 50, 56, 57  src/filters.js
                      tradeSummary  executions, cancels, corrections       src/summary.js
```

Everything is recomputed on every render: a filter change or an order click runs grouping, filters and the
trading summary over the whole log again and rebuilds the whole DOM. Nothing is stored between renders except
the analysis result and the view (`main.js`).

## Advertised, implemented, missing

| Area | Advertised (PRD v1.2) | Implemented | Not there |
|---|---|---|---|
| Versions | FIX 4.2 and 4.4 by BeginString; anything else "unsupported version" per message | yes; an unsupported message is shown raw, still takes part in the timeline and in order grouping, never in the trading summary | FIX 5.0 and all others (out of scope) |
| Input | pasted text; SOH, `\|`, `^A`, `<SOH>`; several messages per line; prefixes ignored | yes, delimiter chosen per message | files, PCAP, JSON, other spellings of SOH (reported as "header order wrong") |
| Framing checks | six rules of TR-002, with message number, position, rule | yes, identical verdicts to QuickFIX's parser on 1,184 valid and damaged messages | a message with no `8=FIX` is not a candidate at all (FL-12) |
| Dictionary | Orchestra FIX 4.2 / 4.4, names and code sets | yes, equal to an independent parse of the pinned files (405 and 912 fields) | multiple-value fields (FL-14); no required-field or format checks (out of scope) |
| Timeline | 9 session events, 5 order events, 7 kinds of execution report, sequence gaps per CompID pair | yes | too-low numbers, session restarts, SubID sessions (FL-05, FL-06, FL-07, FL-09); nothing from timestamps (out of scope) |
| Order story | click an id, see the cancel/replace chain, terms and latest state | yes | scope by session (FL-02); the tag of the clicked id (FL-03) |
| Trading summary | orders, bought, sold, averages, net per Symbol; cancels and corrections; resends counted once | yes | scope by venue (FL-01); out-of-order cancels (FL-04); decimal arithmetic (FL-15, FL-16) |
| Filters | Account, SenderCompID, SenderSubID, TargetCompID, TargetSubID | yes | |
| Limits | 1,048,576 bytes or 1,000 messages, refuse with both numbers | yes, exact at both boundaries | |
| Privacy | no network, no storage, no logging; CSP; text nodes only | yes: no request during decode, nothing stored, hostile markup stays text (BR-09, BR-10) | |

## Assumptions built into the tool

These are the implicit assumptions the brief asks to identify. Each is true for a tidy log of one session and
false for some real logs; the defect it leads to is named.

| # | Assumption | Where | When it is false | Defect |
|---|---|---|---|---|
| 1 | A session direction is the pair SenderCompID, TargetCompID | `timeline.js:34`, TR-003 | several sessions on one CompID pair, told apart by SubID, LocationID or BeginString | FL-06 |
| 2 | Sequence numbers only start again at a Logon with 141=Y | `timeline.js:39` | logout or disconnect resets, daily resets, a paste that joins two days | FL-05 |
| 3 | A number lower than expected is harmless | `timeline.js:50`, design 11 | it is the fatal "MsgSeqNum too low" | FL-07 |
| 4 | A PossDup message never fills a number | `timeline.js:37`, TR-003 | a resend of a message the log has not seen | FL-09 |
| 5 | A ClOrdID or an OrderID names one order in the whole log | `orders.js:24-37`, AC-035 | two clients, two venues, two days | FL-02 |
| 6 | OrderID plus ExecID names one execution in the whole log | `summary.js:29-32`, AC-041 | two venues | FL-01 |
| 7 | An id value is either a ClOrdID or an OrderID, never both | `orders.js:64`, design 12 | numeric ids on both sides | FL-03 |
| 8 | The log is in the order things happened | `summary.js` (one pass), `render.js:114` | merged or re-sorted logs, resends, late reports | FL-04, FL-11 |
| 9 | Every NewOrderSingle message is an order | `summary.js:101-109`, AC-040 | resends, logs merged from both sides | FL-08 |
| 10 | Whatever JavaScript converts to a number is a FIX quantity or price; a double is exact enough | `summary.js:7-11`, `render.js:27` | `0x10`, `1e3`; exact ties; more than 4 decimals; more than 2^53 | FL-10, FL-15, FL-16 |
| 11 | The pasted characters are the bytes that were on the wire, in UTF-8 | `framing.js:134`, design 3.7 | single-byte encodings | FL-13 |
| 12 | Text that does not contain `8=FIX` is not FIX | `framing.js:12` | a message with a missing or damaged BeginString | FL-12 |
| 13 | An enumerated field holds one value | `decode.js:13` | MultipleValueString fields | FL-14 |
| 14 | A Symbol (55) is one instrument | AC-039 | derivatives, the same symbol on two exchanges | risk 1 in `defects.md` |

Timestamps: the tool computes nothing from them (SendingTime is shown, never compared), so there is no
clock-domain assumption to test.

## Strengths seen in the code and confirmed by tests

- **Small, pure, dependency-free modules.** Every logic module is a pure function without DOM access and can
  be driven from Node; that is what made this validation possible at volume.
- **Framing is careful and linear.** One left-to-right scan, offsets into the original text, no regular
  expression over the whole input. Eleven hostile inputs up to the 1 MiB limit all answered in under 0.6 s in
  Node; no input made it throw (300 random hostile texts, PB-04).
- **The security posture is real, not declared.** Output is built with `textContent` only; the CSP forbids
  connections; markup in ids, parties, symbols, MsgType, BeginString and inside a malformed message stayed
  text in Chromium, and no request left the page.
- **The technical design is precise enough to test against,** which is rare. Most of what failed is written
  down there as a decision, and can be changed there first.

## Weaknesses

- **No notion of a session as an entity.** Sequence tracking, order identity and execution identity each use
  their own partial key; none includes the full session identity. This one gap is behind FL-01, FL-02, FL-05
  and FL-06, the four most serious defects.
- **Binary floating point for money figures,** with rounding left to `toFixed`.
- **Silent choices.** Where the tool decides not to count or not to flag something (a lower sequence number, a
  fill with an unusable quantity, a line without `8=FIX`, a second fill with a known key), the page gives no
  count of what was left out. The unmatched-cancel note of AC-044 shows the better pattern.
- **Full re-render on every interaction.** At 1,000 messages a filter change or an order click takes 0.15 to
  0.5 s and returning to the full log 1.3 s; beyond that it is the dominant cost.
- **Tests mirror the PRD.** 264 passing tests, 3,541 lines, none for the cases above.
