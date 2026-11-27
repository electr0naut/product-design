# Defects

16 confirmed defects: **2 P0, 5 P1, 6 P2, 3 P3**. No suspected defect is counted among them; four suspected
defects and six architectural risks are listed at the end.

Every confirmed defect was reproduced at least twice (each case runs twice in every run, and the suite was
run several times), has a minimal log in `reproductions/`, and has an expected result worked out from the FIX
specification or the product's PRD, never from the tool. Reproduce any of them with:

```
FIX_LENS_DIR=<product folder> node reproductions/repro.mjs FL-01
```

**Two kinds of defect are kept apart**, in the "Kind" line of each entry:

- **Product defect:** the tool does not do what its own PRD says. Three of the 16: FL-03, FL-04, FL-15. In
  FL-03 and FL-04 the code follows the technical design, and it is the design that departs from the PRD.
- **Gap in the product's documents:** the tool does what the PRD and design say, and what they say is wrong
  or incomplete for real FIX traffic. Thirteen of the 16, both P0 among them. Fixing these starts with a
  change to the PRD or the design.

Source locations are in the product folder, as built (`src/…:line`). In the logs below `|` stands for the SOH
byte; the fixture files hold real SOH bytes.

| Id | Severity | Kind | Title |
|---|---|---|---|
| FL-01 | P0 | document gap | Two fills that share OrderID and ExecID on different sessions are counted as one |
| FL-02 | P0 | document gap | Orders of different clients that reuse a ClOrdID are merged; the Account filter shows the other client's flow |
| FL-03 | P1 | product defect | Clicking an id opens another order when the value is a ClOrdID of one order and the OrderID of another |
| FL-04 | P1 | product defect | A trade cancel that stands before its fill in the log is not applied |
| FL-05 | P1 | document gap | After a session restarts at 1 without ResetSeqNumFlag, sequence gaps are no longer found |
| FL-06 | P1 | document gap | Sessions told apart only by SubIDs share one sequence counter |
| FL-07 | P1 | document gap | A MsgSeqNum that was already used, without PossDupFlag, is shown as a normal message |
| FL-08 | P2 | document gap | A resent or duplicated NewOrderSingle is counted as another order |
| FL-09 | P2 | document gap | False sequence gaps after a PossDup message with the expected number, and after a reset to a lower number |
| FL-10 | P2 | document gap | Values that are not FIX numbers are counted as quantities and prices |
| FL-11 | P2 | document gap | The order banner takes the latest state from a resent older report |
| FL-12 | P2 | document gap | A message without BeginString disappears without an error |
| FL-13 | P2 | document gap | A wire-valid message with ISO-8859-1 text is reported as malformed |
| FL-14 | P3 | document gap | A valid multiple-value field is labelled "unknown value" |
| FL-15 | P3 | product defect | An average price that ends exactly on a half is rounded down |
| FL-16 | P3 | document gap | Figures finer than 4 decimal places or larger than 2^53 are shown as other values |

---

## FL-01 (P0) Two fills that share OrderID and ExecID on different sessions are counted as one

- **Kind:** gap in the product's documents. AC-041 identifies an execution "by its OrderID (37) and ExecID
  (17)" and nothing else; the tool does exactly that.
- **Component:** trading summary (`src/summary.js`), order grouping (`src/orders.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-01-S07-08.log` (test S07-08). One client, two venues; each venue numbers its
  orders and executions from 1, as many do.

  ```
  35=D 49=CLI 56=VENUEA 11=A1 55=ACME 54=1 38=100
  35=D 49=CLI 56=VENUEB 11=B1 55=ACME 54=1 38=200
  35=8 49=VENUEA 56=CLI 37=1 11=A1 17=1 150=F 39=2 55=ACME 54=1 32=100 31=10
  35=8 49=VENUEB 56=CLI 37=1 11=B1 17=1 150=F 39=2 55=ACME 54=1 32=200 31=11
  ```
- **Reproduce:** `node reproductions/repro.mjs FL-01`
- **Expected:** ACME: 2 buy orders, bought 300, average 10.6667, net +300; two orders. In FIX, OrderID is
  assigned by the executing party and is unique only for that party (and trading day), and so is ExecID: two
  venues are two namespaces.
- **Actual:** bought **100**, average 10, net +100; the strip says **1 order**. The second venue's fill of 200
  is dropped as a "resend" of the first. Nothing on the page says so.
- **Source:** `src/summary.js:29-32` (`orders.get(orderId)` then `reports.has(execId)`, no session in the
  key); `src/orders.js:31-32` (one map of OrderIDs for the whole log).
- **Evidence:** `reports/results.json`, test S07-08. The control test S07-09 (same ExecID, different OrderIDs,
  one venue) passes, and S07-10 (the same execution seen again on a drop copy) passes because of the same
  rule: the rule cannot tell a drop copy from a second venue.
- **Root cause:** the execution key and the OrderID key carry no session identity.
- **Impact:** in a log that holds more than one venue or broker session, bought, sold, average price and net
  can be understated by any amount, silently. A technician checking a client's activity "at a glance" (US-008)
  would confirm a wrong figure.
- **Remediation:** key executions and OrderIDs on the executing party as well: the SenderCompID of the report
  (with SenderSubID and the BeginString), so `<49 of the report>|<37>|<17>`. To keep counting a drop copy
  once, treat a report as a repeat only when OrderID, ExecID, Symbol, Side, LastQty and LastPx are all equal,
  and otherwise count it and say so in the table's note. Change AC-041 first.
- **Regression test:** S07-08 as it stands, with S07-09 and S07-10 kept as controls.

## FL-02 (P0) Orders of different clients that reuse a ClOrdID are merged; the Account filter shows the other client's flow

- **Kind:** gap in the product's documents. AC-035 joins messages that "share a ClOrdID (11) or an OrderID
  (37)", whatever session they are on; AC-051 builds the Account filter on those groups.
- **Component:** order grouping (`src/orders.js`), filters (`src/filters.js`), order story and strip
  (`src/render.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-02-S07-06.log`, `FL-02-S07-07.log` (tests S07-06, S07-07). Two clients of one
  broker both use ClOrdID `1`.

  ```
  35=D 49=CLI1 56=BRK 11=1 1=ACC1 55=AAA 54=1 38=100
  35=D 49=CLI2 56=BRK 11=1 1=ACC2 55=BBB 54=2 38=50
  35=8 49=BRK 56=CLI1 37=O-1 11=1 17=E1 150=F 55=AAA 54=1 32=100 31=5
  35=8 49=BRK 56=CLI2 37=O-2 11=1 17=E2 150=F 55=BBB 54=2 32=50 31=7
  ```
- **Reproduce:** `node reproductions/repro.mjs FL-02`
- **Expected:** two orders. With Account = ACC1: messages 1 and 3, and one row, AAA bought 100. In FIX a
  ClOrdID is unique only for the party that sends the order.
- **Actual:** **one order** holding all four messages, with OrderIDs O-1 and O-2 in one banner. With Account =
  ACC1 the page shows **all four messages and a BBB row: sold 50 at 7**, which is the other client's trade.
- **Source:** `src/orders.js:24-37` (one map of ClOrdIDs for the whole log); `src/filters.js:29-41`.
- **Evidence:** `reports/results.json`, tests S07-06 and S07-07. On the 845-message dataset where every
  identifier is unique (`mixed-sessions`), grouping, order selection and all nine filter choices are correct
  (DS-mixed-sessions-04, -06, -07): the failure needs a collision, and plain counters such as `1`, `2`, `3` or
  a date-and-counter scheme make collisions ordinary.
- **Root cause:** identifiers are compared across sessions without the sender they belong to.
- **Impact:** US-009 exists to "look at one client's flow in a shared log". With colliding ClOrdIDs it shows
  one client another client's orders and executions under that client's account, which is both a wrong
  reconstruction and a disclosure problem if the screen is shared with the client.
- **Remediation:** scope a ClOrdID by the party that sent the order (the SenderCompID of the client message,
  the TargetCompID of the report, with SubIDs) and an OrderID by the executing party. Change AC-035 first.
- **Regression test:** S07-06 and S07-07; keep S07-01 (a cancel/replace chain is one order).

## FL-03 (P1) Clicking an id opens another order when the value is a ClOrdID of one order and the OrderID of another

- **Kind:** product defect against AC-036 ("activating an id shows only that order's messages"). The code
  follows design section 12 (`findOrder` takes the id alone and returns the first group that contains it), so
  the design is where it goes wrong.
- **Component:** order story (`src/orders.js`, `src/render.js`, `src/main.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-03-S07-11.log`. Order A has ClOrdID `1001`; order B (ClOrdID `ZZ9`) was given
  OrderID `1001` by the broker.
- **Reproduce:** `node reproductions/repro.mjs FL-03`; in the page, test BR-08 of `tests/browser_test.cjs`.
- **Expected:** clicking the OrderID button `1001` in message 4 shows order B: messages 2 and 4, banner
  `ZZ9 · 1001`.
- **Actual:** messages 1 and 3 and the banner `1001 · 7`, `Buy 100 AAA Market`, `New`: order A. Seen under
  jsdom and in Chromium.
- **Source:** `src/orders.js:64-65`; `src/render.js:143` (`handlers.pick(id)` passes the value without saying
  whether it is a ClOrdID or an OrderID); `src/render.js:242`.
- **Root cause:** the button forgets which tag it stands for.
- **Impact:** the technician reads the terms, the state and the filled quantity of a different order. The
  banner does show that order's ids, so an attentive reader can notice.
- **Remediation:** pass the tag with the id (`pick(tag, id)`) and look only in `orderIds` for tag 37 and only
  in `clOrdIds` for tags 11 and 41. With FL-02 fixed, pass the message number too.
- **Regression test:** S07-11 (the click check) and BR-08.

## FL-04 (P1) A trade cancel that stands before its fill in the log is not applied

- **Kind:** product defect against AC-041 ("executions as they stand at the end of the log"), AC-042 and
  AC-044 (which applies only "when the execution a report names is not in the log"). Design section 13 looks
  the execution up at the moment the cancel is read, which is where it departs from the PRD.
- **Component:** trading summary (`src/summary.js`).
- **FIX version:** 4.2 and 4.4 (the fixture is 4.4).
- **Fixture:** `reproductions/FL-04-S07-05.log`: a NewOrderSingle, then the TradeCancel (`150=H 19=E1`), then
  the fill `17=E1` of 100 at 10. Logs merged from two sources or sorted by another clock look like this.
- **Reproduce:** `node reproductions/repro.mjs FL-04`
- **Expected:** bought 0; no "unmatched" note, because the execution is in the log.
- **Actual:** **bought 100 at 10, net +100**, and the note "1 trade cancel or correction refers to an
  execution that is not in this log", which is untrue.
- **Source:** `src/summary.js:43-66` (the lookup `reports?.get(refId)` at the time the report is read).
- **Root cause:** one pass in log order; a cancel or correction whose target comes later is never revisited.
- **Impact:** a busted trade stays in the totals. The note warns that something is unmatched, but points the
  reader away from the log.
- **Remediation:** make two passes: collect fills first, then apply cancels and corrections in log order; or
  keep unmatched cancels pending and apply them when their execution appears.
- **Regression test:** S07-05, and the same with a TradeCorrect.

## FL-05 (P1) After a session restarts at 1 without ResetSeqNumFlag, sequence gaps are no longer found

- **Kind:** gap in the product's documents. TR-003 restarts the expected number only on a Logon with
  ResetSeqNumFlag (141)=Y, and design section 11 says a lower number is "ignored".
- **Component:** timeline (`src/timeline.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-05-S06-11.log`: a session A to B with numbers 1 to 8 ending in a Logout, then
  a new Logon with number 1, a Heartbeat 2 and a Heartbeat **5**.
- **Reproduce:** `node reproductions/repro.mjs FL-05`
- **Expected:** a SequenceGap at message 11 (expected 3, received 5). Sequence numbers start again at 1 with
  each new FIX session; engines configured to reset on logout or disconnect (QuickFIX `ResetOnLogout`,
  `ResetOnDisconnect`) and every scheduled daily reset do this without sending 141=Y.
- **Actual:** **0 sequence gaps.** After the restart every number is below the old high-water mark (9), so
  every message is "lower than expected" and ignored until the new session passes number 9.
- **Source:** `src/timeline.js:37-52` (line 39 resets only on 141=Y; line 50 ignores lower numbers).
- **Root cause:** one expected number per direction for the whole log, with no notion of a new session.
- **Impact:** in any paste that covers a restart, the strip's "0 sequence gaps" is not evidence that nothing
  was lost. Missing messages after the restart are not reported.
- **Remediation:** treat a Logon (35=A) with MsgSeqNum 1 on a direction that has already been seen as the
  start of a new session: restart both directions and add a timeline event that says so.
- **Regression test:** S06-11; keep S06-10 (a reconnection that continues the numbers).

## FL-06 (P1) Sessions told apart only by SubIDs share one sequence counter

- **Kind:** gap in the product's documents. TR-003 defines a direction as "each SenderCompID (49) /
  TargetCompID (56) pair".
- **Component:** timeline (`src/timeline.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixtures:** `reproductions/FL-06-S06-15.log` (desk D1 sends 1, 2, 3; desk D2 sends 1, 2, **4**, same
  CompIDs, interleaved) and `FL-06-S06-16.log` (D1 at 1, 2; D2 starts at 50).
- **Reproduce:** `node reproductions/repro.mjs FL-06`
- **Expected:** one gap, on D2's third message (expected 3, received 4); in the second log, none. A FIX session
  is identified by BeginString, the CompIDs and, where used, SubID and LocationID.
- **Actual:** first log: **no gap** (D2's gap is hidden behind D1's numbers). Second log: a **false gap**
  "expected 3, received 50", after which D1's real numbers are ignored.
- **Source:** `src/timeline.js:34` (`direction = [sender, target]`).
- **Impact:** missed and invented gaps wherever one CompID pair carries several sessions. The page offers
  SenderSubID and TargetSubID as filters (AC-050), so such logs are expected.
- **Remediation:** add BeginString, SenderSubID (50), TargetSubID (57), SenderLocationID (142) and
  TargetLocationID (143) to the direction key.
- **Regression test:** S06-15 and S06-16.

## FL-07 (P1) A MsgSeqNum that was already used, without PossDupFlag, is shown as a normal message

- **Kind:** gap in the product's documents. Design section 11: "MsgSeqNum lower than expected: ignored: no
  event, expected number unchanged".
- **Component:** timeline (`src/timeline.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-07-S06-08.log`: numbers 1, 2, 3, then a NewOrderSingle with number **2** and
  no PossDupFlag.
- **Reproduce:** `node reproductions/repro.mjs FL-07`
- **Expected:** the message is pointed out. In FIX this is the one sequence error that ends the session: the
  receiver must log out with "MsgSeqNum too low" and disconnect.
- **Actual:** an ordinary `NewOrder` row; nothing marks it; it counts as a buy order.
- **Source:** `src/timeline.js:50` (`else if (expected === undefined || seq >= expected)`: no branch for the
  lower number).
- **Evidence:** test S06-08; and the four QuickFIX acceptance definitions in which the engine ends the
  session for this reason (`2c_MsgSeqNumTooLow`, `10_MsgSeqNumLess`, FIX 4.2 and 4.4): the tool shows nothing
  in any of them (`reports/partial/external.json`, EX-quickfix-defs-03).
- **Impact:** the usual cause of "the counterparty dropped us at logon" is invisible in the tool whose purpose
  is to explain session behaviour. It also hides FL-05.
- **Remediation:** add a timeline event, for example `SequenceTooLow` with "expected N, received M".
- **Regression test:** S06-08; S06-09 (out of order) with the late message marked.

## FL-08 (P2) A resent or duplicated NewOrderSingle is counted as another order

- **Kind:** gap in the product's documents. AC-040: "buy orders and sell orders count NewOrderSingle messages".
- **Component:** trading summary (`src/summary.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixtures:** `reproductions/FL-08-S06-13-4.4.log`, `-4.2.log` (a NewOrderSingle sent again with
  PossDupFlag=Y and the same number), `FL-08-S11-01.log` (a log merged from both sides of a connection: every
  message twice).
- **Reproduce:** `node reproductions/repro.mjs FL-08`
- **Expected:** Buy orders 1. A retransmission is not a new business event.
- **Actual:** **Buy orders 2.** The strip's "1 order" (from the grouping) and the fills (deduplicated by
  ExecID) are right, so the table contradicts the strip.
- **Source:** `src/summary.js:101-109`.
- **Impact:** order counts doubled in the logs technicians most often build by hand: both sides merged.
- **Remediation:** count distinct ClOrdIDs per session, or skip a NewOrderSingle whose ClOrdID has been
  counted on that session.
- **Regression test:** S06-13 (both versions), S11-01.

## FL-09 (P2) False sequence gaps after a PossDup message with the expected number, and after a reset to a lower number

- **Kind:** gap in the product's documents. TR-003: "messages with PossDupFlag (43)=Y don't advance or reset
  the expected number" and "a SequenceReset sets the expected next number to NewSeqNo".
- **Component:** timeline (`src/timeline.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixtures:** `reproductions/FL-09-S06-17.log` (1, 2, then number 3 with PossDupFlag=Y, then 4) and
  `FL-09-S06-18.log` (1, 2, a SequenceReset with NewSeqNo 1, then 4).
- **Reproduce:** `node reproductions/repro.mjs FL-09`
- **Expected:** no gap in either. A PossDup message whose number has not been received is processed normally
  and takes its number; a SequenceReset may only move the expected number forward.
- **Actual:** "expected 3, received 4" in the first; "expected 1, received 4" in the second.
- **Source:** `src/timeline.js:37` (PossDup skips all tracking) and `:49`.
- **Evidence:** tests S06-17 and S06-18. Found through the QuickFIX acceptance definitions
  `2e_PossDupNotReceived` and `11c_NewSeqNoLess`, where the engine asks for no resend and the tool reports a
  gap (EX-quickfix-defs-02).
- **Impact:** an invented gap sends the technician looking for lost messages that were delivered.
- **Remediation:** let a PossDup message advance the expected number when its number equals it; ignore a
  NewSeqNo that is not higher than the expected number, and say so in the event.
- **Regression test:** S06-17, S06-18; keep S06-03 and S06-04.

## FL-10 (P2) Values that are not FIX numbers are counted as quantities and prices

- **Kind:** gap in the product's documents. Design section 13 asks for "a finite number above zero" without
  saying what a number is; the code uses JavaScript's `Number()`.
- **Component:** trading summary (`src/summary.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixtures:** `reproductions/FL-10-S10-15-01.log` (`32=0x10`), `-02` (`32=1e3`), `-03` (`32= 100 `),
  `-12` (`31=0x10`). Also `0b11` and `+100` (tests S10-15-04, -05).
- **Reproduce:** `node reproductions/repro.mjs FL-10`
- **Expected:** not counted. A FIX Qty or Price is digits with an optional decimal point and an optional
  leading minus; the brief asks that the tool "does not mistake invalid data for valid business activity".
- **Actual:** `0x10` is bought **16**; `1e3` is **1000**; `0b11` is **3**; a price `0x10` gives average **16**.
  Text, an empty value, a negative quantity, `NaN`, `Infinity` and `1,000` are correctly left out (tests
  S10-15-06 to -11 pass).
- **Source:** `src/summary.js:7-11`.
- **Impact:** a corrupt or hostile value becomes a traded quantity without any mark. Needs a counterparty that
  sends an invalid value, so it is rare.
- **Remediation:** accept only `/^-?\d+(\.\d*)?$/` (and `.5` if wanted) before converting; show a note for
  fills left out for this reason.
- **Regression test:** S10-15-01 to S10-15-12.

## FL-11 (P2) The order banner takes the latest state from a resent older report

- **Kind:** gap in the product's documents. AC-036: "its latest state, from its last ExecutionReport".
- **Component:** order story (`src/render.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-11-S07-12.log`: a fill of 40 (CumQty 40), a fill of 60 (CumQty 100, Filled),
  then the first report again with PossDupFlag=Y.
- **Reproduce:** `node reproductions/repro.mjs FL-11`
- **Expected:** `Filled · 100 filled @ 10`.
- **Actual:** `PartiallyFilled · 40 filled @ 10`, while the trading summary on the same screen correctly says
  bought 100.
- **Source:** `src/render.js:114` (`messages.findLast(...)` with no regard to PossDupFlag or ExecID).
- **Impact:** a filled order is presented as partly filled after any resend. Late and reordered reports give
  the same effect.
- **Remediation:** skip reports with PossDupFlag=Y whose ExecID was already seen; say "as of message N".
- **Regression test:** S07-12.

## FL-12 (P2) A message without BeginString disappears without an error

- **Kind:** gap in the product's documents; TR-002 contradicts itself ("a message is malformed if its first
  three fields are not 8, 9 and 35" and "a message starts at `8=FIX`").
- **Component:** framing (`src/framing.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-12-S10-03.log`: a Logon, a NewOrderSingle whose `8=FIX.4.4` field is missing,
  a Heartbeat.
- **Reproduce:** `node reproductions/repro.mjs FL-12`
- **Expected:** 3 messages, 1 malformed, with an error card for the second.
- **Actual:** "2 messages, 2 valid, 0 malformed". The line is treated as non-FIX text. The same happens when
  one character of `8=FIX` is damaged.
- **Source:** `src/framing.js:12-18` (`findMessageStart` is the only way a candidate begins).
- **Impact:** the order in that line is missing from every view and the page reports zero malformed messages.
  The only trace is a sequence gap on the next message of that direction.
- **Remediation:** report a line that is skipped although it contains `35=` and ends in a `10=nnn` field, as a
  malformed candidate ("no BeginString"); or at least show a count of skipped lines that look like FIX.
- **Regression test:** S10-03.

## FL-13 (P2) A wire-valid message with ISO-8859-1 text is reported as malformed

- **Kind:** gap in the product's documents. Design section 3.7 counts "the UTF-8 bytes of its text in the
  paste".
- **Component:** framing (`src/framing.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-13-S10-24.log`: a Heartbeat with `58=Société Générale order`, whose BodyLength
  and CheckSum are right for one byte per character, as the message was on the wire.
- **Reproduce:** `node reproductions/repro.mjs FL-13`
- **Expected:** valid. BodyLength and CheckSum count bytes on the wire; once pasted, the text is characters,
  and many FIX links carry accented names in single-byte encodings.
- **Actual:** "Message 1: BodyLength (9) says 71, actual 75 at position 11": a protocol error is reported where there is none. If the
  message is a fill, it also drops out of the trading summary.
- **Source:** `src/framing.js:134` (`encoder.encode(field)`).
- **Impact:** limited compatibility with European and Latin American counterparties; a false diagnosis.
- **Remediation:** when the UTF-8 count fails, try again counting every character up to U+00FF as one byte;
  accept the message if that matches and show a note about the encoding.
- **Regression test:** S10-24; the UTF-8 property PB-01 must keep passing.

## FL-14 (P3) A valid multiple-value field is labelled "unknown value"

- **Kind:** gap in the product's documents. AC-004 and design section 5 look the whole value up in the code
  set.
- **Component:** decode (`src/decode.js`, `src/dictionary.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-14-S04-05-4.4.log`, `-4.2.log`: a NewOrderSingle with `18=1 6` (ExecInst: not
  held, participate don't initiate).
- **Expected:** the two meanings, or at least no "unknown value". ExecInst is a MultipleValueString; other
  such fields are 277, 276, 291, 292.
- **Actual:** `ExecInst | 1 6 | unknown value`.
- **Source:** `src/decode.js:13`.
- **Impact:** a correct message looks as if the counterparty had sent a bad enumeration.
- **Remediation:** for fields whose Orchestra datatype is MultipleValueString or MultipleCharValue, split on
  spaces and look each value up.
- **Regression test:** S04-05 (both versions).

## FL-15 (P3) An average price that ends exactly on a half is rounded down

- **Kind:** product defect against AC-045 and design section 13 ("`n` rounded to 4 decimal places").
- **Component:** rendering of figures (`src/render.js`).
- **FIX version:** 4.2 and 4.4.
- **Fixture:** `reproductions/FL-15-S07-16.log`: fills of 1 at 1.005 and 1 at 1.0001. The average is exactly
  1.00255.
- **Reproduce:** `node reproductions/repro.mjs FL-15`
- **Expected:** `1.0026` (half-up and half-even agree).
- **Actual:** `1.0025`. The randomised lifecycle test found the same in ordinary data: seed 9014, sold 11 for
  34.17865, exact average 3.10715, shown `3.1071` (PB-06). 3,000 random fill sets without exact ties were all
  right (PB-07).
- **Source:** `src/render.js:27-29` (`Number(value.toFixed(4))` on a binary floating-point quotient).
- **Impact:** one unit in the fourth decimal place, on exact ties only.
- **Remediation:** do the sums in integers (scale quantities and prices by a power of ten, or use BigInt) and
  round in decimal; or correct before `toFixed` with a relative epsilon.
- **Regression test:** S07-16 and seed 9014 of PB-06.

## FL-16 (P3) Figures finer than 4 decimal places or larger than 2^53 are shown as other values

- **Kind:** gap in the product's documents. Design section 13 rounds every figure, quantities included, to 4
  places, and the sums are binary floating point.
- **Component:** trading summary and its rendering (`src/summary.js`, `src/render.js`).
- **Fixtures:** `reproductions/FL-16-S10-17.log` (two fills of 0.00004: bought is shown as `0.0001`, the truth
  is 0.00008; an average price of 1.08345 is shown as `1.0835`) and `FL-16-S10-16.log`
  (9007199254740993 + 2 is shown as `…994`, the truth ends in `…995`). In probes, a single fill of 0.00004 is
  shown as bought `0` beside an average of `64000`, and a quantity of 5000000000000000000000 as `5e+21`.
- **Impact:** small. Five-decimal FX prices and eight-decimal crypto quantities are the realistic cases; a
  small fill can be shown as bought `0`.
- **Remediation:** show quantities exactly as summed in decimal; say in the note that averages are rounded to
  4 places.
- **Regression test:** S10-16, S10-17.

---

## Suspected defects (not confirmed; not counted above)

| Id | Severity if confirmed | What is suspected | Why it is not confirmed |
|---|---|---|---|
| SD-1 | P1 | FIX 4.4 counterparties that still send ExecType `1` or `2` for fills get no fill counted, and the report shows "unknown value" | The tool follows TR-003 and both dictionaries (neither lists 1 or 2 for FIX 4.4; test S04-04 passes). Whether real FIX 4.4 logs of the owner's counterparties contain such reports can only be seen in real logs, which were not available. |
| SD-2 | P3 | A sequence gap is reported right after a malformed message whose own MsgSeqNum fills that gap | Follows from AC-013 (a malformed message adds nothing). An engine does the same for a garbled message, but not for one it rejects at session level (QuickFIX definition `14a_BadField`). Seen in exploratory runs only; whether technicians read it as misleading is a judgement for the owner. |
| SD-3 | P3 | Messages with a missing, empty or wrong TargetCompID fall into a direction of their own and cause a gap on the next normal message | Seen with QuickFIX definitions `14b`, `14d`, `2k`. Invalid traffic; the design says a missing 49 or 56 is an empty string in the key. |
| SD-4 | P3 | Two messages on one line where the first has lost its last delimiter (`…10=123` directly followed by `8=FIX…`) are read as one malformed message | Follows from design section 3.2. Seen once in a probe with two valid pipe-form heartbeats ("0 valid, 1 malformed: BodyLength (9) says 45, actual 111"); not made a test case, because a message without its final delimiter is itself malformed. |

## Architectural risks

1. **One row per Symbol (55).** Futures and options that share a symbol and differ by maturity, strike or
   exchange (tags 200, 202, 201, 207, 48) are netted in one row. AC-039 says so explicitly; for a derivatives
   desk the net figure is then not meaningful. Not tested (the PRD is explicit).
2. **The first message of a direction never makes a gap.** A log that starts with a Logon whose number is too
   high (QuickFIX definition `1a_ValidLogonMsgSeqNumTooHigh`) shows no gap. Inherent to reading a log without
   the engine's stored state; worth a line in the user guidance.
3. **The message limit counts candidates,** so any `8=FIX` in ordinary log text counts towards the 1,000.
4. **Drawing, not analysis, is the cost.** At 1,000 messages the analysis takes about 50 ms and the page
   about 1.5 s to paint 129,000 elements. See `final-assessment.md` for 10,000 messages.
5. **The text is scanned three times** (`checkLimits`, `splitMessages` again in `analyse`, and `checkMessage`
   re-scans every candidate). It costs about 20 ms at 1,000 messages; not a problem at today's limits.
6. **The product's own tests follow the PRD closely** and so share its blind spots: none covers two sessions
   with colliding identifiers, a restart without 141=Y, a reordered log or a decimal tie.
